from typing import Any


REQUIRED_FIELDS = {
    "document_id",
    "title",
    "source_type",
    "department",
    "classification",
    "allowed_roles",
    "revision",
    "content",
    "program_id",
    "authority_rank",
    "document_status",
}

VALID_CLASSIFICATIONS = {
    "internal",
    "confidential",
    "restricted",
    "highly_restricted",
}

VALID_STATUSES = {
    "current",
    "superseded",
}

VALID_ROLES = {
    "engineer",
    "program_manager",
    "hr",
    "executive",
}


def _require_non_empty_string(
    document: dict[str, Any],
    field: str,
) -> None:
    value = document.get(field)

    if not isinstance(value, str):
        raise ValueError(
            f"{field} must be a string"
        )

    if not value.strip():
        raise ValueError(
            f"{field} must not be empty"
        )


def validate_document(
    document: dict[str, Any],
) -> None:
    if not isinstance(document, dict):
        raise ValueError(
            "document must be a JSON object"
        )

    missing = (
        REQUIRED_FIELDS
        - set(document.keys())
    )

    if missing:
        raise ValueError(
            f"{document.get('document_id')} "
            f"missing fields: {sorted(missing)}"
        )

    for field in [
        "document_id",
        "title",
        "source_type",
        "department",
        "revision",
        "content",
        "program_id",
    ]:
        _require_non_empty_string(
            document,
            field,
        )

    classification = (
        document["classification"]
    )

    if classification not in VALID_CLASSIFICATIONS:
        raise ValueError(
            f"{document['document_id']} "
            "invalid classification"
        )

    status = document["document_status"]

    if status not in VALID_STATUSES:
        raise ValueError(
            f"{document['document_id']} "
            "invalid document status"
        )

    roles = document["allowed_roles"]

    if not isinstance(roles, list):
        raise ValueError(
            f"{document['document_id']} "
            "allowed_roles must be a list"
        )

    if not roles:
        raise ValueError(
            f"{document['document_id']} "
            "allowed_roles must not be empty"
        )

    if not all(
        isinstance(role, str)
        for role in roles
    ):
        raise ValueError(
            f"{document['document_id']} "
            "allowed_roles entries must be strings"
        )

    invalid_roles = (
        set(roles)
        - VALID_ROLES
    )

    if invalid_roles:
        raise ValueError(
            f"{document['document_id']} "
            f"invalid roles: {sorted(invalid_roles)}"
        )

    authority_rank = (
        document["authority_rank"]
    )

    if (
        isinstance(authority_rank, bool)
        or not isinstance(
            authority_rank,
            int,
        )
    ):
        raise ValueError(
            f"{document['document_id']} "
            "authority_rank must be int"
        )

    if not 0 <= authority_rank <= 100:
        raise ValueError(
            f"{document['document_id']} "
            "authority_rank must be between 0 and 100"
        )


def validate_document_batch(
    documents: list[dict[str, Any]],
) -> None:
    seen_ids: set[str] = set()

    for document in documents:
        validate_document(document)

        document_id = (
            document["document_id"]
        )

        if document_id in seen_ids:
            raise ValueError(
                "Duplicate document_id: "
                f"{document_id}"
            )

        seen_ids.add(document_id)
