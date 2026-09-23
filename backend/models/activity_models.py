from pydantic import BaseModel, Field


class ActivityEvent(BaseModel):
    timestamp_utc: str

    user_id: str | None = None
    role: str | None = None

    programs: list[str] = Field(
        default_factory=list
    )

    repository_id: str | None = None

    query_length: int | None = None
    authorized_document_count: int | None = None

    retrieved_document_ids: list[str] = Field(
        default_factory=list
    )

    answer_status: str | None = None
    gate_reason: str | None = None

    model: str | None = None

    retrieval_latency_ms: int | None = None
    generation_latency_ms: int | None = None
    total_latency_ms: int | None = None
