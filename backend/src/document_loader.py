import json
from pathlib import Path
from typing import Any


def load_documents(data_directory: str | Path) -> list[dict[str, Any]]:
    directory = Path(data_directory)
    documents: list[dict[str, Any]] = []

    for path in sorted(directory.glob("*.json")):
        try:
            documents.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not load {path.name}: {exc}") from exc

    return documents
