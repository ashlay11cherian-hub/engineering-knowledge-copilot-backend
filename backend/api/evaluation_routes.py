import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/api/evaluation",
    tags=["Evaluation"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LATEST_EVALUATION_FILE = (
    PROJECT_ROOT
    / "evaluation"
    / "results"
    / "latest.json"
)


@router.get("/latest")
def get_latest_evaluation():
    """
    Return the latest saved golden-evaluation report.

    This endpoint does not run the evaluation and does not call
    the generation provider. It only reads the latest persisted result.
    """

    if not LATEST_EVALUATION_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="No evaluation report is available.",
        )

    try:
        report = json.loads(
            LATEST_EVALUATION_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Latest evaluation report contains invalid JSON.",
        ) from exc

    summary = report.get("summary")

    if not isinstance(summary, dict):
        raise HTTPException(
            status_code=500,
            detail="Evaluation report is missing a valid summary.",
        )

    results = report.get("results")

    if not isinstance(results, list):
        raise HTTPException(
            status_code=500,
            detail="Evaluation report is missing valid case results.",
        )

    return report
