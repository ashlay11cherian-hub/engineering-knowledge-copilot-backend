import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.connectors.google_drive import (
    GoogleDriveConnector,
)

from backend.src.document_validation import (
    validate_document,
)


REPOSITORY_TAG = "demo-v1"

BACKEND_DIR = (
    Path(__file__).resolve().parents[1]
)

QUARANTINE_FILE = (
    BACKEND_DIR
    / "runtime"
    / "ingestion_quarantine.jsonl"
)


def _write_quarantine_event(
    *,
    repository_tag: str,
    file_metadata: dict[str, Any],
    reason: str,
) -> None:
    QUARANTINE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    event = {
        "timestamp_utc": (
            datetime.now(timezone.utc)
            .isoformat()
        ),
        "repository_tag": repository_tag,
        "source_provider": "google_drive",
        "source_file_id": (
            file_metadata.get("id")
        ),
        "source_file_name": (
            file_metadata.get("name")
        ),
        "reason": reason,
    }

    with QUARANTINE_FILE.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(event)
            + "\n"
        )


def load_google_drive_documents(
    repository_tag: str = REPOSITORY_TAG,
) -> list[dict[str, Any]]:
    connector = GoogleDriveConnector()

    files = connector.list_repository_files(
        repository_tag
    )

    documents: list[dict[str, Any]] = []

    seen_document_ids: set[str] = set()

    for file in files:
        if (
            file.get("mimeType")
            != "application/json"
        ):
            continue

        try:
            document = (
                connector.download_json_document(
                    file["id"]
                )
            )

            validate_document(document)

            document_id = (
                document["document_id"]
            )

            if document_id in seen_document_ids:
                raise ValueError(
                    "Duplicate document_id: "
                    f"{document_id}"
                )

            seen_document_ids.add(
                document_id
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValueError,
            TypeError,
            KeyError,
        ) as exc:
            _write_quarantine_event(
                repository_tag=repository_tag,
                file_metadata=file,
                reason=(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

            continue

        # Cloud-source metadata is added only
        # after the document has passed validation.
        document["source_provider"] = (
            "google_drive"
        )

        document["source_file_id"] = (
            file["id"]
        )

        document["source_url"] = (
            file.get("webViewLink")
        )

        document[
            "source_modified_time"
        ] = file.get(
            "modifiedTime"
        )

        document["repository_tag"] = (
            repository_tag
        )

        documents.append(document)

    return documents
