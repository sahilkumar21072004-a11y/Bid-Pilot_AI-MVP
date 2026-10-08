"""Replaceable local retrieval adapter for the MVP knowledge base."""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Protocol


class KnowledgeRetriever(Protocol):
    def retrieve(self, query: str, entries: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]: ...


class LocalKeywordRetriever:
    """Small TF-IDF/cosine retriever; no external embedding service required."""

    @staticmethod
    def _tokens(text: str) -> list[str]:
        words = re.findall(r"[a-z0-9]{2,}", text.lower())
        stop = {"the", "and", "for", "with", "from", "that", "this", "will", "shall", "must", "are", "our", "your", "you", "into", "have", "has", "was", "were", "should", "can", "may", "not", "but", "all", "any", "per", "their", "they"}
        return [word for word in words if word not in stop]

    def retrieve(self, query: str, entries: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
        query_counts = Counter(self._tokens(query))
        if not query_counts or not entries:
            return []
        docs = [Counter(self._tokens(" ".join(str(item.get(key, "")) for key in ("title", "content", "category", "tags")))) for item in entries]
        terms = set(query_counts)
        idf = {term: math.log(1 + (len(docs) + 1) / (1 + sum(term in doc for doc in docs))) for term in terms}
        qnorm = math.sqrt(sum((count * idf[term]) ** 2 for term, count in query_counts.items())) or 1
        scored: list[tuple[float, dict[str, Any]]] = []
        for item, counts in zip(entries, docs):
            dot = sum(query_counts[term] * counts[term] * idf[term] ** 2 for term in terms)
            norm = math.sqrt(sum((count * idf.get(term, 1)) ** 2 for term, count in counts.items())) or 1
            score = dot / (qnorm * norm)
            if score > 0:
                scored.append((score, {**item, "relevance_score": round(score, 4)}))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]


retriever: KnowledgeRetriever = LocalKeywordRetriever()
