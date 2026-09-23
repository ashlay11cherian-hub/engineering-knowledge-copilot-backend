import json
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

from backend.src.document_loader import (
    load_documents,
)
from backend.src.vector_index import (
    load_index,
)


BACKEND_DIR = Path(__file__).resolve().parents[1]

LOCAL_DATA_DIR = (
    BACKEND_DIR / "data"
)

LOCAL_INDEX_FILE = (
    BACKEND_DIR / "embedding_index.json"
)

PUBLIC_INDEX_FILE = (
    BACKEND_DIR
    / "public_demo_assets"
    / "local_embedding_index.json"
)

DRIVE_DOCUMENT_FILE = (
    BACKEND_DIR
    / "runtime"
    / "google_drive_documents.json"
)

DRIVE_INDEX_FILE = (
    BACKEND_DIR
    / "runtime"
    / "google_drive_embedding_index.json"
)


LOCAL_REPOSITORY_ID = (
    "demo-engineering-repository"
)

GOOGLE_DRIVE_REPOSITORY_ID = (
    "google-drive-engineering-repository"
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


@dataclass
class RepositoryContext:
    repository_id: str
    provider: str
    documents: list[dict[str, Any]]
    index_entries: list[dict[str, Any]]


def _load_google_drive_documents() -> list[dict[str, Any]]:

    if not DRIVE_DOCUMENT_FILE.exists():
        raise RuntimeError(
            "Google Drive document manifest is missing. "
            "Run python -m backend.build_google_drive_index."
        )

    return json.loads(
        DRIVE_DOCUMENT_FILE.read_text()
    )


def load_repository_context(
    repository_id: str,
) -> RepositoryContext:

    if repository_id == LOCAL_REPOSITORY_ID:

        documents = load_documents(
            LOCAL_DATA_DIR
        )

        index_file = (
            PUBLIC_INDEX_FILE
            if _public_demo_mode()
            else LOCAL_INDEX_FILE
        )

        index_entries = load_index(
            index_file
        )

        return RepositoryContext(
            repository_id=repository_id,
            provider="local_demo",
            documents=documents,
            index_entries=index_entries,
        )

    if repository_id == GOOGLE_DRIVE_REPOSITORY_ID:

        if _public_demo_mode():
            raise ValueError(
                "Google Drive repository is not "
                "available in public demo mode."
            )

        documents = (
            _load_google_drive_documents()
        )

        index_entries = load_index(
            DRIVE_INDEX_FILE
        )

        if not index_entries:
            raise RuntimeError(
                "Google Drive semantic index is missing."
            )

        return RepositoryContext(
            repository_id=repository_id,
            provider="google_drive",
            documents=documents,
            index_entries=index_entries,
        )

    raise ValueError(
        f"Unknown repository: {repository_id}"
    )
