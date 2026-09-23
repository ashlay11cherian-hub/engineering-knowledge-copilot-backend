from fastapi import APIRouter, HTTPException

from backend.connectors.google_drive import (
    GoogleDriveConnector,
)

from backend.services.google_drive_sync_service import (
    sync_google_drive_repository,
)

router = APIRouter(
    prefix="/api/google-drive",
    tags=["Google Drive"],
)


@router.get("/files")
def list_google_drive_files():

    try:
        connector = GoogleDriveConnector()

        files = connector.list_files()

        return {
            "provider": "google_drive",
            "connected": True,
            "file_count": len(files),
            "files": files,
        }

    except RuntimeError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail=(
                "Google Drive API request failed."
            ),
        )
@router.post("/sync")
def sync_google_drive(
    force: bool = False,
):
    try:
        return sync_google_drive_repository(
            force=force
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Google Drive repository sync failed.",
        )