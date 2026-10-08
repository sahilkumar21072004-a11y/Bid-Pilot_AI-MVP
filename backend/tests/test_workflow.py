import asyncio

from app.workflow import run_proposal_workflow


def test_workflow_runs_all_six_agents_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr("app.llm_adapter.settings.llm_api_key", "")
    result = asyncio.run(run_proposal_workflow(
        source_text="The vendor must provide 24/7 support. The proposal should include a delivery timeline.",
        title="Support Services RFP",
        company={"name": "Demo Co", "rate_card": ""},
        knowledge=[{"title": "Support", "content": "Our support team provides 24/7 incident response", "category": "Capability", "tags": "support"}],
        template=None,
    ))
    assert [run["agent"] for run in result["agents"]] == ["Extraction Agent", "Analysis Agent", "Drafting Agent", "Cost Estimation Agent", "Compliance Agent", "Optimisation Agent"]
    assert result["llm_mode"] in {"mock", "mock-fallback"}
    assert result["requirements"]
    assert result["cost_estimate"]["planning_hours"] >= 24
