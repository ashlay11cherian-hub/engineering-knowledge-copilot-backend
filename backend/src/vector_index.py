import json
from pathlib import Path
from typing import Any

from google import genai

from backend.src.embedding_service import cosine_similarity, embed_query


def save_index(
    index_entries: list[dict[str, Any]],
    path: str | Path,
) -> None:
    Path(path).write_text(
        json.dumps(index_entries, indent=2),
        encoding="utf-8",
    )


def load_index(path: str | Path) -> list[dict[str, Any]]:
    index_path = Path(path)
    if not index_path.exists():
        return []

    return json.loads(index_path.read_text(encoding="utf-8"))


def semantic_search(
    query: str,
    index_entries: list[dict[str, Any]],
    authorized_document_ids: set[str],
    client: genai.Client,
    top_k: int = 5,
    minimum_score: float = 0.40,
) -> list[dict[str, Any]]:
    """Authorize first, then rank only permitted chunks."""
    candidates = [
        entry
        for entry in index_entries
        if entry["document_id"] in authorized_document_ids
    ]

    if not candidates:
        return []

    query_embedding = embed_query(query, client)
    scored_results: list[dict[str, Any]] = []

    for entry in candidates:
        score = cosine_similarity(
            query_embedding,
            entry["embedding"],
        )

        if score >= minimum_score:
            result = entry.copy()
            result["semantic_score"] = round(score, 4)
            scored_results.append(result)

    # Second-stage reranking.
    #
    # Semantic relevance remains the dominant signal,
    # while current/high-authority records receive a
    # bounded adjustment. Superseded records are
    # deliberately demoted for current-state questions.
    for result in scored_results:
        authority_rank = int(
            result.get("authority_rank", 0)
            or 0
        )

        authority_rank = max(
            0,
            min(
                100,
                authority_rank,
            ),
        )

        authority_bonus = (
            0.02
            * (
                authority_rank
                / 100.0
            )
        )

        status_adjustment = (
            0.02
            if result.get(
                "document_status"
            ) == "current"
            else -0.06
        )

        result["ranking_score"] = round(
            result["semantic_score"]
            + authority_bonus
            + status_adjustment,
            4,
        )

    scored_results.sort(
        key=lambda result: (
            result["ranking_score"],
            result["semantic_score"],
        ),
        reverse=True,
    )

    return scored_results[:top_k]


def evidence_is_sufficient(
    results: list[dict[str, Any]],
    minimum_score: float,
) -> bool:
    if not results:
        return False

    top_score = float(results[0].get("semantic_score", 0.0))
    return top_score >= minimum_score
