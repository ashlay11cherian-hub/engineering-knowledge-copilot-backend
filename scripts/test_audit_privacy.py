import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AUDIT_FILE = (
    ROOT
    / "backend"
    / "runtime"
    / "audit_log.jsonl"
)

QUARANTINE_FILE = (
    ROOT
    / "backend"
    / "runtime"
    / "ingestion_quarantine.jsonl"
)

FORBIDDEN_KEYS = {
    "query",
    "prompt",
    "raw_prompt",
    "answer",
    "generated_answer",
    "content",
    "document_content",
    "api_key",
    "gemini_api_key",
    "access_token",
    "refresh_token",
    "oauth_token",
}

SECRET_VALUES = [
    value
    for value in [
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GOOGLE_CLIENT_SECRET"),
        os.getenv("GOOGLE_CLIENT_ID"),
    ]
    if value
]


def inspect_jsonl(path: Path):
    violations = []

    if not path.exists():
        return violations, 0

    count = 0

    for line_number, line in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        count += 1

        try:
            record = json.loads(line)

        except json.JSONDecodeError:
            violations.append(
                (
                    line_number,
                    "invalid_json",
                )
            )
            continue

        normalized_keys = {
            str(key).lower()
            for key in record.keys()
        }

        leaked_keys = (
            normalized_keys
            & FORBIDDEN_KEYS
        )

        for key in sorted(leaked_keys):
            violations.append(
                (
                    line_number,
                    f"forbidden_key:{key}",
                )
            )

        serialized = json.dumps(
            record
        )

        for secret in SECRET_VALUES:
            if secret and secret in serialized:
                violations.append(
                    (
                        line_number,
                        "secret_value_detected",
                    )
                )

    return violations, count


def main():
    print("=" * 72)
    print("STAGE 6D — AUDIT & PRIVACY LEAKAGE TEST")
    print("=" * 72)

    total_violations = []

    for label, path in [
        ("AUDIT LOG", AUDIT_FILE),
        ("INGESTION QUARANTINE", QUARANTINE_FILE),
    ]:
        print()
        print(label)
        print("-" * 72)

        violations, count = inspect_jsonl(
            path
        )

        print("File:", path)
        print("Records checked:", count)

        if not path.exists():
            print(
                "Status: NOT PRESENT "
                "(nothing to inspect)"
            )

        elif violations:
            print("Status: FAIL")

            for violation in violations:
                print(
                    "Line",
                    violation[0],
                    violation[1],
                )

            total_violations.extend(
                (
                    label,
                    *violation,
                )
                for violation in violations
            )

        else:
            print("Status: PASS")
            print(
                "No raw prompt/answer/content/"
                "credential fields detected."
            )

    print()
    print("=" * 72)

    if total_violations:
        print("OVERALL RESULT: FAIL")
        print(
            "Potential sensitive-data logging "
            "requires investigation."
        )
    else:
        print("OVERALL RESULT: PASS")
        print(
            "Operational logs contain metadata "
            "without raw prompt, answer, document "
            "content, or credential fields."
        )

    print("=" * 72)


if __name__ == "__main__":
    main()
