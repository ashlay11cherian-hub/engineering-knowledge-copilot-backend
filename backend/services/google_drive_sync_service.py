import json
from pathlib import Path
from typing import Any

from backend.build_google_drive_index import (
    main as rebuild_google_drive_index,
)
from backend.connectors.google_drive import (
    GoogleDriveConnector,
)


BACKEND_DIR = Path(__file__).resolve().parents[1]

MANIFEST_FILE = (
    BACKEND_DIR
    / "runtime"
    / "google_drive_documents.json"
)

REPOSITORY_TAG = "demo-v1"


def _load_cached_documents() -> list[dict[str, Any]]:

    if not MANIFEST_FILE.exists():
        return []

    return json.loads(
        MANIFEST_FILE.read_text()
    )


def detect_google_drive_changes() -> dict[str, Any]:

    connector = GoogleDriveConnector()

    drive_files = connector.list_repository_files(
        REPOSITORY_TAG
    )

    drive_files = [
        file
        for file in drive_files
        if file.get("mimeType")
        == "application/json"
    ]

    cached_documents = (
        _load_cached_documents()
    )

    current_by_id = {
        file["id"]: file
        for file in drive_files
    }

    cached_by_id = {
        document["source_file_id"]: document
        for document in cached_documents
        if document.get("source_file_id")
    }

    current_ids = set(
        current_by_id
    )

    cached_ids = set(
        cached_by_id
    )

    added_ids = (
        current_ids - cached_ids
    )

    deleted_ids = (
        cached_ids - current_ids
    )

    common_ids = (
        current_ids & cached_ids
    )

    updated_ids = {
        file_id
        for file_id in common_ids
        if (
            current_by_id[file_id].get(
                "modifiedTime"
            )
            !=
            cached_by_id[file_id].get(
                "source_modified_time"
            )
        )
    }

    def current_document_id(
        file_id: str,
    ) -> str:

        file = current_by_id[file_id]

        return (
            file.get(
                "appProperties",
                {},
            ).get(
                "ekc_document_id",
                file.get("name", file_id),
            )
        )

    def cached_document_id(
        file_id: str,
    ) -> str:

        document = cached_by_id[
            file_id
        ]

        return document.get(
            "document_id",
            file_id,
        )

    added = sorted(
        current_document_id(file_id)
        for file_id in added_ids
    )

    updated = sorted(
        current_document_id(file_id)
        for file_id in updated_ids
    )

    deleted = sorted(
        cached_document_id(file_id)
        for file_id in deleted_ids
    )

    changed = bool(
        added
        or updated
        or deleted
    )

    return {
        "changed": changed,
        "drive_document_count": len(
            drive_files
        ),
        "cached_document_count": len(
            cached_documents
        ),
        "added": added,
        "updated": updated,
        "deleted": deleted,
    }


def sync_google_drive_repository(
    force: bool = False,
) -> dict[str, Any]:

    changes = (
        detect_google_drive_changes()
    )

    if (
        not changes["changed"]
        and not force
    ):
        return {
            "status": "up_to_date",
            "repository": "google_drive",
            **changes,
        }

    rebuild_google_drive_index()

    refreshed_documents = (
        _load_cached_documents()
    )

    return {
        "status": "synced",
        "repository": "google_drive",
        **changes,
        "indexed_document_count": len(
            refreshed_documents
        ),
    }
