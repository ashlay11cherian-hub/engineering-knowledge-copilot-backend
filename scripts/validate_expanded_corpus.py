import json
from pathlib import Path
from collections import Counter, defaultdict

from backend.services.demo_service import get_demo_users


DATA_DIR = Path("backend/data")

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

VALID_ROLES = {
    "engineer",
    "program_manager",
    "hr",
    "executive",
}

VALID_STATUSES = {
    "current",
    "superseded",
}

EXPECTED_PROGRAMS = {
    "GEN3-WLC",
    "TELEMATICS-X",
    "WEARABLE-ORBIT",
    "SMARTGLASS-NOVA",
    "EARBUDS-PULSE",
    "SMARTHOME-HALO",
    "ALL_PROGRAMS",
}


def fail(message):
    raise AssertionError(message)


def main():
    docs = []

    for path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        docs.append(data)

    print("=" * 72)
    print("CORPUS INTEGRITY VALIDATION")
    print("=" * 72)

    # ---------------------------------------------------------
    # Basic count
    # ---------------------------------------------------------

    print("\n[1] Document count")

    if len(docs) != 50:
        fail(
            f"Expected 50 documents, found {len(docs)}"
        )

    print("PASS: 50 documents found.")

    # ---------------------------------------------------------
    # Required fields
    # ---------------------------------------------------------

    print("\n[2] Required fields")

    for doc in docs:
        missing = REQUIRED_FIELDS - set(doc.keys())

        if missing:
            fail(
                f"{doc.get('document_id')} missing fields: "
                f"{sorted(missing)}"
            )

    print("PASS: all documents contain required fields.")

    # ---------------------------------------------------------
    # Unique IDs
    # ---------------------------------------------------------

    print("\n[3] Document IDs")

    ids = [
        doc["document_id"]
        for doc in docs
    ]

    if len(ids) != len(set(ids)):
        duplicates = [
            item
            for item, count in Counter(ids).items()
            if count > 1
        ]

        fail(
            f"Duplicate document IDs: {duplicates}"
        )

    print("PASS: all document IDs are unique.")

    # ---------------------------------------------------------
    # Classifications
    # ---------------------------------------------------------

    print("\n[4] Classifications")

    invalid = [
        doc["document_id"]
        for doc in docs
        if doc["classification"]
        not in VALID_CLASSIFICATIONS
    ]

    if invalid:
        fail(
            f"Documents with invalid classifications: {invalid}"
        )

    print("PASS: classifications are valid.")

    # ---------------------------------------------------------
    # Roles
    # ---------------------------------------------------------

    print("\n[5] Allowed roles")

    for doc in docs:
        invalid_roles = (
            set(doc["allowed_roles"])
            - VALID_ROLES
        )

        if invalid_roles:
            fail(
                f"{doc['document_id']} has invalid roles: "
                f"{sorted(invalid_roles)}"
            )

    print("PASS: allowed roles are valid.")

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    print("\n[6] Document status")

    invalid = [
        doc["document_id"]
        for doc in docs
        if doc["document_status"]
        not in VALID_STATUSES
    ]

    if invalid:
        fail(
            f"Documents with invalid status: {invalid}"
        )

    print("PASS: document statuses are valid.")

    # ---------------------------------------------------------
    # Program IDs
    # ---------------------------------------------------------

    print("\n[7] Program IDs")

    invalid = [
        doc["document_id"]
        for doc in docs
        if doc["program_id"]
        not in EXPECTED_PROGRAMS
    ]

    if invalid:
        fail(
            f"Documents with invalid program IDs: {invalid}"
        )

    print("PASS: program IDs are valid.")

    # ---------------------------------------------------------
    # Authority ranks
    # ---------------------------------------------------------

    print("\n[8] Authority ranks")

    for doc in docs:
        rank = doc["authority_rank"]

        if (
            not isinstance(rank, int)
            or rank < 0
            or rank > 100
        ):
            fail(
                f"{doc['document_id']} invalid authority rank: "
                f"{rank}"
            )

    print("PASS: authority ranks are valid.")

    # ---------------------------------------------------------
    # Content
    # ---------------------------------------------------------

    print("\n[9] Content")

    empty = [
        doc["document_id"]
        for doc in docs
        if not doc["content"].strip()
    ]

    if empty:
        fail(
            f"Documents with empty content: {empty}"
        )

    print("PASS: all documents contain content.")

    # ---------------------------------------------------------
    # Superseded evidence
    # ---------------------------------------------------------

    print("\n[10] Superseded records")

    superseded = [
        doc
        for doc in docs
        if doc["document_status"] == "superseded"
    ]

    if len(superseded) < 5:
        fail(
            "Expected at least 5 superseded records."
        )

    for doc in superseded:
        if doc["authority_rank"] >= 80:
            fail(
                f"Superseded record {doc['document_id']} "
                "has unexpectedly high authority."
            )

    print(
        f"PASS: {len(superseded)} superseded records available."
    )

    # ---------------------------------------------------------
    # Users
    # ---------------------------------------------------------

    print("\n[11] Synthetic users")

    users = get_demo_users()

    user_ids = {
        user.user_id
        for user in users
    }

    expected_users = {
        "alex",
        "sarah",
        "chris",
        "maya",
        "daniel",
        "priya",
        "evan",
    }

    if user_ids != expected_users:
        fail(
            f"Unexpected users. Found: {sorted(user_ids)}"
        )

    print("PASS: 7 synthetic users available.")

    # ---------------------------------------------------------
    # Program coverage by users
    # ---------------------------------------------------------

    print("\n[12] Program access coverage")

    engineering_programs = (
        EXPECTED_PROGRAMS
        - {"ALL_PROGRAMS"}
    )

    covered_programs = set()

    for user in users:
        if user.role not in {
            "engineer",
            "program_manager",
        }:
            continue

        covered_programs.update(
            program
            for program in user.assigned_programs
            if program != "ALL_PROGRAMS"
        )

    missing_coverage = (
        engineering_programs
        - covered_programs
    )

    if missing_coverage:
        fail(
            "No engineering/PM persona assigned to: "
            f"{sorted(missing_coverage)}"
        )

    print(
        "PASS: every engineering program has an "
        "assigned engineering or PM persona."
    )

    # ---------------------------------------------------------
    # Known conflict / supersession scenarios
    # ---------------------------------------------------------

    print("\n[12B] Unresolved specification conflict fixture")

    by_id_for_spec = {
        doc["document_id"]: doc
        for doc in docs
    }

    required_spec_ids = [
        "SPEC-120",
        "SPEC-121",
    ]

    missing_specs = [
        document_id
        for document_id in required_spec_ids
        if document_id not in by_id_for_spec
    ]

    if missing_specs:
        fail(
            f"Gen-3 specification conflict fixture missing: {missing_specs}"
        )

    spec_a = by_id_for_spec["SPEC-120"]
    spec_b = by_id_for_spec["SPEC-121"]

    if spec_a["program_id"] != "GEN3-WLC":
        fail("SPEC-120 must belong to GEN3-WLC.")

    if spec_b["program_id"] != "GEN3-WLC":
        fail("SPEC-121 must belong to GEN3-WLC.")

    if spec_a["document_status"] != "current":
        fail("SPEC-120 must be current.")

    if spec_b["document_status"] != "current":
        fail("SPEC-121 must be current.")

    if spec_a["authority_rank"] != spec_b["authority_rank"]:
        fail(
            "SPEC-120 and SPEC-121 must have equal authority "
            "for the unresolved-conflict fixture."
        )

    if spec_a["content"] == spec_b["content"]:
        fail(
            "SPEC-120 and SPEC-121 must contain conflicting values."
        )

    if "60" not in spec_a["content"]:
        fail("SPEC-120 must contain the 60°C limit.")

    if "65" not in spec_b["content"]:
        fail("SPEC-121 must contain the 65°C limit.")

    print(
        "PASS: unresolved Gen-3 surface-temperature "
        "specification conflict fixture is valid."
    )

    print("\n[13] Conflict scenarios")

    by_id = {
        doc["document_id"]: doc
        for doc in docs
    }

    conflict_sets = {
        "GEN3-WLC": [
            "MEMO-202",
            "VAL-037",
            "JIRA-889",
        ],
        "TELEMATICS-X": [
            "NOTE-318",
            "JIRA-317",
            "ECR-319",
        ],
        "WEARABLE-ORBIT": [
            "NOTE-404",
            "JIRA-403",
            "DVT-405",
        ],
        "SMARTGLASS-NOVA": [
            "NOTE-503",
            "JIRA-504",
            "ECR-505",
        ],
        "EARBUDS-PULSE": [
            "NOTE-603",
            "JIRA-604",
            "ECR-605",
        ],
        "SMARTHOME-HALO": [
            "NOTE-703",
            "JIRA-704",
            "ECR-705",
        ],
    }

    for program, document_ids in conflict_sets.items():
        missing = [
            document_id
            for document_id in document_ids
            if document_id not in by_id
        ]

        if missing:
            fail(
                f"{program} conflict scenario missing: {missing}"
            )

        first = by_id[document_ids[0]]

        if first["document_status"] != "superseded":
            fail(
                f"{document_ids[0]} should be superseded."
            )

    print(
        f"PASS: {len(conflict_sets)} conflict/supersession "
        "scenarios are present."
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 72)
    print("VALIDATION SUMMARY")
    print("=" * 72)

    print(
        "Programs:",
        Counter(
            doc["program_id"]
            for doc in docs
        ),
    )

    print(
        "Statuses:",
        Counter(
            doc["document_status"]
            for doc in docs
        ),
    )

    print(
        "Classifications:",
        Counter(
            doc["classification"]
            for doc in docs
        ),
    )

    print("\nSUCCESS: expanded corpus integrity validation passed.")


if __name__ == "__main__":
    main()
