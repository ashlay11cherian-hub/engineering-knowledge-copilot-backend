import json
import shutil
from pathlib import Path

from backend.services.google_drive_repository_service import (
    load_google_drive_documents,
)

from backend.src.chunking import (
    create_document_chunks,
)

from backend.src.document_validation import (
    validate_document_batch,
)

from backend.src.embedding_service import (
    embed_document,
    get_client,
)

from backend.src.vector_index import (
    save_index,
)


BACKEND_DIR = Path(__file__).parent

RUNTIME_DIR = (
    BACKEND_DIR
    / "runtime"
)

INDEX_FILE = (
    RUNTIME_DIR
    / "google_drive_embedding_index.json"
)

MANIFEST_FILE = (
    RUNTIME_DIR
    / "google_drive_documents.json"
)

TEMP_INDEX_FILE = (
    RUNTIME_DIR
    / "google_drive_embedding_index.json.tmp"
)

TEMP_MANIFEST_FILE = (
    RUNTIME_DIR
    / "google_drive_documents.json.tmp"
)

BACKUP_INDEX_FILE = (
    RUNTIME_DIR
    / "google_drive_embedding_index.json.last_good"
)

BACKUP_MANIFEST_FILE = (
    RUNTIME_DIR
    / "google_drive_documents.json.last_good"
)


def _remove_if_exists(
    path: Path,
) -> None:
    if path.exists():
        path.unlink()


def _validate_staged_artifacts(
    *,
    manifest_path: Path,
    index_path: Path,
    expected_document_count: int,
    expected_chunk_count: int,
) -> None:
    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8",
        )
    )

    index_entries = json.loads(
        index_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(manifest, list):
        raise RuntimeError(
            "Staged manifest is not a list."
        )

    if not isinstance(index_entries, list):
        raise RuntimeError(
            "Staged index is not a list."
        )

    if len(manifest) != expected_document_count:
        raise RuntimeError(
            "Staged manifest document count mismatch: "
            f"expected {expected_document_count}, "
            f"found {len(manifest)}."
        )

    if len(index_entries) != expected_chunk_count:
        raise RuntimeError(
            "Staged index chunk count mismatch: "
            f"expected {expected_chunk_count}, "
            f"found {len(index_entries)}."
        )

    document_ids = [
        document.get("document_id")
        for document in manifest
    ]

    if len(document_ids) != len(set(document_ids)):
        raise RuntimeError(
            "Staged manifest contains duplicate document IDs."
        )

    chunk_ids = [
        entry.get("chunk_id")
        for entry in index_entries
    ]

    if (
        not all(chunk_ids)
        or len(chunk_ids) != len(set(chunk_ids))
    ):
        raise RuntimeError(
            "Staged index contains missing or "
            "duplicate chunk IDs."
        )

    # Cross-artifact referential integrity.
    # Every indexed chunk must belong to a document
    # that exists in the current staged manifest.
    index_document_ids = [
        entry.get("document_id")
        for entry in index_entries
    ]

    if any(
        not isinstance(document_id, str)
        or not document_id.strip()
        for document_id in index_document_ids
    ):
        raise RuntimeError(
            "Staged index contains a missing or "
            "invalid document_id."
        )

    manifest_document_ids = set(
        document_ids
    )

    stale_document_ids = sorted(
        set(index_document_ids)
        - manifest_document_ids
    )

    if stale_document_ids:
        raise RuntimeError(
            "Staged index contains documents that "
            "are absent from the current manifest: "
            f"{stale_document_ids}"
        )

    # Every validated manifest document should also
    # be represented by at least one indexed chunk.
    missing_index_documents = sorted(
        manifest_document_ids
        - set(index_document_ids)
    )

    if missing_index_documents:
        raise RuntimeError(
            "Staged manifest contains documents "
            "missing from the vector index: "
            f"{missing_index_documents}"
        )

    for entry in index_entries:
        embedding = entry.get("embedding")

        if (
            not isinstance(embedding, list)
            or not embedding
        ):
            raise RuntimeError(
                "Staged index contains a missing "
                "or invalid embedding."
            )


def _publish_staged_artifacts() -> None:
    manifest_existed = (
        MANIFEST_FILE.exists()
    )

    index_existed = (
        INDEX_FILE.exists()
    )

    if manifest_existed:
        shutil.copy2(
            MANIFEST_FILE,
            BACKUP_MANIFEST_FILE,
        )

    if index_existed:
        shutil.copy2(
            INDEX_FILE,
            BACKUP_INDEX_FILE,
        )

    try:
        # Publish only after BOTH staged artifacts
        # have been completely generated and validated.
        TEMP_INDEX_FILE.replace(
            INDEX_FILE
        )

        TEMP_MANIFEST_FILE.replace(
            MANIFEST_FILE
        )

    except Exception:
        # Roll back to the last known-good pair.
        if index_existed:
            shutil.copy2(
                BACKUP_INDEX_FILE,
                INDEX_FILE,
            )
        elif INDEX_FILE.exists():
            INDEX_FILE.unlink()

        if manifest_existed:
            shutil.copy2(
                BACKUP_MANIFEST_FILE,
                MANIFEST_FILE,
            )
        elif MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()

        raise


def main() -> None:
    RUNTIME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    _remove_if_exists(
        TEMP_INDEX_FILE
    )

    _remove_if_exists(
        TEMP_MANIFEST_FILE
    )

    print(
        "Loading Google Drive documents..."
    )

    documents = (
        load_google_drive_documents()
    )

    if not documents:
        raise RuntimeError(
            "No valid Google Drive documents were loaded. "
            "Existing runtime artifacts were not changed."
        )

    # Defense-in-depth validation immediately
    # before indexing.
    validate_document_batch(
        documents
    )

    print(
        "Drive documents loaded:",
        len(documents),
    )

    chunks = create_document_chunks(
        documents,
        chunk_size_words=120,
        overlap_words=25,
    )

    if not chunks:
        raise RuntimeError(
            "No chunks were generated. "
            "Existing runtime artifacts were not changed."
        )

    source_metadata = {
        document["document_id"]: {
            "source_provider": (
                document.get(
                    "source_provider"
                )
            ),
            "source_file_id": (
                document.get(
                    "source_file_id"
                )
            ),
            "source_url": (
                document.get(
                    "source_url"
                )
            ),
            "source_modified_time": (
                document.get(
                    "source_modified_time"
                )
            ),
        }
        for document in documents
    }

    client = get_client()

    index_entries = []

    print(
        "Creating Drive embeddings for",
        len(chunks),
        "chunks...",
    )

    # IMPORTANT:
    # Nothing in the active runtime is written
    # while embeddings are being generated.
    for position, chunk in enumerate(
        chunks,
        start=1,
    ):
        print(
            f"[{position}/{len(chunks)}] "
            f"{chunk['chunk_id']} — "
            f"{chunk['title']}"
        )

        embedding_text = (
            f"Title: {chunk['title']}\n"
            f"Source type: "
            f"{chunk['source_type']}\n"
            f"Program: "
            f"{chunk['program_id']}\n"
            f"Revision: "
            f"{chunk['revision']}\n"
            f"Status: "
            f"{chunk.get('document_status', 'current')}\n"
            f"Content: {chunk['text']}"
        )

        entry = chunk.copy()

        entry["embedding"] = (
            embed_document(
                embedding_text,
                client,
            )
        )

        metadata = source_metadata.get(
            chunk["document_id"],
            {},
        )

        entry.update(
            metadata
        )

        index_entries.append(
            entry
        )

    # -----------------------------------------
    # Stage new artifacts
    # -----------------------------------------

    TEMP_MANIFEST_FILE.write_text(
        json.dumps(
            documents,
            indent=2,
        ),
        encoding="utf-8",
    )

    save_index(
        index_entries,
        TEMP_INDEX_FILE,
    )

    # -----------------------------------------
    # Validate staged artifacts
    # -----------------------------------------

    _validate_staged_artifacts(
        manifest_path=TEMP_MANIFEST_FILE,
        index_path=TEMP_INDEX_FILE,
        expected_document_count=len(
            documents
        ),
        expected_chunk_count=len(
            index_entries
        ),
    )

    print(
        "PASS: staged runtime artifacts validated."
    )

    # -----------------------------------------
    # Publish
    # -----------------------------------------

    _publish_staged_artifacts()

    print()
    print(
        "SUCCESS: Google Drive index built "
        "and published."
    )

    print(
        "Documents:",
        len(documents),
    )

    print(
        "Indexed chunks:",
        len(index_entries),
    )

    print(
        "Manifest:",
        MANIFEST_FILE,
    )

    print(
        "Index:",
        INDEX_FILE,
    )

    print(
        "Last-known-good backups:",
        BACKUP_MANIFEST_FILE,
        "and",
        BACKUP_INDEX_FILE,
    )


if __name__ == "__main__":
    try:
        main()

    finally:
        # Temporary build artifacts should never
        # remain authoritative.
        _remove_if_exists(
            TEMP_MANIFEST_FILE
        )

        _remove_if_exists(
            TEMP_INDEX_FILE
        )
