from typing import Any

CLEARANCE_LEVELS = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
    "highly_restricted": 4,
}


def user_has_required_clearance(
    user_clearance: str,
    document_classification: str,
) -> bool:
    return CLEARANCE_LEVELS.get(user_clearance, -1) >= CLEARANCE_LEVELS.get(
        document_classification,
        999,
    )


def program_is_relevant(
    assigned_programs: list[str],
    document_program_id: str,
) -> bool:
    return (
        "ALL_PROGRAMS" in assigned_programs
        or document_program_id == "ALL_PROGRAMS"
        or document_program_id in assigned_programs
    )


def is_authorized(
    user: dict[str, Any],
    document: dict[str, Any],
) -> bool:
    role_allowed = user.get("role") in document.get("allowed_roles", [])
    program_allowed = program_is_relevant(
        user.get("assigned_programs", []),
        document.get("program_id", ""),
    )
    clearance_allowed = user_has_required_clearance(
        user.get("clearance", ""),
        document.get("classification", ""),
    )

    return role_allowed and program_allowed and clearance_allowed


def filter_authorized_documents(
    documents: list[dict[str, Any]],
    user: dict[str, Any],
) -> list[dict[str, Any]]:
    """Filter by role, assigned program, and document classification."""
    return [
        document
        for document in documents
        if is_authorized(user, document)
    ]
