from google.genai import errors as genai_errors

import backend.services.query_service as query_service


class Fake503Error(genai_errors.ServerError):
    """Deterministic stand-in for a Gemini 503 response."""

    def __init__(self):
        Exception.__init__(
            self,
            "503 UNAVAILABLE: simulated provider outage",
        )
        self.code = 503


def test_generation_503_returns_typed_error(monkeypatch):
    def raise_503(*args, **kwargs):
        raise Fake503Error()

    monkeypatch.setattr(
        query_service,
        "generate_grounded_answer",
        raise_503,
    )

    response = query_service.execute_demo_query(
        user_id="sarah",
        repository_id="google-drive-engineering-repository",
        query=(
            "What caused the Gen-3 wireless charger "
            "thermal failure?"
        ),
    )

    assert response.status == "error"
    assert response.confidence is None
    assert response.citations == []

    assert response.user_id == "sarah"
    assert (
        response.repository_id
        == "google-drive-engineering-repository"
    )

    assert response.retrieved_chunk_count > 0

    assert response.diagnostics is not None
    assert response.diagnostics.generation_called is True
    assert (
        response.diagnostics.gate_reason
        == "generation_service_unavailable"
    )
    assert response.diagnostics.accepted_evidence_count > 0

    assert "temporarily unavailable" in response.answer.lower()
