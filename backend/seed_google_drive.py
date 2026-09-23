import json
from pathlib import Path

from backend.connectors.google_drive import (
    GoogleDriveConnector,
)


BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / "data"

FOLDER_NAME = (
    "Engineering Knowledge Copilot Demo"
)


def main():

    connector = GoogleDriveConnector()

    folder = connector.ensure_folder(
        FOLDER_NAME
    )

    print(
        "Repository folder:",
        folder["name"],
    )

    json_files = sorted(
        DATA_DIR.glob("*.json")
    )

    print(
        "Synthetic documents:",
        len(json_files),
    )

    uploaded = []

    for position, path in enumerate(
        json_files,
        start=1,
    ):

        document = json.loads(
            path.read_text()
        )

        document_id = document.get(
            "document_id",
            path.stem,
        )

        result = connector.upload_json_file(
            local_path=path,
            parent_id=folder["id"],
            document_id=document_id,
        )

        uploaded.append(result)

        print(
            f"[{position}/{len(json_files)}] "
            f"{document_id} → {result['name']}"
        )

    print()
    print(
        "SUCCESS: Google Drive repository seeded."
    )
    print(
        "Uploaded documents:",
        len(uploaded),
    )


if __name__ == "__main__":
    main()
