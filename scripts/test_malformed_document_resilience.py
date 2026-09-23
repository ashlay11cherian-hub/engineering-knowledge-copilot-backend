import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.src.chunking import create_document_chunks


# ---------------------------------------------------------
# Load the REAL existing corpus validator without changing it
# ---------------------------------------------------------

generator_path = ROOT / "scripts" / "generate_expanded_corpus.py"

spec = importlib.util.spec_from_file_location(
    "generate_expanded_corpus",
    generator_path,
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

validate_document = module.validate_document


# ---------------------------------------------------------
# Known-good synthetic baseline
# ---------------------------------------------------------

BASE_DOCUMENT = {
    "document_id": "ROBUST-001",
    "title": "Synthetic Robustness Test Document",
    "source_type": "validation_report",
    "department": "engineering",
    "classification": "internal",
    "allowed_roles": [
        "engineer",
        "program_manager",
    ],
    "revision": "1.0",
    "content": (
        "Synthetic engineering content used only for malformed "
        "document resilience testing."
    ),
    "program_id": "GEN3-WLC",
    "authority_rank": 80,
    "document_status": "current",
}


def validator_result(document):
    try:
        validate_document(copy.deepcopy(document))
        return "ACCEPTED", None
    except Exception as exc:
        return "REJECTED", f"{type(exc).__name__}: {exc}"


def chunker_result(documents):
    try:
        chunks = create_document_chunks(
            copy.deepcopy(documents),
            chunk_size_words=120,
            overlap_words=25,
        )

        return (
            "ACCEPTED",
            len(chunks),
            [
                chunk.get("chunk_id")
                for chunk in chunks
            ],
            None,
        )

    except Exception as exc:
        return (
            "REJECTED",
            0,
            [],
            f"{type(exc).__name__}: {exc}",
        )


def build_cases():
    cases = {}

    good = copy.deepcopy(BASE_DOCUMENT)
    cases["VALID_BASELINE"] = good

    missing_id = copy.deepcopy(BASE_DOCUMENT)
    del missing_id["document_id"]
    cases["MISSING_DOCUMENT_ID"] = missing_id

    empty_id = copy.deepcopy(BASE_DOCUMENT)
    empty_id["document_id"] = ""
    cases["EMPTY_DOCUMENT_ID"] = empty_id

    bad_rank = copy.deepcopy(BASE_DOCUMENT)
    bad_rank["authority_rank"] = "VERY_HIGH"
    cases["INVALID_AUTHORITY_TYPE"] = bad_rank

    bad_classification = copy.deepcopy(BASE_DOCUMENT)
    bad_classification["classification"] = "top_secret"
    cases["INVALID_CLASSIFICATION"] = bad_classification

    empty_content = copy.deepcopy(BASE_DOCUMENT)
    empty_content["content"] = ""
    cases["EMPTY_CONTENT"] = empty_content

    bad_roles = copy.deepcopy(BASE_DOCUMENT)
    bad_roles["allowed_roles"] = "program_manager"
    cases["INVALID_ALLOWED_ROLES_TYPE"] = bad_roles

    missing_program = copy.deepcopy(BASE_DOCUMENT)
    del missing_program["program_id"]
    cases["MISSING_PROGRAM_ID"] = missing_program

    return cases


def main():
    print("=" * 76)
    print("STAGE 6C.2 — MALFORMED DOCUMENT RESILIENCE DIAGNOSTIC")
    print("=" * 76)

    print()
    print(
        "NOTE: This test uses in-memory synthetic fixtures only."
    )
    print(
        "Google Drive and the existing runtime index are not modified."
    )

    cases = build_cases()

    unexpected_accepts = []

    for name, document in cases.items():
        print()
        print("-" * 76)
        print(name)
        print("-" * 76)

        validation_status, validation_error = (
            validator_result(document)
        )

        chunk_status, chunk_count, chunk_ids, chunk_error = (
            chunker_result([document])
        )

        print("Validator:", validation_status)

        if validation_error:
            print("Validator detail:", validation_error)

        print("Chunker:", chunk_status)

        if chunk_error:
            print("Chunker detail:", chunk_error)
        else:
            print("Chunks produced:", chunk_count)
            print("Chunk IDs:", chunk_ids)

        if (
            name != "VALID_BASELINE"
            and validation_status == "ACCEPTED"
        ):
            unexpected_accepts.append(name)

    # -----------------------------------------------------
    # Duplicate-ID test
    # -----------------------------------------------------

    print()
    print("=" * 76)
    print("DUPLICATE DOCUMENT-ID TEST")
    print("=" * 76)

    first = copy.deepcopy(BASE_DOCUMENT)

    second = copy.deepcopy(BASE_DOCUMENT)
    second["title"] = "Duplicate ID — Different Document"
    second["content"] = (
        "This second document deliberately reuses ROBUST-001."
    )

    first_validation = validator_result(first)
    second_validation = validator_result(second)

    print(
        "Document 1 validator:",
        first_validation[0],
    )

    print(
        "Document 2 validator:",
        second_validation[0],
    )

    (
        duplicate_chunk_status,
        duplicate_chunk_count,
        duplicate_chunk_ids,
        duplicate_chunk_error,
    ) = chunker_result([first, second])

    print(
        "Chunker:",
        duplicate_chunk_status,
    )

    if duplicate_chunk_error:
        print(
            "Chunker detail:",
            duplicate_chunk_error,
        )
    else:
        print(
            "Chunks produced:",
            duplicate_chunk_count,
        )

        print(
            "Chunk IDs:",
            duplicate_chunk_ids,
        )

        duplicate_chunk_ids_found = (
            len(duplicate_chunk_ids)
            != len(set(duplicate_chunk_ids))
        )

        print(
            "Duplicate chunk IDs detected:",
            duplicate_chunk_ids_found,
        )

    # -----------------------------------------------------
    # Malformed JSON parsing test
    # -----------------------------------------------------

    print()
    print("=" * 76)
    print("MALFORMED JSON PARSING TEST")
    print("=" * 76)

    malformed_json = """
    {
        "document_id": "BROKEN-JSON-001",
        "title": "Broken JSON",
        "content": "Missing closing structure"
    """

    try:
        json.loads(malformed_json)

        print("Malformed JSON rejected: FAIL")
        malformed_json_rejected = False

    except json.JSONDecodeError as exc:

        print("Malformed JSON rejected: PASS")
        print(
            "Parser detail:",
            type(exc).__name__,
        )

        malformed_json_rejected = True

    print()
    print("=" * 76)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 76)

    if unexpected_accepts:
        print(
            "Malformed records accepted by current validator:"
        )

        for case in unexpected_accepts:
            print(" -", case)

    else:
        print(
            "No malformed structured records were accepted "
            "by the validator."
        )

    print(
        "Malformed JSON parser rejection:",
        "PASS"
        if malformed_json_rejected
        else "FAIL",
    )

    print()
    print(
        "This is a diagnostic test. Acceptance of malformed "
        "structured records indicates a validation gap; it does "
        "not mean the test script itself failed."
    )

    print("=" * 76)


if __name__ == "__main__":
    main()
