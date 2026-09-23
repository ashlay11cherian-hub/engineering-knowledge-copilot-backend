import json
from pathlib import Path

from backend.models.activity_models import ActivityEvent


BACKEND_DIR = Path(__file__).resolve().parents[1]

AUDIT_LOG_FILE = (
    BACKEND_DIR
    / "runtime"
    / "audit_log.jsonl"
)


def get_activity_events(
    limit: int = 50,
) -> list[ActivityEvent]:

    if not AUDIT_LOG_FILE.exists():
        return []

    events: list[ActivityEvent] = []

    with AUDIT_LOG_FILE.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line in handle:

            line = line.strip()

            if not line:
                continue

            try:
                payload = json.loads(line)

                # Backward compatibility:
                # older audit records stored total request
                # latency under `latency_ms`.
                if (
                    payload.get("total_latency_ms") is None
                    and payload.get("latency_ms") is not None
                ):
                    payload["total_latency_ms"] = (
                        payload["latency_ms"]
                    )

                events.append(
                    ActivityEvent.model_validate(
                        payload
                    )
                )

            except (
                json.JSONDecodeError,
                ValueError,
            ):
                # A damaged historical audit row should
                # not take down the Activity API.
                continue

    # Audit log is append-only, so newest records
    # are at the bottom of the file.
    events.reverse()

    safe_limit = max(
        1,
        min(limit, 200),
    )

    return events[:safe_limit]
