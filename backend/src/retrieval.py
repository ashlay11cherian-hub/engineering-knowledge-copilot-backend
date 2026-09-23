import re
from typing import Any

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "did", "do",
    "for", "from", "how", "i", "in", "is", "it", "of", "on", "or",
    "the", "to", "was", "what", "when", "where", "which", "who",
    "why", "with",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9-]+", text.lower())
    return {
        word
        for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def retrieve_documents(
    query: str,
    documents: list[dict[str, Any]],
    top_k: int = 4,
) -> list[dict[str, Any]]:
    """Phase 1 keyword retrieval. Embeddings are added on Day 2."""
    query_tokens = _tokens(query)
    scored: list[tuple[float, dict[str, Any]]] = []

    for document in documents:
        searchable_text = " ".join(
            [
                document.get("title", ""),
                document.get("source_type", ""),
                document.get("content", ""),
            ]
        )
        overlap = query_tokens.intersection(_tokens(searchable_text))

        if overlap:
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append((score, document))

    scored.sort(key=lambda item: item[0], reverse=True)

    results: list[dict[str, Any]] = []
    for score, document in scored[:top_k]:
        result = document.copy()
        result["retrieval_score"] = round(score, 3)
        results.append(result)

    return results
