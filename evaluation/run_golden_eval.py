import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.query_service import execute_demo_query


GOLDEN_FILE = ROOT / "evaluation" / "golden_cases.json"
RESULTS_DIR = ROOT / "evaluation" / "results"


def load_cases():
    return json.loads(GOLDEN_FILE.read_text())


def safe_diagnostics(response):
    diagnostics = response.diagnostics
    if diagnostics is None:
        return {}
    return diagnostics.model_dump()


def evaluate_case(case):
    started = perf_counter()

    try:
        response = execute_demo_query(
            user_id=case["user_id"],
            repository_id=case["repository_id"],
            query=case["query"],
        )
    except Exception as exc:
        elapsed_ms = int((perf_counter() - started) * 1000)

        return {
            "case_id": case["case_id"],
            "category": case["category"],
            "result": "exception",
            "scorable": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "elapsed_ms": elapsed_ms,
        }

    elapsed_ms = int((perf_counter() - started) * 1000)

    diagnostics = safe_diagnostics(response)

    citations = [
        citation.model_dump()
        for citation in response.citations
    ]

    cited_sources = {
        citation["document_id"]
        for citation in citations
    }

    required_sources = set(
        case.get("required_sources", [])
    )

    forbidden_sources = set(
        case.get("forbidden_sources", [])
    )

    status_pass = (
        response.status
        == case["expected_status"]
    )

    generation_called = diagnostics.get(
        "generation_called"
    )

    generation_pass = (
        generation_called
        == case["expected_generation_called"]
    )

    if required_sources:
        required_hits = (
            required_sources
            & cited_sources
        )

        required_source_recall = (
            len(required_hits)
            / len(required_sources)
        )

        required_sources_pass = (
            required_sources
            <= cited_sources
        )
    else:
        required_source_recall = 1.0
        required_sources_pass = True

    forbidden_hits = sorted(
        forbidden_sources
        & cited_sources
    )

    forbidden_sources_pass = (
        len(forbidden_hits) == 0
    )

    expected_gate_fragment = (
        case.get(
            "expected_gate_reason_contains"
        )
    )

    actual_gate_reason = str(
        diagnostics.get(
            "gate_reason",
            "",
        )
    )

    if expected_gate_fragment:
        gate_reason_pass = (
            expected_gate_fragment.lower()
            in actual_gate_reason.lower()
        )
    else:
        gate_reason_pass = True

    provider_unavailable = (
        response.status == "error"
        and actual_gate_reason
        in {
            "generation_service_unavailable",
            "generation_rate_limited",
        }
    )

    scorable = not provider_unavailable

    checks = {
        "status": status_pass,
        "generation_gate": generation_pass,
        "required_sources": required_sources_pass,
        "forbidden_sources": forbidden_sources_pass,
        "gate_reason": gate_reason_pass,
    }

    passed = (
        scorable
        and all(checks.values())
    )

    if provider_unavailable:
        result = "provider_unavailable"
    elif passed:
        result = "pass"
    else:
        result = "fail"

    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "user_id": case["user_id"],
        "query": case["query"],
        "expected_status": case["expected_status"],
        "actual_status": response.status,
        "result": result,
        "scorable": scorable,
        "checks": checks,
        "required_sources": sorted(
            required_sources
        ),
        "cited_sources": sorted(
            cited_sources
        ),
        "forbidden_sources": sorted(
            forbidden_sources
        ),
        "forbidden_hits": forbidden_hits,
        "required_source_recall": (
            required_source_recall
        ),
        "answer": response.answer,
        "confidence": response.confidence,
        "retrieved_chunk_count": (
            response.retrieved_chunk_count
        ),
        "diagnostics": diagnostics,
        "elapsed_ms": elapsed_ms,
    }


def percentage(numerator, denominator):
    if denominator == 0:
        return None
    return round(
        numerator / denominator * 100,
        2,
    )


def build_summary(results):
    scored = [
        item
        for item in results
        if item.get("scorable")
    ]

    provider_unavailable = [
        item
        for item in results
        if item.get("result")
        == "provider_unavailable"
    ]

    exceptions = [
        item
        for item in results
        if item.get("result")
        == "exception"
    ]

    passed = [
        item
        for item in scored
        if item["result"] == "pass"
    ]

    status_passes = sum(
        1
        for item in scored
        if item["checks"]["status"]
    )

    generation_passes = sum(
        1
        for item in scored
        if item["checks"]["generation_gate"]
    )

    forbidden_leaks = [
        item
        for item in scored
        if item.get("forbidden_hits")
    ]

    citation_cases = [
        item
        for item in scored
        if item.get("required_sources")
    ]

    refusal_cases = [
        item
        for item in scored
        if item["expected_status"]
        == "insufficient_evidence"
    ]

    refusal_passes = sum(
        1
        for item in refusal_cases
        if item["actual_status"]
        == "insufficient_evidence"
    )

    conflict_cases = [
        item
        for item in scored
        if item["expected_status"]
        == "conflicting_evidence"
    ]

    conflict_passes = sum(
        1
        for item in conflict_cases
        if item["actual_status"]
        == "conflicting_evidence"
    )

    latencies = [
        item["diagnostics"].get(
            "total_latency_ms"
        )
        for item in scored
        if item.get("diagnostics")
        and item["diagnostics"].get(
            "total_latency_ms"
        )
        is not None
    ]

    retrieval_latencies = [
        item["diagnostics"].get(
            "retrieval_latency_ms"
        )
        for item in scored
        if item.get("diagnostics")
        and item["diagnostics"].get(
            "retrieval_latency_ms"
        )
        is not None
    ]

    citation_recalls = [
        item["required_source_recall"]
        for item in citation_cases
    ]

    return {
        "total_cases": len(results),
        "scored_cases": len(scored),
        "passed_cases": len(passed),
        "failed_cases": (
            len(scored) - len(passed)
        ),
        "provider_unavailable_cases": (
            len(provider_unavailable)
        ),
        "exception_cases": len(exceptions),

        "overall_case_pass_rate_pct":
            percentage(
                len(passed),
                len(scored),
            ),

        "status_accuracy_pct":
            percentage(
                status_passes,
                len(scored),
            ),

        "generation_gate_accuracy_pct":
            percentage(
                generation_passes,
                len(scored),
            ),

        "refusal_accuracy_pct":
            percentage(
                refusal_passes,
                len(refusal_cases),
            ),

        "conflict_accuracy_pct":
            percentage(
                conflict_passes,
                len(conflict_cases),
            ),

        "mean_required_source_recall_pct":
            (
                round(
                    mean(citation_recalls)
                    * 100,
                    2,
                )
                if citation_recalls
                else None
            ),

        "forbidden_source_leak_cases":
            len(forbidden_leaks),

        "forbidden_source_leak_rate_pct":
            percentage(
                len(forbidden_leaks),
                len(scored),
            ),

        "average_retrieval_latency_ms":
            (
                round(mean(retrieval_latencies))
                if retrieval_latencies
                else None
            ),

        "average_total_latency_ms":
            (
                round(mean(latencies))
                if latencies
                else None
            ),
    }


def print_case_result(result):
    symbol = {
        "pass": "PASS",
        "fail": "FAIL",
        "provider_unavailable": "INFRA",
        "exception": "EXCEPTION",
    }.get(
        result["result"],
        result["result"].upper(),
    )

    print(
        f"{symbol:9} "
        f"{result['case_id']}"
    )

    if result["result"] == "fail":
        failed_checks = [
            name
            for name, passed
            in result["checks"].items()
            if not passed
        ]

        print(
            "          Failed checks:",
            ", ".join(failed_checks),
        )

        print(
            "          Expected:",
            result["expected_status"],
            "| Actual:",
            result["actual_status"],
        )


def main():
    cases = load_cases()

    print("=" * 76)
    print("ENGINEERING KNOWLEDGE COPILOT")
    print("STAGE 7D.3 FINAL PUBLIC GOLDEN EVALUATION")
    print("=" * 76)
    print(
        "Cases:",
        len(cases),
    )
    print()

    results = []

    for index, case in enumerate(
        cases,
        start=1,
    ):
        print(
            f"[{index}/{len(cases)}] "
            f"{case['case_id']}"
        )

        result = evaluate_case(case)
        results.append(result)

        print_case_result(result)
        print()

    summary = build_summary(results)

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "generated_at_utc": timestamp,
        "golden_dataset": str(
            GOLDEN_FILE.relative_to(ROOT)
        ),
        "summary": summary,
        "results": results,
    }

    timestamped_file = (
        RESULTS_DIR
        / f"eval_{timestamp}.json"
    )

    latest_file = (
        RESULTS_DIR
        / "latest.json"
    )

    serialized = json.dumps(
        report,
        indent=2,
    ) + "\n"

    timestamped_file.write_text(
        serialized
    )

    latest_file.write_text(
        serialized
    )

    print("=" * 76)
    print("EVALUATION SUMMARY")
    print("=" * 76)

    for key, value in summary.items():
        print(
            f"{key:38} {value}"
        )

    print()
    print(
        "Report:",
        timestamped_file,
    )

    print(
        "Latest:",
        latest_file,
    )


if __name__ == "__main__":
    main()
