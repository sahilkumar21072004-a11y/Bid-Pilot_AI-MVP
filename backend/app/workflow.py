"""Six-node LangGraph proposal workflow used by the MVP."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .llm_adapter import draft_sections
from .service import draft_proposal, extract_requirements

logger = logging.getLogger("bidpilot.workflow")


class ProposalState(TypedDict, total=False):
    source_text: str
    title: str
    company: dict[str, Any]
    knowledge: list[dict[str, Any]]
    template: dict[str, Any] | None
    requirements: list[dict[str, Any]]
    sections: list[dict[str, str]]
    agents: list[dict[str, str]]
    llm_mode: str
    compliance: dict[str, int]
    cost_estimate: dict[str, Any]


def mark(state: ProposalState, name: str) -> list[dict[str, str]]:
    current = list(state.get("agents", []))
    current.append({"agent": name, "status": "completed"})
    logger.info("Agent completed: %s", name)
    return current


def extraction_agent(state: ProposalState) -> dict[str, Any]:
    requirements = extract_requirements(state.get("source_text", ""))
    return {"requirements": requirements, "agents": mark(state, "Extraction Agent")}


def analysis_agent(state: ProposalState) -> dict[str, Any]:
    updated = []
    for item in state.get("requirements", []):
        text = item["text"]
        mandatory = bool(re.search(r"\b(must|shall|required|mandatory)\b", text, re.I))
        updated.append({**item, "category": "Mandatory" if mandatory else "Optional", "priority": "High" if mandatory else "Normal", "confidence": 0.85 if mandatory else 0.65})
    return {"requirements": updated, "agents": mark(state, "Analysis Agent")}


async def drafting_agent(state: ProposalState) -> dict[str, Any]:
    title = state.get("title", "RFP Response")
    company, knowledge, template = state.get("company", {}), state.get("knowledge", []), state.get("template")
    fallback = draft_proposal(title, state.get("requirements", []), company, knowledge, template)
    headings = [item["heading"] for item in fallback]
    sections, mode = await draft_sections(title, state.get("requirements", []), company, knowledge, headings, fallback)
    return {"sections": sections, "llm_mode": mode, "agents": mark(state, "Drafting Agent")}


def cost_agent(state: ProposalState) -> dict[str, Any]:
    rate_card = state.get("company", {}).get("rate_card", {})
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
    hours = max(24, 8 * len(state.get("requirements", [])))
    estimate = {"planning_hours": hours, "hourly_rate": rate, "total": round(hours * rate, 2) if rate else None, "basis": "8 planning hours per extracted requirement; 24-hour minimum"}
    sections = list(state.get("sections", []))
    for section in sections:
        if any(word in section["heading"].lower() for word in ("investment", "cost", "price")):
            if estimate["total"] is not None:
                section["body"] = f"Planning estimate: {hours:,} hours × ${rate:,.2f}/hour = ${estimate['total']:,.2f}. Confirm roles, schedule, expenses, taxes, and rate-card scope before submission."
    return {"sections": sections, "cost_estimate": estimate, "agents": mark(state, "Cost Estimation Agent")}


def compliance_agent(state: ProposalState) -> dict[str, Any]:
    reqs = [{**item, "review_status": item.get("review_status", "Needs review"), "evidence": item.get("evidence", "RFP source")} for item in state.get("requirements", [])]
    approved = sum(item.get("review_status") == "Approved" for item in reqs)
    readiness = round(100 * approved / len(reqs)) if reqs else 0
    return {"requirements": reqs, "compliance": {"approved": approved, "total": len(reqs), "readiness_percent": readiness}, "agents": mark(state, "Compliance Agent")}


def optimisation_agent(state: ProposalState) -> dict[str, Any]:
    sections = [{"heading": item["heading"].strip(), "body": re.sub(r"\n{3,}", "\n\n", item["body"]).strip()} for item in state.get("sections", [])]
    return {"sections": sections, "agents": mark(state, "Optimisation Agent")}


_graph = StateGraph(ProposalState)
_graph.add_node("extraction", extraction_agent)
_graph.add_node("analysis", analysis_agent)
_graph.add_node("drafting", drafting_agent)
_graph.add_node("cost", cost_agent)
_graph.add_node("compliance", compliance_agent)
_graph.add_node("optimisation", optimisation_agent)
_graph.add_edge(START, "extraction")
_graph.add_edge("extraction", "analysis")
_graph.add_edge("analysis", "drafting")
_graph.add_edge("drafting", "cost")
_graph.add_edge("cost", "compliance")
_graph.add_edge("compliance", "optimisation")
_graph.add_edge("optimisation", END)
proposal_graph = _graph.compile()


async def run_proposal_workflow(source_text: str, title: str, company: dict[str, Any], knowledge: list[dict[str, Any]], template: dict[str, Any] | None) -> ProposalState:
    initial: ProposalState = {"source_text": source_text, "title": title, "company": company, "knowledge": knowledge, "template": template, "agents": []}
    return await proposal_graph.ainvoke(initial)
