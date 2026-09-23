import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.services.query_service import execute_demo_query
from backend.services.demo_service import get_demo_users
from backend.src.auth import filter_authorized_documents


REPOSITORY_ID = "google-drive-engineering-repository"

DRIVE_DOCS_PATH = (
    ROOT
    / "backend"
    / "runtime"
    / "google_drive_documents.json"
)

OUTPUT_PATH = (
    ROOT
    / "backend"
    / "runtime"
    / "grounded_answer_regression.json"
)


CASES = [
    {
        "id": "GEN3-ROOT-CORRECTIVE",
        "user_id": "sarah",
        "query": (
            "What caused the Gen-3 wireless charger thermal "
            "failure, and what corrective action was approved?"
        ),
        "expected_status": "answered",
        "expected_any_citation": [
            "VAL-037",
            "JIRA-889",
            "ECR-238",
            "PLM-G3WLC-C",
        ],
    },
    {
        "id": "TELEMATICS-ROOT-CAUSE",
        "user_id": "sarah",
        "query": (
            "What caused the intermittent LTE network drops "
            "in Telematics-X?"
        ),
        "expected_status": "answered",
        "expected_any_citation": [
            "JIRA-317",
            "ECR-319",
        ],
    },
    {
        "id": "ORBIT-ROOT-CAUSE",
        "user_id": "maya",
        "query": (
            "What caused the Orbit wearable heart-rate "
            "sensor dropouts during exercise?"
        ),
        "expected_status": "answered",
        "expected_any_citation": [
            "JIRA-403",
            "DVT-405",
        ],
    },
    {
        "id": "NOVA-ROOT-CAUSE",
        "user_id": "daniel",
        "query": (
            "What caused the right-temple thermal hotspot "
            "in Nova smart glasses?"
        ),
        "expected_status": "answered",
        "expected_any_citation": [
            "JIRA-504",
            "ECR-505",
        ],
    },
    {
        "id": "PULSE-ROOT-CAUSE",
        "user_id": "daniel",
        "query": (
            "What caused the wind-noise problem in the "
            "Pulse earbuds?"
        ),
        "expected_status": "answered",
        "expected_any_citation": [
            "JIRA-604",
            "ECR-605",
        ],
    },
    {
        "id": "HALO-ROOT-CAUSE",
        "user_id": "priya",
        "query": (
            "What caused the Halo smart home hub to reboot "
            "during brownout testing?"
        ),
        "expected_status": "answered",
        "expected_any_citation": [
            "JIRA-704",
        ],
    },
    {
        "id": "SARAH-CROSS-PROGRAM-COST",
        "user_id": "sarah",
        "query": (
            "What is the Orbit wearable manufacturing "
            "cost per unit?"
        ),
        "expected_status": "insufficient_evidence",
        "expected_any_citation": [],
    },
    {
        "id": "DANIEL-CROSS-PROGRAM",
        "user_id": "daniel",
        "query": (
            "What caused the Gen-3 wireless charger "
            "thermal shutdown?"
        ),
        "expected_status": "insufficient_evidence",
        "expected_any_citation": [],
    },
    {
        "id": "CHRIS-PRODUCT-FINANCE",
        "user_id": "chris",
        "query": (
            "What are the product unit economics?"
        ),
        "expected_status": "insufficient_evidence",
        "expected_any_citation": [],
    },
    {
        "id": "UNSUPPORTED-SUPPLIER-2028",
        "user_id": "sarah",
        "query": (
            "Which supplier will manufacture the redesigned "
            "Telematics-X antenna in 2028?"
        ),
        "expected_status": "insufficient_evidence",
        "expected_any_citation": [],
    },
]


def run_with_retry(case):
    attempts = 4

    for attempt in range(1, attempts + 1):
        try:
            return execute_demo_query(
                user_id=case["user_id"],
                repository_id=REPOSITORY_ID,
                query=case["query"],
            )

        except Exception as exc:
            message = str(exc)

            temporary = (
                "503" in message
                or "UNAVAILABLE" in message.upper()
                or "HIGH DEMAND" in message.upper()
                or "TEMPORARILY UNAVAILABLE" in message.upper()
                or "RETRY SHORTLY" in message.upper()
            )

            if not temporary or attempt == attempts:
                raise

            wait_seconds = 8 * (2 ** (attempt - 1))

            print(
                f"     Temporary Gemini error. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)


def main():
    documents = json.loads(
        DRIVE_DOCS_PATH.read_text()
    )

    users = {
        user.user_id: user.model_dump()
        for user in get_demo_users()
    }

    document_ids = {
        doc["document_id"]
        for doc in documents
    }

    failures = []
    reports = []

    print("=" * 100)
    print("GROUNDED ANSWER REGRESSION")
    print("=" * 100)
    print("Repository:", REPOSITORY_ID)
    print("Cases:", len(CASES))
    print()

    for number, case in enumerate(
        CASES,
        start=1,
    ):
        print(
            f"[{number:02}/{len(CASES)}] "
            f"{case['id']}"
        )

        response = run_with_retry(case)

        data = response.model_dump()

        status = data.get("status")

        citations = data.get(
            "citations",
            [],
        )

        citation_ids = [
            citation.get("document_id")
            or citation.get("source_id")
            for citation in citations
        ]

        citation_ids = [
            cid
            for cid in citation_ids
            if cid
        ]

        expected_citations = set(
            case["expected_any_citation"]
        )

        status_ok = (
            status
            == case["expected_status"]
        )

        citation_match = True

        if (
            case["expected_status"]
            == "answered"
        ):
            citation_match = bool(
                expected_citations
                & set(citation_ids)
            )

        # ------------------------------------------------------
        # Validate that every returned citation exists
        # ------------------------------------------------------

        invalid_citations = [
            cid
            for cid in citation_ids
            if cid not in document_ids
        ]

        # ------------------------------------------------------
        # Validate that every citation was authorized
        # for this user
        # ------------------------------------------------------

        user = users[
            case["user_id"]
        ]

        authorized_docs = (
            filter_authorized_documents(
                documents,
                user,
            )
        )

        authorized_ids = {
            doc["document_id"]
            for doc in authorized_docs
        }

        unauthorized_citations = [
            cid
            for cid in citation_ids
            if cid not in authorized_ids
        ]

        passed = (
            status_ok
            and citation_match
            and not invalid_citations
            and not unauthorized_citations
        )

        print(
            "     Status:",
            status,
            "| expected:",
            case["expected_status"],
        )

        print(
            "     Confidence:",
            data.get("confidence"),
        )

        print(
            "     Citations:",
            citation_ids,
        )

        print(
            "     Retrieved chunks:",
            data.get(
                "retrieved_chunk_count"
            ),
        )

        diagnostics = data.get(
            "diagnostics",
            {}
        )

        print(
            "     Gate:",
            diagnostics.get(
                "gate_reason"
            ),
        )

        print(
            "     Result:",
            "PASS" if passed else "FAIL",
        )

        print()

        if not passed:
            failures.append(
                case["id"]
            )

        reports.append(
            {
                "id": case["id"],
                "user_id": case["user_id"],
                "query": case["query"],
                "expected_status": case[
                    "expected_status"
                ],
                "actual_status": status,
                "citation_ids": citation_ids,
                "expected_any_citation": (
                    case[
                        "expected_any_citation"
                    ]
                ),
                "status_ok": status_ok,
                "citation_match": (
                    citation_match
                ),
                "invalid_citations": (
                    invalid_citations
                ),
                "unauthorized_citations": (
                    unauthorized_citations
                ),
                "passed": passed,
                "diagnostics": diagnostics,
            }
        )

    passed_count = (
        len(CASES)
        - len(failures)
    )

    print("=" * 100)
    print("REGRESSION SUMMARY")
    print("=" * 100)

    print(
        "Passed:",
        f"{passed_count}/{len(CASES)}",
    )

    print(
        "Failed:",
        len(failures),
    )

    print(
        "Unauthorized citations:",
        sum(
            len(
                report[
                    "unauthorized_citations"
                ]
            )
            for report in reports
        ),
    )

    print(
        "Invalid citations:",
        sum(
            len(
                report[
                    "invalid_citations"
                ]
            )
            for report in reports
        ),
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "repository_id": (
                    REPOSITORY_ID
                ),
                "passed": passed_count,
                "failed": len(failures),
                "cases": reports,
            },
            indent=2,
            default=str,
        )
        + "\n"
    )

    print()
    print(
        "Saved report:",
        OUTPUT_PATH,
    )

    if failures:
        print()
        print(
            "FAILED CASES:",
            failures,
        )

        raise SystemExit(1)

    print()
    print(
        "SUCCESS: grounded-answer "
        "regression passed."
    )


if __name__ == "__main__":
    main()
