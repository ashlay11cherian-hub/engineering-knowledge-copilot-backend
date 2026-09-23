from backend.main import app

from backend.models.api_models import (
    Citation,
    QueryDiagnostics,
    QueryRequest,
    QueryResponse,
    RepositorySummary,
    UserSummary,
)


def fields(model):
    return set(
        model.model_json_schema()
        .get("properties", {})
        .keys()
    )


def test_stage5_frontend_contract():

    assert {
        "user_id",
        "repository_id",
        "query",
    } <= fields(QueryRequest)

    assert {
        "status",
        "answer",
        "confidence",
        "citations",
        "repository_id",
        "user_id",
        "retrieved_chunk_count",
        "diagnostics",
    } <= fields(QueryResponse)

    assert {
        "document_id",
        "title",
        "source_url",
        "supported_claim",
    } <= fields(Citation)

    assert {
        "candidate_count",
        "accepted_evidence_count",
        "generation_called",
        "gate_reason",
        "top_semantic_score",
        "query_coverage",
        "retrieval_latency_ms",
        "generation_latency_ms",
        "total_latency_ms",
    } <= fields(QueryDiagnostics)

    assert {
        "user_id",
        "name",
        "role",
        "assigned_programs",
        "clearance",
    } <= fields(UserSummary)

    assert {
        "repository_id",
        "name",
        "provider",
        "status",
        "document_count",
        "last_sync",
    } <= fields(RepositorySummary)

    paths = app.openapi()["paths"]

    assert "/api/users" in paths
    assert "/api/repositories" in paths
    assert "/api/query" in paths

    assert "get" in paths["/api/users"]
    assert "get" in paths["/api/repositories"]
    assert "post" in paths["/api/query"]

    status_schema = (
        QueryResponse
        .model_json_schema()
        ["properties"]
        ["status"]
    )

    assert set(status_schema["enum"]) == {
        "answered",
        "insufficient_evidence",
        "conflicting_evidence",
        "error",
    }
