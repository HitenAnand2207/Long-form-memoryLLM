"""Benchmark-style regression test for token normalization relevance."""

from __future__ import annotations

import os
import sys
from statistics import mean

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from memory_retrieval import MemoryRetriever


OLD_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "is",
    "are",
}


def _old_similarity(memory_content: str, query: str) -> float:
    """Replicates the previous split-based semantic similarity behavior."""
    memory_words = set(memory_content.lower().split()) - OLD_STOPWORDS
    query_words = set(query.lower().split()) - OLD_STOPWORDS

    if not memory_words or not query_words:
        return 0.0

    intersection = len(memory_words & query_words)
    union = len(memory_words | query_words)
    return intersection / union if union > 0 else 0.0


def test_token_normalization_relevance_benchmark() -> None:
    """Compare relevance quality before vs after token normalization."""
    retriever = MemoryRetriever(storage=object())

    cases = [
        ("preferred language is Kannada", "What language?", True),
        ("call after 11 AM", "Can you call me?", True),
        ("office location is Bengaluru", "Where is your office?", True),
        ("favorite cuisine is South Indian", "favorite cuisine", False),
        ("meeting is on friday", "meeting friday", False),
        ("email me at noon", "email at noon", False),
        ("project code is ALPHA", "project code?", True),
        ("timezone is UTC+5:30", "timezone UTC+5:30?", True),
        ("always respond formally", "always respond formally", False),
        ("call before 9 PM", "call before 9 PM!", True),
    ]

    before_scores = [_old_similarity(memory, query) for memory, query, _ in cases]
    after_scores = [
        retriever._calculate_semantic_similarity(memory, query)
        for memory, query, _ in cases
    ]

    punctuation_indexes = [idx for idx, (_, _, has_punct) in enumerate(cases) if has_punct]
    before_punct_mean = mean(before_scores[idx] for idx in punctuation_indexes)
    after_punct_mean = mean(after_scores[idx] for idx in punctuation_indexes)

    overall_before_mean = mean(before_scores)
    overall_after_mean = mean(after_scores)

    # Primary benchmark claim: normalization improves punctuation-heavy retrieval relevance.
    assert after_punct_mean > before_punct_mean

    # Guardrail: overall relevance should not regress.
    assert overall_after_mean >= overall_before_mean
