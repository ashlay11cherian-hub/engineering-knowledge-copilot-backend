import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.services.demo_service import get_demo_users
from backend.src.auth import filter_authorized_documents
from backend.src.embedding_service import get_client
from backend.src.relevance_gate import evaluate_evidence
from backend.src.vector_index import load_index, semantic_search


DATA_DIR = ROOT / "backend" / "data"
INDEX_PATH = ROOT / "backend" / "embedding_index.json"
OUTPUT_PATH = ROOT / "backend" / "runtime" / "local_retrieval_benchmark.json"


CASES = [
    {
        "id": "GEN3-ROOT-CAUSE",
        "user_id": "sarah",
        "query": (
            "What caused the Gen-3 wireless charger thermal failure?"
        ),
        "answerable": True,
        "expected_docs": [
            "VAL-037",
            "JIRA-889",
        ],
    },
    {
        "id": "GEN3-CORRECTIVE-ACTION",
        "user_id": "sarah",
        "query": (
            "What corrective action was approved for the "
            "Gen-3 wireless charger thermal failure?"
        ),
        "answerable": True,
        "expected_docs": [
            "ECR-238",
            "PLM-G3WLC-C",
            "MFG-061",
        ],
    },
    {
        "id": "TELEM-ROOT-CAUSE",
        "user_id": "sarah",
        "query": (
            "What caused the intermittent LTE network drops "
            "in Telematics-X?"
        ),
        "answerable": True,
        "expected_docs": [
            "JIRA-317",
        ],
    },
    {
        "id": "TELEM-CORRECTIVE-ACTION",
        "user_id": "sarah",
        "query": (
            "What design change was approved to correct the "
            "Telematics-X connectivity problem?"
        ),
        "answerable": True,
        "expected_docs": [
            "ECR-319",
            "PLM-TX-RB",
        ],
    },
    {
        "id": "TELEM-COST",
        "user_id": "sarah",
        "query": (
            "What is the manufacturing cost per unit for "
            "Telematics-X?"
        ),
        "answerable": True,
        "expected_docs": [
            "FIN-320",
        ],
    },
    {
        "id": "ORBIT-ROOT-CAUSE",
        "user_id": "maya",
        "query": (
            "What caused the Orbit wearable heart-rate "
            "sensor dropouts during exercise?"
        ),
        "answerable": True,
        "expected_docs": [
            "JIRA-403",
            "DVT-405",
        ],
    },
    {
        "id": "ORBIT-BATTERY",
        "user_id": "maya",
        "query": (
            "What battery life did the Orbit wearable achieve "
            "during EVT testing?"
        ),
        "answerable": True,
        "expected_docs": [
            "EVT-402",
        ],
    },
    {
        "id": "ORBIT-DVT",
        "user_id": "maya",
        "query": (
            "Did the revised Orbit optical sensor design pass "
            "DVT validation?"
        ),
        "answerable": True,
        "expected_docs": [
            "DVT-405",
        ],
    },
    {
        "id": "ORBIT-FINANCE-BLOCKED",
        "user_id": "maya",
        "query": (
            "What is the Orbit wearable manufacturing cost "
            "per unit?"
        ),
        "answerable": False,
        "expected_docs": [],
    },
    {
        "id": "ORBIT-CHANGE",
        "user_id": "daniel",
        "query": (
            "What mechanical design change was approved to "
            "fix the Orbit sensor dropout issue?"
        ),
        "answerable": True,
        "expected_docs": [
            "ECR-406",
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
        "answerable": True,
        "expected_docs": [
            "JIRA-504",
        ],
    },
    {
        "id": "NOVA-CORRECTIVE-ACTION",
        "user_id": "daniel",
        "query": (
            "What corrective design change was approved for "
            "the Nova smart glasses thermal hotspot?"
        ),
        "answerable": True,
        "expected_docs": [
            "ECR-505",
        ],
    },
    {
        "id": "NOVA-COST",
        "user_id": "daniel",
        "query": (
            "What is the Nova smart glasses manufacturing "
            "cost per unit?"
        ),
        "answerable": True,
        "expected_docs": [
            "FIN-508",
        ],
    },
    {
        "id": "PULSE-ROOT-CAUSE",
        "user_id": "daniel",
        "query": (
            "What caused the wind-noise problem in the Pulse "
            "earbuds?"
        ),
        "answerable": True,
        "expected_docs": [
            "JIRA-604",
        ],
    },
    {
        "id": "PULSE-CORRECTIVE-ACTION",
        "user_id": "daniel",
        "query": (
            "What change was approved to correct the Pulse "
            "earbuds wind-noise issue?"
        ),
        "answerable": True,
        "expected_docs": [
            "ECR-605",
        ],
    },
    {
        "id": "PULSE-BATTERY",
        "user_id": "daniel",
        "query": (
            "How long did the Pulse earbuds battery last "
            "during EVT testing with ANC enabled?"
        ),
        "answerable": True,
        "expected_docs": [
            "EVT-602",
        ],
    },
    {
        "id": "HALO-ROOT-CAUSE",
        "user_id": "priya",
        "query": (
            "What caused the Halo smart home hub to repeatedly "
            "reboot during brownout testing?"
        ),
        "answerable": True,
        "expected_docs": [
            "JIRA-704",
        ],
    },
    {
        "id": "HALO-CORRECTIVE-ACTION",
        "user_id": "daniel",
        "query": (
            "What corrective action was approved for the "
            "Halo brownout reboot problem?"
        ),
        "answerable": True,
        "expected_docs": [
            "ECR-705",
        ],
    },
    {
        "id": "HALO-CERTIFICATION",
        "user_id": "priya",
        "query": (
            "Did the Halo release configuration complete "
            "regulatory verification?"
        ),
        "answerable": True,
        "expected_docs": [
            "CERT-706",
        ],
    },
    {
        "id": "ALEX-CROSS-PROGRAM",
        "user_id": "alex",
        "query": (
            "What caused the Orbit wearable heart-rate "
            "sensor dropout?"
        ),
        "answerable": False,
        "expected_docs": [],
    },
    {
        "id": "SARAH-CROSS-PROGRAM-FINANCE",
        "user_id": "sarah",
        "query": (
            "What is the Orbit wearable manufacturing cost "
            "per unit?"
        ),
        "answerable": False,
        "expected_docs": [],
    },
    {
        "id": "DANIEL-CROSS-PROGRAM",
        "user_id": "daniel",
        "query": (
            "What caused the Gen-3 wireless charger "
            "thermal shutdown?"
        ),
        "answerable": False,
        "expected_docs": [],
    },
    {
        "id": "CHRIS-PRODUCT-FINANCE",
        "user_id": "chris",
        "query": (
            "What are the product unit economics?"
        ),
        "answerable": False,
        "expected_docs": [],
    },
    {
        "id": "UNANSWERABLE-SUPPLIER-YEAR",
        "user_id": "sarah",
        "query": (
            "Which supplier will manufacture the redesigned "
            "Telematics-X antenna in 2028?"
        ),
        "answerable": False,
        "expected_docs": [],
    },
]


def load_documents():
    documents = []

    for path in sorted(DATA_DIR.glob("*.json")):
        documents.append(
            json.loads(path.read_text())
        )

    return documents


def load_users():
    return {
        user.user_id: user.model_dump()
        for user in get_demo_users()
    }


def search_with_retry(
    query,
    index,
    authorized_ids,
    client,
):
    attempts = 3

    for attempt in range(1, attempts + 1):
        try:
            return semantic_search(
                query=query,
                index_entries=index,
                authorized_document_ids=authorized_ids,
                client=client,
                top_k=5,
                minimum_score=0.40,
            )

        except Exception as exc:
            text = str(exc)

            temporary = (
                "503" in text
                or "UNAVAILABLE" in text.upper()
                or "HIGH DEMAND" in text.upper()
            )

            if not temporary or attempt == attempts:
                raise

            wait_seconds = attempt * 3

            print(
                f"Temporary embedding error. "
                f"Retrying in {wait_seconds}s..."
            )

            time.sleep(wait_seconds)

    return []


def main():
    documents = load_documents()
    documents_by_id = {
        document["document_id"]: document
        for document in documents
    }

    users = load_users()

    index = load_index(
        str(INDEX_PATH)
    )

    client = get_client()

    print("=" * 100)
    print("LOCAL RETRIEVAL BENCHMARK")
    print("=" * 100)

    print("Documents:", len(documents))
    print("Index chunks:", len(index))
    print("Queries:", len(CASES))
    print()

    answerable_count = 0
    hit_at_1 = 0
    hit_at_3 = 0
    hit_at_5 = 0

    gate_correct = 0
    gate_false_accept = 0
    gate_false_reject = 0

    leakage_count = 0
    superseded_top1 = 0

    case_reports = []

    for number, case in enumerate(
        CASES,
        start=1,
    ):
        user = users[case["user_id"]]

        authorized_documents = (
            filter_authorized_documents(
                documents,
                user,
            )
        )

        authorized_ids = {
            document["document_id"]
            for document in authorized_documents
        }

        results = search_with_retry(
            query=case["query"],
            index=index,
            authorized_ids=authorized_ids,
            client=client,
        )

        gate = evaluate_evidence(
            query=case["query"],
            results=results,
        )

        result_ids = [
            result["document_id"]
            for result in results
        ]

        expected = set(
            case["expected_docs"]
        )

        leaked = [
            document_id
            for document_id in result_ids
            if document_id not in authorized_ids
        ]

        if leaked:
            leakage_count += len(leaked)

        h1 = False
        h3 = False
        h5 = False

        if case["answerable"]:
            answerable_count += 1

            h1 = bool(
                expected
                & set(result_ids[:1])
            )

            h3 = bool(
                expected
                & set(result_ids[:3])
            )

            h5 = bool(
                expected
                & set(result_ids[:5])
            )

            hit_at_1 += int(h1)
            hit_at_3 += int(h3)
            hit_at_5 += int(h5)

        expected_gate = case["answerable"]

        gate_match = (
            gate.accepted
            == expected_gate
        )

        if gate_match:
            gate_correct += 1

        elif gate.accepted and not expected_gate:
            gate_false_accept += 1

        elif (
            not gate.accepted
            and expected_gate
        ):
            gate_false_reject += 1

        top1_status = None

        if results:
            top1_status = results[0].get(
                "document_status"
            )

            if (
                case["answerable"]
                and top1_status == "superseded"
            ):
                superseded_top1 += 1

        quality_ok = (
            (
                not case["answerable"]
                or h3
            )
            and gate_match
            and not leaked
        )

        status = (
            "PASS"
            if quality_ok
            else "REVIEW"
        )

        print(
            f"[{number:02}/{len(CASES)}] "
            f"{status:6} | "
            f"{case['id']}"
        )

        print(
            "     User:",
            case["user_id"],
        )

        print(
            "     Expected:",
            (
                case["expected_docs"]
                if case["answerable"]
                else "INSUFFICIENT_EVIDENCE"
            ),
        )

        print(
            "     Retrieved:",
            [
                (
                    result["document_id"],
                    result.get(
                        "semantic_score"
                    ),
                    result.get(
                        "document_status"
                    ),
                    result.get(
                        "authority_rank"
                    ),
                )
                for result in results
            ],
        )

        print(
            "     Gate:",
            gate.accepted,
            "| reason:",
            gate.reason,
            "| score:",
            round(
                gate.top_semantic_score,
                4,
            ),
            "| coverage:",
            round(
                gate.query_coverage,
                4,
            ),
        )

        if case["answerable"]:
            print(
                "     Hit@1:",
                h1,
                "| Hit@3:",
                h3,
                "| Hit@5:",
                h5,
            )

        if leaked:
            print(
                "     SECURITY LEAK:",
                leaked,
            )

        print()

        case_reports.append(
            {
                "id": case["id"],
                "user_id": case["user_id"],
                "query": case["query"],
                "answerable": case[
                    "answerable"
                ],
                "expected_docs": case[
                    "expected_docs"
                ],
                "retrieved_docs": [
                    {
                        "document_id": result[
                            "document_id"
                        ],
                        "semantic_score": result.get(
                            "semantic_score"
                        ),
                        "authority_rank": result.get(
                            "authority_rank"
                        ),
                        "document_status": result.get(
                            "document_status"
                        ),
                    }
                    for result in results
                ],
                "hit_at_1": h1,
                "hit_at_3": h3,
                "hit_at_5": h5,
                "gate_expected": expected_gate,
                "gate_accepted": gate.accepted,
                "gate_reason": gate.reason,
                "top_semantic_score": (
                    gate.top_semantic_score
                ),
                "query_coverage": (
                    gate.query_coverage
                ),
                "leaked_documents": leaked,
            }
        )

    hit1_pct = (
        hit_at_1
        / answerable_count
        * 100
    )

    hit3_pct = (
        hit_at_3
        / answerable_count
        * 100
    )

    hit5_pct = (
        hit_at_5
        / answerable_count
        * 100
    )

    gate_accuracy = (
        gate_correct
        / len(CASES)
        * 100
    )

    print("=" * 100)
    print("BENCHMARK SUMMARY")
    print("=" * 100)

    print(
        "Answerable queries:",
        answerable_count,
    )

    print(
        f"Hit@1: {hit_at_1}/{answerable_count} "
        f"({hit1_pct:.1f}%)"
    )

    print(
        f"Hit@3: {hit_at_3}/{answerable_count} "
        f"({hit3_pct:.1f}%)"
    )

    print(
        f"Hit@5: {hit_at_5}/{answerable_count} "
        f"({hit5_pct:.1f}%)"
    )

    print(
        f"Gate accuracy: "
        f"{gate_correct}/{len(CASES)} "
        f"({gate_accuracy:.1f}%)"
    )

    print(
        "False accepts:",
        gate_false_accept,
    )

    print(
        "False rejects:",
        gate_false_reject,
    )

    print(
        "Superseded document ranked #1:",
        superseded_top1,
    )

    print(
        "Unauthorized retrieval leakage:",
        leakage_count,
    )

    summary = {
        "repository": "local_demo",
        "document_count": len(documents),
        "index_chunk_count": len(index),
        "query_count": len(CASES),
        "answerable_query_count": (
            answerable_count
        ),
        "hit_at_1": hit_at_1,
        "hit_at_1_percent": hit1_pct,
        "hit_at_3": hit_at_3,
        "hit_at_3_percent": hit3_pct,
        "hit_at_5": hit_at_5,
        "hit_at_5_percent": hit5_pct,
        "gate_correct": gate_correct,
        "gate_accuracy_percent": (
            gate_accuracy
        ),
        "false_accepts": gate_false_accept,
        "false_rejects": gate_false_reject,
        "superseded_top1": (
            superseded_top1
        ),
        "unauthorized_leakage": (
            leakage_count
        ),
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "summary": summary,
                "cases": case_reports,
            },
            indent=2,
        )
        + "\n"
    )

    print()
    print(
        "Saved report:",
        OUTPUT_PATH,
    )

    if leakage_count:
        raise SystemExit(
            "FAILED: unauthorized document leakage detected."
        )

    print()
    print(
        "SECURITY CHECK PASSED: "
        "no unauthorized retrieval leakage."
    )

    print(
        "QUALITY RESULTS RECORDED. "
        "Review metrics before tuning thresholds."
    )


if __name__ == "__main__":
    main()
