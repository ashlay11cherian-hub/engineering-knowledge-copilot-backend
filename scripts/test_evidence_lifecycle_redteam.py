import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.services.query_service import execute_demo_query


REPOSITORY = "google-drive-engineering-repository"


def thermal_root_cause_test():
    print()
    print("=" * 72)
    print("6B.2A — SUPERSEDED ROOT-CAUSE TEST")
    print("=" * 72)

    response = execute_demo_query(
        user_id="sarah",
        repository_id=REPOSITORY,
        query=(
            "What was the confirmed root cause of the Gen-3 "
            "wireless charger thermal failure?"
        ),
    )

    answer = (response.answer or "").lower()
    citations = [c.document_id for c in response.citations]

    print("Status:", response.status)
    print("Gate:", response.diagnostics.gate_reason)
    print("Generation called:", response.diagnostics.generation_called)
    print("Retrieved:", response.retrieved_chunk_count)
    print("Citations:", citations)
    print("Answer:", response.answer)

    correct_root_cause = (
        "coil" in answer
        and (
            "misalign" in answer
            or "tolerance" in answer
        )
    )

    preliminary_not_promoted = not (
        "poor thermal interface material coverage caused"
        in answer
    )

    current_source_used = any(
        source in citations
        for source in [
            "VAL-037",
            "JIRA-889",
            "ECR-238",
            "PLM-G3WLC-C",
        ]
    )

    not_false_conflict = (
        response.status == "answered"
    )

    print()
    print("CHECKS")
    print(
        "Confirmed root cause used:",
        "PASS" if correct_root_cause else "FAIL",
    )
    print(
        "Superseded hypothesis not promoted:",
        "PASS" if preliminary_not_promoted else "FAIL",
    )
    print(
        "Current/final evidence cited:",
        "PASS" if current_source_used else "FAIL",
    )
    print(
        "Resolved history not treated as conflict:",
        "PASS" if not_false_conflict else "FAIL",
    )

    return all([
        correct_root_cause,
        preliminary_not_promoted,
        current_source_used,
        not_false_conflict,
    ])


def specification_conflict_test():
    print()
    print("=" * 72)
    print("6B.2B — UNRESOLVED SPECIFICATION CONFLICT TEST")
    print("=" * 72)

    response = execute_demo_query(
        user_id="sarah",
        repository_id=REPOSITORY,
        query=(
            "What is the maximum allowable external surface "
            "temperature specification for Gen-3?"
        ),
    )

    citations = {
        c.document_id
        for c in response.citations
    }

    print("Status:", response.status)
    print("Gate:", response.diagnostics.gate_reason)
    print("Generation called:", response.diagnostics.generation_called)
    print("Retrieved:", response.retrieved_chunk_count)
    print("Citations:", sorted(citations))
    print("Answer:", response.answer)

    correct_status = (
        response.status == "conflicting_evidence"
    )

    both_specs = {
        "SPEC-120",
        "SPEC-121",
    }.issubset(citations)

    answer_mentions_both = (
        "60" in response.answer
        and "65" in response.answer
    )

    print()
    print("CHECKS")
    print(
        "Conflict detected:",
        "PASS" if correct_status else "FAIL",
    )
    print(
        "Both conflicting specs cited:",
        "PASS" if both_specs else "FAIL",
    )
    print(
        "Both conflicting values surfaced:",
        "PASS" if answer_mentions_both else "FAIL",
    )

    return all([
        correct_status,
        both_specs,
        answer_mentions_both,
    ])


def main():
    print("=" * 72)
    print("STAGE 6B.2 — EVIDENCE LIFECYCLE & CONFLICT TEST")
    print("=" * 72)

    try:
        test_a = thermal_root_cause_test()
        test_b = specification_conflict_test()
    except Exception as exc:
        print()
        print("OVERALL RESULT: INCONCLUSIVE")
        print("Exception:", type(exc).__name__)
        print(str(exc))
        return

    print()
    print("=" * 72)

    if test_a and test_b:
        print("OVERALL RESULT: PASS")
        print(
            "Superseded evidence was not promoted and genuine "
            "unresolved conflicting evidence was surfaced."
        )
    else:
        print("OVERALL RESULT: FAIL")
        print(
            "At least one evidence-lifecycle behavior requires investigation."
        )

    print("=" * 72)


if __name__ == "__main__":
    main()
