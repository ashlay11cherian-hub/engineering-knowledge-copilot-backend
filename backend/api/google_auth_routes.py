import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow


load_dotenv()


router = APIRouter(
    prefix="/api/auth/google",
    tags=["Google OAuth"],
)


SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
]


BACKEND_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = BACKEND_DIR / "runtime"
TOKEN_FILE = RUNTIME_DIR / "google_token.json"


def _get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable is missing: {name}"
        )

    return value


def _client_config() -> dict:
    client_id = _get_required_env("GOOGLE_CLIENT_ID")
    client_secret = _get_required_env("GOOGLE_CLIENT_SECRET")
    redirect_uri = _get_required_env("GOOGLE_REDIRECT_URI")

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


@router.get("/login")
def google_login(request: Request):
    redirect_uri = _get_required_env("GOOGLE_REDIRECT_URI")

    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        autogenerate_code_verifier=True,
    )

    flow.redirect_uri = redirect_uri

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    request.session["google_oauth_state"] = state

    # PKCE: preserve the verifier generated during login
    # so the callback can use the exact same value.
    request.session["google_code_verifier"] = flow.code_verifier

    return RedirectResponse(
        authorization_url,
        status_code=302,
    )


@router.get("/callback")
def google_callback(request: Request):
    oauth_error = request.query_params.get("error")

    if oauth_error:
        raise HTTPException(
            status_code=400,
            detail=f"Google authorization failed: {oauth_error}",
        )

    expected_state = request.session.get(
        "google_oauth_state"
    )

    returned_state = request.query_params.get("state")

    if not expected_state or returned_state != expected_state:
        raise HTTPException(
            status_code=400,
            detail="OAuth state validation failed.",
        )

    code_verifier = request.session.get(
        "google_code_verifier"
    )

    if not code_verifier:
        raise HTTPException(
            status_code=400,
            detail="OAuth PKCE code verifier is missing.",
        )

    redirect_uri = _get_required_env("GOOGLE_REDIRECT_URI")

    # Recreate the flow with the SAME PKCE verifier
    # generated during /login.
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        state=expected_state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )

    flow.redirect_uri = redirect_uri

    flow.fetch_token(
        authorization_response=str(request.url)
    )

    credentials = flow.credentials

    RUNTIME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    token_payload = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "scopes": list(credentials.scopes or []),
        "expiry": (
            credentials.expiry.isoformat()
            if credentials.expiry
            else None
        ),
    }

    TOKEN_FILE.write_text(
        json.dumps(
            token_payload,
            indent=2,
        )
    )

    request.session.pop(
        "google_oauth_state",
        None,
    )

    request.session.pop(
        "google_code_verifier",
        None,
    )

    return {
        "status": "connected",
        "provider": "google_drive",
        "message": "Google Drive connected successfully.",
        "refresh_token_received": bool(
            credentials.refresh_token
        ),
        "granted_scopes": list(
            credentials.scopes or []
        ),
    }


@router.get("/status")
def google_status():
    if not TOKEN_FILE.exists():
        return {
            "connected": False,
            "provider": "google_drive",
        }

    return {
        "connected": True,
        "provider": "google_drive",
    }
