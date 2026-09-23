import os
import json
from pathlib import Path

from backend.models.api_models import RepositorySummary
from backend.services.demo_service import get_demo_repositories


BACKEND_DIR = Path(__file__).resolve().parents[1]

LOCAL_DATA_DIR = (
    BACKEND_DIR
    / "data"
)

DRIVE_MANIFEST = (
    BACKEND_DIR
    / "runtime"
    / "google_drive_documents.json"
)


def _public_demo_mode() -> bool:
    return (
        os.getenv(
            "PUBLIC_DEMO_MODE",
            "false",
        )
        .strip()
        .lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )


def get_repository_catalog() -> list[RepositorySummary]:

    local_document_count = len(
        list(
            LOCAL_DATA_DIR.glob("*.json")
        )
    )

    repositories = [
        repository.model_copy(
            update={
                "document_count": (
                    local_document_count
                )
            }
        )
        if repository.repository_id
        == "demo-engineering-repository"
        else repository
        for repository
        in get_demo_repositories()
    ]

    if _public_demo_mode():
        return repositories

    drive_document_count = 0
    last_sync = None

    if DRIVE_MANIFEST.exists():

        documents = json.loads(
            DRIVE_MANIFEST.read_text()
        )

        drive_document_count = len(
            documents
        )

        modified_times = [
            document.get(
                "source_modified_time"
            )
            for document in documents
            if document.get(
                "source_modified_time"
            )
        ]

        if modified_times:
            last_sync = max(
                modified_times
            )

    repositories.append(
        RepositorySummary(
            repository_id=(
                "google-drive-engineering-repository"
            ),
            name=(
                "Engineering Knowledge Copilot Demo - Google Drive"
            ),
            provider="google_drive",
            status="connected",
            document_count=drive_document_count,
            last_sync=last_sync,
        )
    )

    return repositories
