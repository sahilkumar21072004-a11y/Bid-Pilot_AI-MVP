import re
import json
from typing import Any


REQUIREMENT_WORDS = re.compile(r"\b(must|shall|required|mandatory|should|may|will)\b", re.I)


def extract_requirements(text: str) -> list[dict[str, Any]]:
    candidates = [re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip() for line in text.splitlines()]
    found = [line for line in candidates if len(line) > 16 and REQUIREMENT_WORDS.search(line)]
    if not found:
        found = [line.strip() for line in re.split(r"(?<=[.!?])\s+", text) if len(line.strip()) > 25][:8]
    return [{"id": index + 1, "text": sentence, "category": "Mandatory" if re.search(r"\b(must|shall|required|mandatory)\b", sentence, re.I) else "Optional", "response": "We will address this requirement through the proposed delivery approach.", "evidence": "RFP source", "owner": "Unassigned", "review_status": "Needs review"} for index, sentence in enumerate(found[:40])]


def draft_proposal(title: str, requirements: list[dict[str, Any]], company: dict[str, Any], knowledge: list[dict[str, Any]], template: dict[str, Any] | None) -> list[dict[str, str]]:
    company_name = company.get("name") or "Your Company"
    context = " ".join(item.get("content", "") for item in knowledge[:4])
    titles = template.get("sections", ["Executive Summary", "Understanding the Requirements", "Delivery Approach", "Project Timeline", "Investment", "Risk and Governance"]) if template else ["Executive Summary", "Understanding the Requirements", "Delivery Approach", "Project Timeline", "Investment", "Risk and Governance"]
    summary = f"{company_name} proposes a measurable, governed delivery approach for {title}. The response maps the RFP requirements to accountable workstreams, milestones, and review evidence."
    if context:
        summary += f" Relevant company knowledge considered: {context[:500]}"
    rate_card = company.get("rate_card") or {}
    if isinstance(rate_card, str):
        try:
            rate_card = json.loads(rate_card)
        except json.JSONDecodeError:
            rate_card = {}
    rate = rate_card.get("blended_hourly_rate", rate_card.get("hourly_rate")) if isinstance(rate_card, dict) else None
    try:
        rate = float(rate) if rate not in (None, "") and float(rate) > 0 else None
    except (TypeError, ValueError):
        rate = None
    estimated_hours = max(24, len(requirements) * 8)
    investment = (f"Planning estimate: {estimated_hours:,} hours × ${rate:,.2f}/hour = ${estimated_hours * rate:,.2f}. "
                  "This is an assumption-based estimate; confirm staffing, duration, expenses, taxes, and rate-card scope before submission.") if rate else (f"Planning effort: {estimated_hours:,} hours based on an assumption of eight hours per extracted requirement (24-hour minimum). "
                  "No price is calculated because the company profile has no numeric hourly_rate or blended_hourly_rate in its rate-card JSON. Confirm estimates before submission.")
    bodies = []
    for index, heading in enumerate(titles):
        lowered = heading.lower()
        if index == 0:
            body = summary
        elif "requirement" in lowered or "compliance" in lowered:
            body = "The team will address the RFP obligations with named ownership, documented evidence, and review checkpoints.\n\n" + "\n".join(f"• {item['text']} — {item.get('response', '')}" for item in requirements[:12])
        elif "investment" in lowered or "cost" in lowered or "price" in lowered:
            body = investment
        else:
            body = "Delivery will proceed through discovery, solution design, implementation, quality assurance, and controlled handover. Dates, staffing, and contractual assumptions should be confirmed by the proposal owner."
        bodies.append({"heading": heading, "body": body})
    return bodies
