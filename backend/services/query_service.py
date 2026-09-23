from time import perf_counter
from pathlib import Path

from google.genai import errors as genai_errors

from backend.models.api_models import (
    Citation as ApiCitation,
    QueryDiagnostics,
    QueryResponse,
)
from backend.services.demo_service import (
    get_demo_users,
)
from backend.services.repository_context_service import (
    load_repository_context,
)

from backend.src.audit import write_audit_event
from backend.src.answer_service import (
    generate_grounded_answer,
    insufficient_evidence_answer,
)
from backend.src.auth import (
    filter_authorized_documents,
)
from backend.src.embedding_service import (
    get_client,
    get_generation_model,
)
from backend.src.relevance_gate import (
    evaluate_evidence,
)
from backend.src.vector_index import (
    semantic_search,
)


AUDIT_LOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "runtime"
    / "audit_log.jsonl"
)


def _write_query_audit(
    *,
    user,
    repository_id: str,
    query: str,
    authorized_documents,
    accepted_results,
    answer_status: str,
    gate_reason: str,
    model: str | None,
    retrieval_latency_ms: int,
    generation_latency_ms: int,
    total_latency_ms: int,
) -> None:
    retrieved_document_ids = sorted(
        {
            result["document_id"]
            for result in accepted_results
            if result.get("document_id")
        }
    )

    write_audit_event(
        AUDIT_LOG_PATH,
        {
            "user_id": user.user_id,
            "role": user.role,
            "programs": user.assigned_programs,
            "repository_id": repository_id,
            "query_length": len(query),
            "authorized_document_count": len(
                authorized_documents
            ),
            "retrieved_document_ids": (
                retrieved_document_ids
            ),
            "answer_status": answer_status,
            "gate_reason": gate_reason,
            "model": model,
            "retrieval_latency_ms": (
                retrieval_latency_ms
            ),
            "generation_latency_ms": (
                generation_latency_ms
            ),
            "latency_ms": total_latency_ms,
        },
    )


def execute_demo_query(
    user_id: str,
    repository_id: str,
    query: str,
) -> QueryResponse:

    total_start = perf_counter()

    users = {
        user.user_id: user
        for user in get_demo_users()
    }

    user = users.get(user_id)

    if user is None:
        raise ValueError(
            "Unknown demo user."
        )

    # ----------------------------------
    # Repository selection
    # ----------------------------------

    repository = load_repository_context(
        repository_id
    )

    documents = repository.documents
    index_entries = repository.index_entries

    # ----------------------------------
    # Authorization
    # ----------------------------------

    authorized_documents = (
        filter_authorized_documents(
            documents,
            user.model_dump(),
        )
    )

    authorized_document_ids = {
        document["document_id"]
        for document in authorized_documents
    }

    client = get_client()

    # ----------------------------------
    # Semantic retrieval
    # ----------------------------------

    retrieval_start = perf_counter()

    candidates = semantic_search(
        query=query,
        index_entries=index_entries,
        authorized_document_ids=(
            authorized_document_ids
        ),
        client=client,
        top_k=5,
        minimum_score=0.0,
    )

    retrieval_latency_ms = int(
        (
            perf_counter()
            - retrieval_start
        )
        * 1000
    )

    # ----------------------------------
    # Hybrid evidence gate
    # ----------------------------------

    gate = evaluate_evidence(
        query=query,
        results=candidates,
    )

    generation_called = False
    generation_latency_ms = 0
    model: str | None = None

    if not gate.accepted:

        grounded_answer = (
            insufficient_evidence_answer(
                (
                    "I could not find sufficiently "
                    "relevant authorized evidence "
                    "to answer this question."
                )
            )
        )

        accepted_results = []

    else:

        accepted_results = [
            result
            for result in candidates
            if float(
                result.get(
                    "semantic_score",
                    0.0,
                )
            )
            >= 0.60
        ][:5]

        model = get_generation_model()

        generation_start = (
            perf_counter()
        )

        try:
            grounded_answer, _metadata = (
                generate_grounded_answer(
                    query=query,
                    results=accepted_results,
                    client=client,
                    model=model,
                )
            )

        except genai_errors.ClientError as exc:
            if exc.code == 429:
                generation_latency_ms = int(
                    (perf_counter() - generation_start) * 1000
                )

                generation_called = True

                total_latency_ms = int(
                    (perf_counter() - total_start) * 1000
                )

                diagnostics = QueryDiagnostics(
                    candidate_count=len(candidates),
                    accepted_evidence_count=len(accepted_results),
                    generation_called=True,
                    gate_reason="generation_rate_limited",
                    top_semantic_score=gate.top_semantic_score,
                    query_coverage=gate.query_coverage,
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=generation_latency_ms,
                    total_latency_ms=total_latency_ms,
                )

                _write_query_audit(
                    user=user,
                    repository_id=repository_id,
                    query=query,
                    authorized_documents=authorized_documents,
                    accepted_results=accepted_results,
                    answer_status="error",
                    gate_reason="generation_rate_limited",
                    model=model,
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=generation_latency_ms,
                    total_latency_ms=total_latency_ms,
                )

                return QueryResponse(
                    status="error",
                    answer=(
                        "AI generation is temporarily rate limited. "
                        "Your authorized evidence was retrieved successfully. "
                        "Please retry later."
                    ),
                    confidence=None,
                    citations=[],
                    repository_id=repository_id,
                    user_id=user_id,
                    retrieved_chunk_count=len(accepted_results),
                    diagnostics=diagnostics,
                )

            raise

        except genai_errors.ServerError as exc:
            if exc.code == 503:
                generation_latency_ms = int(
                    (perf_counter() - generation_start) * 1000
                )

                generation_called = True

                total_latency_ms = int(
                    (perf_counter() - total_start) * 1000
                )

                diagnostics = QueryDiagnostics(
                    candidate_count=len(candidates),
                    accepted_evidence_count=len(accepted_results),
                    generation_called=True,
                    gate_reason="generation_service_unavailable",
                    top_semantic_score=gate.top_semantic_score,
                    query_coverage=gate.query_coverage,
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=generation_latency_ms,
                    total_latency_ms=total_latency_ms,
                )

                _write_query_audit(
                    user=user,
                    repository_id=repository_id,
                    query=query,
                    authorized_documents=authorized_documents,
                    accepted_results=accepted_results,
                    answer_status="error",
                    gate_reason="generation_service_unavailable",
                    model=model,
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=generation_latency_ms,
                    total_latency_ms=total_latency_ms,
                )

                return QueryResponse(
                    status="error",
                    answer=(
                        "AI generation is temporarily unavailable. "
                        "Your authorized evidence was retrieved successfully. "
                        "Please retry shortly."
                    ),
                    confidence=None,
                    citations=[],
                    repository_id=repository_id,
                    user_id=user_id,
                    retrieved_chunk_count=len(accepted_results),
                    diagnostics=diagnostics,
                )

            raise

        generation_latency_ms = int(
            (
                perf_counter()
                - generation_start
            )
            * 1000
        )

        generation_called = bool(
            _metadata.get(
                "generation_called",
                True,
            )
        )

        if not generation_called:
            model = None

    # -------------------------------
    # Citation enrichment
    # ----------------------------------

    documents_by_id = {
        document["document_id"]: document
        for document in documents
    }

    api_citations: list[
        ApiCitation
    ] = []

    for citation in grounded_answer.citations:

        source_id = citation.source_id

        source_document = (
            documents_by_id.get(
                source_id,
                {},
            )
        )

        api_citations.append(
            ApiCitation(
                document_id=source_id,
                title=source_document.get(
                    "title",
                    source_id,
                ),

                # Local repository:
                #     None
                #
                # Google Drive repository:
                #     actual Drive webViewLink
                source_url=(
                    source_document.get(
                        "source_url"
                    )
                ),

                supported_claim=(
                    citation.supported_claim
                ),
            )
        )

    total_latency_ms = int(
        (
            perf_counter()
            - total_start
        )
        * 1000
    )

    diagnostics = QueryDiagnostics(
        candidate_count=len(
            candidates
        ),
        accepted_evidence_count=len(
            accepted_results
        ),
        generation_called=(
            generation_called
        ),
        gate_reason=gate.reason,
        top_semantic_score=(
            gate.top_semantic_score
        ),
        query_coverage=(
            gate.query_coverage
        ),
        retrieval_latency_ms=(
            retrieval_latency_ms
        ),
        generation_latency_ms=(
            generation_latency_ms
        ),
        total_latency_ms=(
            total_latency_ms
        ),
    )

    _write_query_audit(
        user=user,
        repository_id=repository_id,
        query=query,
        authorized_documents=authorized_documents,
        accepted_results=accepted_results,
        answer_status=grounded_answer.status,
        gate_reason=gate.reason,
        model=model,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        total_latency_ms=total_latency_ms,
    )

    return QueryResponse(
        status=grounded_answer.status,
        answer=grounded_answer.answer,
        confidence=(
            grounded_answer.confidence
        ),
        citations=api_citations,
        repository_id=repository_id,
        user_id=user_id,
        retrieved_chunk_count=len(
            accepted_results
        ),
        diagnostics=diagnostics,
    )
