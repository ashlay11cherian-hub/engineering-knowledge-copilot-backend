from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserSummary(BaseModel):
    user_id: str
    name: str
    role: str
    assigned_programs: list[str]
    clearance: str


class RepositorySummary(BaseModel):
    repository_id: str
    name: str
    provider: Literal[
        "local_demo",
        "google_drive",
        "sharepoint",
    ]
    status: Literal[
        "connected",
        "disconnected",
        "syncing",
        "error",
    ]
    document_count: int
    last_sync: str | None = None


class QueryRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    repository_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9_-]+$",
    )

    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
    )



class Citation(BaseModel):
    document_id: str
    title: str
    source_url: str | None = None
    supported_claim: str | None = None


class QueryDiagnostics(BaseModel):
    candidate_count: int
    accepted_evidence_count: int

    generation_called: bool

    gate_reason: str

    top_semantic_score: float
    query_coverage: float

    retrieval_latency_ms: int
    generation_latency_ms: int
    total_latency_ms: int


class QueryResponse(BaseModel):
    status: Literal[
        "answered",
        "insufficient_evidence",
        "conflicting_evidence",
        "error",
    ]

    answer: str

    confidence: Literal[
        "high",
        "medium",
        "low",
    ] | None = None

    citations: list[Citation] = Field(
        default_factory=list
    )

    repository_id: str
    user_id: str

    retrieved_chunk_count: int = 0

    diagnostics: QueryDiagnostics | None = None
