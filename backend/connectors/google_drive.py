import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from backend.connectors.base import RepositoryConnector


load_dotenv()


DRIVE_FILE_SCOPE = (
    "https://www.googleapis.com/auth/drive.file"
)

FOLDER_MIME_TYPE = (
    "application/vnd.google-apps.folder"
)

BACKEND_DIR = Path(__file__).resolve().parents[1]

TOKEN_FILE = (
    BACKEND_DIR
    / "runtime"
    / "google_token.json"
)


class GoogleDriveConnector(RepositoryConnector):

    def __init__(self):
        self.credentials = self._load_credentials()

        self.service = build(
            "drive",
            "v3",
            credentials=self.credentials,
            cache_discovery=False,
        )

    def _load_credentials(self) -> Credentials:

        if not TOKEN_FILE.exists():
            raise RuntimeError(
                "Google Drive is not connected."
            )

        payload = json.loads(
            TOKEN_FILE.read_text()
        )

        expiry = None

        if payload.get("expiry"):
            expiry = datetime.fromisoformat(
                payload["expiry"]
            )

        credentials = Credentials(
            token=payload.get("token"),
            refresh_token=payload.get(
                "refresh_token"
            ),
            token_uri=payload.get(
                "token_uri",
                "https://oauth2.googleapis.com/token",
            ),
            client_id=os.getenv(
                "GOOGLE_CLIENT_ID"
            ),
            client_secret=os.getenv(
                "GOOGLE_CLIENT_SECRET"
            ),
            scopes=payload.get(
                "scopes",
                [DRIVE_FILE_SCOPE],
            ),
            expiry=expiry,
        )

        if (
            credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(
                GoogleAuthRequest()
            )

            self._save_credentials(
                credentials
            )

        if not credentials.valid:
            raise RuntimeError(
                "Google credentials are not valid."
            )

        return credentials

    def _save_credentials(
        self,
        credentials: Credentials,
    ) -> None:

        payload = {
            "token": credentials.token,
            "refresh_token": (
                credentials.refresh_token
            ),
            "token_uri": credentials.token_uri,
            "scopes": list(
                credentials.scopes or []
            ),
            "expiry": (
                credentials.expiry.isoformat()
                if credentials.expiry
                else None
            ),
        }

        TOKEN_FILE.write_text(
            json.dumps(
                payload,
                indent=2,
            )
        )

    @staticmethod
    def _escape_query_value(
        value: str,
    ) -> str:
        return (
            value
            .replace("\\", "\\\\")
            .replace("'", "\\'")
        )

    def list_files(
        self,
        parent_id: str | None = None,
    ) -> list[dict[str, Any]]:

        query_parts = [
            "trashed = false"
        ]

        if parent_id:
            query_parts.append(
                f"'{parent_id}' in parents"
            )

        response = (
            self.service
            .files()
            .list(
                q=" and ".join(query_parts),
                spaces="drive",
                pageSize=100,
                fields=(
                    "files("
                    "id,"
                    "name,"
                    "mimeType,"
                    "modifiedTime,"
                    "webViewLink,"
                    "parents,"
                    "appProperties"
                    ")"
                ),
            )
            .execute()
        )

        return response.get(
            "files",
            [],
        )

    def ensure_folder(
        self,
        folder_name: str,
    ) -> dict[str, Any]:

        safe_name = self._escape_query_value(
            folder_name
        )

        response = (
            self.service
            .files()
            .list(
                q=(
                    f"name = '{safe_name}' "
                    f"and mimeType = '{FOLDER_MIME_TYPE}' "
                    "and trashed = false"
                ),
                spaces="drive",
                pageSize=10,
                fields=(
                    "files("
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink"
                    ")"
                ),
            )
            .execute()
        )

        existing = response.get(
            "files",
            [],
        )

        if existing:
            return existing[0]

        metadata = {
            "name": folder_name,
            "mimeType": FOLDER_MIME_TYPE,
            "appProperties": {
                "ekc_repository": "demo-v1",
            },
        }

        return (
            self.service
            .files()
            .create(
                body=metadata,
                fields=(
                    "id,"
                    "name,"
                    "mimeType,"
                    "webViewLink,"
                    "appProperties"
                ),
            )
            .execute()
        )

    def list_repository_files(
        self,
        repository_tag: str = "demo-v1",
    ) -> list[dict[str, Any]]:

        safe_tag = self._escape_query_value(
            repository_tag
        )

        query = (
            "trashed = false "
            "and appProperties has "
            "{ key='ekc_repository' "
            f"and value='{safe_tag}' }}"
            f" and mimeType != '{FOLDER_MIME_TYPE}'"
        )

        response = (
            self.service
            .files()
            .list(
                q=query,
                spaces="drive",
                pageSize=100,
                fields=(
                    "files("
                    "id,"
                    "name,"
                    "mimeType,"
                    "modifiedTime,"
                    "webViewLink,"
                    "parents,"
                    "appProperties"
                    ")"
                ),
            )
            .execute()
        )

        return response.get(
            "files",
            [],
        )


    def download_file_bytes(
        self,
        file_id: str,
    ) -> bytes:

        return (
            self.service
            .files()
            .get_media(
                fileId=file_id
            )
            .execute()
        )


    def download_json_document(
        self,
        file_id: str,
    ) -> dict[str, Any]:

        raw = self.download_file_bytes(
            file_id
        )

        return json.loads(
            raw.decode("utf-8")
        )


    def upload_json_file(
        self,
        local_path: Path,
        parent_id: str,
        document_id: str,
    ) -> dict[str, Any]:

        safe_name = self._escape_query_value(
            local_path.name
        )

        response = (
            self.service
            .files()
            .list(
                q=(
                    f"'{parent_id}' in parents "
                    f"and name = '{safe_name}' "
                    "and trashed = false"
                ),
                spaces="drive",
                pageSize=10,
                fields="files(id,name)",
            )
            .execute()
        )

        existing = response.get(
            "files",
            [],
        )

        media = MediaFileUpload(
            str(local_path),
            mimetype="application/json",
            resumable=False,
        )

        app_properties = {
            "ekc_repository": "demo-v1",
            "ekc_document_id": document_id,
        }

        fields = (
            "id,"
            "name,"
            "mimeType,"
            "modifiedTime,"
            "webViewLink,"
            "parents,"
            "appProperties"
        )

        # If the seed script is run again,
        # update rather than create duplicates.
        if existing:

            return (
                self.service
                .files()
                .update(
                    fileId=existing[0]["id"],
                    body={
                        "name": local_path.name,
                        "appProperties": (
                            app_properties
                        ),
                    },
                    media_body=media,
                    fields=fields,
                )
                .execute()
            )

        metadata = {
            "name": local_path.name,
            "parents": [parent_id],
            "appProperties": app_properties,
        }

        return (
            self.service
            .files()
            .create(
                body=metadata,
                media_body=media,
                fields=fields,
            )
            .execute()
        )
