import json
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BACKEND_DIR / "data"

PUBLIC_INDEX_FILE = (
    BACKEND_DIR
    / "public_demo_assets"
    / "local_embedding_index.json"
)


def test_public_demo_index_covers_entire_corpus():
    source_document_ids = {
        json.loads(
            path.read_text(encoding="utf-8")
        )["document_id"]
        for path in DATA_DIR.glob("*.json")
    }

    public_index = json.loads(
        PUBLIC_INDEX_FILE.read_text(
            encoding="utf-8"
        )
    )

    indexed_document_ids = {
        entry["document_id"]
        for entry in public_index
    }

    assert indexed_document_ids == source_document_ids, (
        "Public demo embedding index is stale. "
        f"Missing: "
        f"{sorted(source_document_ids - indexed_document_ids)}; "
        f"Unexpected: "
        f"{sorted(indexed_document_ids - source_document_ids)}"
    )
