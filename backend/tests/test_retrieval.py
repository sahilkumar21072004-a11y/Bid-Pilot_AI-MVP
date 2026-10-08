from app.retrieval import LocalKeywordRetriever


def test_retriever_ranks_matching_knowledge_first() -> None:
    retriever = LocalKeywordRetriever()
    entries = [
        {"id": 1, "title": "Security certifications", "content": "ISO 27001 certified security program", "category": "Security", "tags": "iso"},
        {"id": 2, "title": "Office location", "content": "Our team is based in Delhi", "category": "Company", "tags": "location"},
    ]
    results = retriever.retrieve("vendor security ISO certification", entries)
    assert results[0]["id"] == 1
    assert results[0]["relevance_score"] > 0


def test_retriever_returns_no_unrelated_evidence() -> None:
    retriever = LocalKeywordRetriever()
    entries = [{"id": 1, "title": "Office", "content": "Delhi office location", "category": "General", "tags": ""}]
    assert retriever.retrieve("cloud encryption", entries) == []
