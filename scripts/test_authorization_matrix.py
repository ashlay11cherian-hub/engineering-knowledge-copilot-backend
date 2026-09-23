import json
import sys
from pathlib import Path

# Allow this script to import the backend package when executed directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.services.demo_service import get_demo_users
from backend.src.auth import is_authorized


DATA_DIR = ROOT / "backend" / "data"


def load_documents():
    documents = {}

    for path in sorted(DATA_DIR.glob("*.json")):
        document = json.loads(path.read_text())
        documents[document["document_id"]] = document

    return documents


def load_users():
    users = {}

    for user in get_demo_users():
        users[user.user_id] = user.model_dump()

    return users


TEST_CASES = [
    # ----------------------------------------------------------
    # Alex — GEN3-WLC engineer / internal
    # ----------------------------------------------------------
    (
        "alex",
        "VAL-037",
        True,
        "Alex can access GEN3-WLC internal validation",
    ),
    (
        "alex",
        "JIRA-889",
        True,
        "Alex can access GEN3-WLC engineering investigation",
    ),
    (
        "alex",
        "FIN-042",
        False,
        "Alex cannot access confidential GEN3 finance",
    ),
    (
        "alex",
        "REQ-401",
        False,
        "Alex cannot access Orbit because it is another program",
    ),

    # ----------------------------------------------------------
    # Sarah — PM / GEN3-WLC + TELEMATICS-X / confidential
    # ----------------------------------------------------------
    (
        "sarah",
        "ECR-238",
        True,
        "Sarah can access confidential GEN3 change request",
    ),
    (
        "sarah",
        "FIN-042",
        True,
        "Sarah can access GEN3 finance",
    ),
    (
        "sarah",
        "REQ-301",
        True,
        "Sarah can access Telematics engineering requirements",
    ),
    (
        "sarah",
        "FIN-320",
        True,
        "Sarah can access Telematics finance",
    ),
    (
        "sarah",
        "REQ-401",
        False,
        "Sarah cannot access Orbit because it is unassigned",
    ),
    (
        "sarah",
        "HR-101",
        False,
        "Sarah cannot access HR-only records",
    ),

    # ----------------------------------------------------------
    # Maya — Orbit engineer / internal
    # ----------------------------------------------------------
    (
        "maya",
        "REQ-401",
        True,
        "Maya can access Orbit requirements",
    ),
    (
        "maya",
        "DVT-405",
        True,
        "Maya can access Orbit DVT validation",
    ),
    (
        "maya",
        "FIN-408",
        False,
        "Maya cannot access confidential Orbit finance",
    ),
    (
        "maya",
        "REQ-501",
        False,
        "Maya cannot access Nova smart-glasses documents",
    ),

    # ----------------------------------------------------------
    # Daniel — PM / consumer programs / confidential
    # ----------------------------------------------------------
    (
        "daniel",
        "FIN-408",
        True,
        "Daniel can access Orbit finance",
    ),
    (
        "daniel",
        "ECR-505",
        True,
        "Daniel can access Nova confidential change request",
    ),
    (
        "daniel",
        "FIN-607",
        True,
        "Daniel can access Pulse finance",
    ),
    (
        "daniel",
        "ECR-705",
        True,
        "Daniel can access Halo confidential change request",
    ),
    (
        "daniel",
        "VAL-037",
        False,
        "Daniel cannot access GEN3 because it is unassigned",
    ),
    (
        "daniel",
        "REQ-301",
        False,
        "Daniel cannot access Telematics because it is unassigned",
    ),

    # ----------------------------------------------------------
    # Priya — Halo engineer / internal
    # ----------------------------------------------------------
    (
        "priya",
        "REQ-701",
        True,
        "Priya can access Halo requirements",
    ),
    (
        "priya",
        "JIRA-704",
        True,
        "Priya can access Halo engineering investigation",
    ),
    (
        "priya",
        "ECR-705",
        False,
        "Priya cannot access confidential PM-only Halo ECR",
    ),
    (
        "priya",
        "REQ-601",
        False,
        "Priya cannot access Pulse because it is another program",
    ),

    # ----------------------------------------------------------
    # Chris — HR / ALL_PROGRAMS / restricted
    # ----------------------------------------------------------
    (
        "chris",
        "HR-101",
        True,
        "Chris can access restricted HR policy",
    ),
    (
        "chris",
        "VAL-037",
        False,
        "Chris cannot access product engineering despite ALL_PROGRAMS",
    ),
    (
        "chris",
        "FIN-408",
        False,
        "Chris cannot access product finance",
    ),

    # ----------------------------------------------------------
    # Evan — Executive / ALL_PROGRAMS / highly restricted
    # ----------------------------------------------------------
    (
        "evan",
        "EXEC-007",
        True,
        "Evan can access executive strategy",
    ),
    (
        "evan",
        "VAL-037",
        False,
        "Executive clearance does not bypass document role restrictions",
    ),
    (
        "evan",
        "HR-101",
        False,
        "Executive role does not automatically grant HR access",
    ),
]


def main():
    documents = load_documents()
    users = load_users()

    print("=" * 80)
    print("AUTHORIZATION MATRIX")
    print("=" * 80)

    failures = []

    for user_id, document_id, expected, description in TEST_CASES:

        if user_id not in users:
            failures.append(
                f"Missing user: {user_id}"
            )
            continue

        if document_id not in documents:
            failures.append(
                f"Missing document: {document_id}"
            )
            continue

        actual = is_authorized(
            users[user_id],
            documents[document_id],
        )

        result = (
            "PASS"
            if actual == expected
            else "FAIL"
        )

        expected_text = (
            "ALLOW"
            if expected
            else "BLOCK"
        )

        actual_text = (
            "ALLOW"
            if actual
            else "BLOCK"
        )

        print(
            f"{result:4} | "
            f"{user_id:7} | "
            f"{document_id:13} | "
            f"expected={expected_text:5} | "
            f"actual={actual_text:5} | "
            f"{description}"
        )

        if actual != expected:
            failures.append(
                f"{user_id} / {document_id}: "
                f"expected {expected_text}, "
                f"got {actual_text}"
            )

    # ----------------------------------------------------------
    # Full-corpus leakage checks
    # ----------------------------------------------------------

    print("\n" + "=" * 80)
    print("FULL CORPUS ACCESS SUMMARY")
    print("=" * 80)

    for user_id, user in users.items():

        authorized = [
            document
            for document in documents.values()
            if is_authorized(
                user,
                document,
            )
        ]

        print(
            f"\n{user_id.upper()} "
            f"({user['role']})"
        )

        print(
            "Authorized documents:",
            len(authorized),
        )

        for document in sorted(
            authorized,
            key=lambda item: (
                item["program_id"],
                item["document_id"],
            ),
        ):
            print(
                " ",
                document["document_id"],
                "|",
                document["program_id"],
                "|",
                document["classification"],
                "|",
                document["title"],
            )

        # Users without ALL_PROGRAMS must never retrieve
        # documents from an unrelated product program.
        if "ALL_PROGRAMS" not in user["assigned_programs"]:

            illegal_program_docs = [
                document
                for document in authorized
                if (
                    document["program_id"]
                    != "ALL_PROGRAMS"
                    and document["program_id"]
                    not in user["assigned_programs"]
                )
            ]

            if illegal_program_docs:
                failures.append(
                    f"{user_id} has cross-program access to: "
                    + ", ".join(
                        document["document_id"]
                        for document
                        in illegal_program_docs
                    )
                )

    print("\n" + "=" * 80)

    if failures:
        print("AUTHORIZATION TEST FAILED")
        print("=" * 80)

        for failure in failures:
            print("FAIL:", failure)

        raise SystemExit(1)

    print(
        f"SUCCESS: all {len(TEST_CASES)} "
        "authorization scenarios passed."
    )

    print(
        "SUCCESS: no cross-program leakage detected."
    )


if __name__ == "__main__":
    main()
