import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_audit_event(
    path: str | Path,
    event: dict[str, Any],
) -> None:
    """
    Write privacy-minimized operational telemetry.

    Intentionally excluded:
    - full query text
    - generated answer text
    - document contents
    - embeddings
    - credentials / tokens
    """

    audit_path = Path(path)

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_event = {
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "user_id": event.get("user_id"),
        "role": event.get("role"),
        "programs": event.get(
            "programs",
            [],
        ),

        "repository_id": event.get(
            "repository_id"
        ),

        "query_length": event.get(
            "query_length"
        ),

        "authorized_document_count": (
            event.get(
                "authorized_document_count"
            )
        ),

        "retrieved_document_ids": event.get(
            "retrieved_document_ids",
            [],
        ),

        "answer_status": event.get(
            "answer_status"
        ),

        "gate_reason": event.get(
            "gate_reason"
        ),

        "model": event.get("model"),

        "retrieval_latency_ms": event.get(
            "retrieval_latency_ms"
        ),

        "generation_latency_ms": event.get(
            "generation_latency_ms"
        ),

        "latency_ms": event.get(
            "latency_ms"
        ),
    }

    with audit_path.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                safe_event,
                ensure_ascii=False,
            )
            + "\n"
        )
