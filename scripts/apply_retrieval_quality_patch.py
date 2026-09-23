from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]

VECTOR_PATH = ROOT / "backend" / "src" / "vector_index.py"
GATE_PATH = ROOT / "backend" / "src" / "relevance_gate.py"


def backup(path: Path):
    backup_path = path.with_suffix(
        path.suffix + ".pre_4j3e"
    )

    if not backup_path.exists():
        shutil.copy2(
            path,
            backup_path,
        )

        print(
            "Backup:",
            backup_path,
        )


def patch_vector_index():
    text = VECTOR_PATH.read_text()

    old = '''    # Relevance remains primary. Authority breaks close-score ties.
    scored_results.sort(
        key=lambda result: (
            result["semantic_score"],
            result.get("authority_rank", 0),
            result.get("document_status") == "current",
        ),
        reverse=True,
    )

    return scored_results[:top_k]
'''

    new = '''    # Second-stage reranking.
    #
    # Semantic relevance remains the dominant signal,
    # while current/high-authority records receive a
    # bounded adjustment. Superseded records are
    # deliberately demoted for current-state questions.
    for result in scored_results:
        authority_rank = int(
            result.get("authority_rank", 0)
            or 0
        )

        authority_rank = max(
            0,
            min(
                100,
                authority_rank,
            ),
        )

        authority_bonus = (
            0.02
            * (
                authority_rank
                / 100.0
            )
        )

        status_adjustment = (
            0.02
            if result.get(
                "document_status"
            ) == "current"
            else -0.06
        )

        result["ranking_score"] = round(
            result["semantic_score"]
            + authority_bonus
            + status_adjustment,
            4,
        )

    scored_results.sort(
        key=lambda result: (
            result["ranking_score"],
            result["semantic_score"],
        ),
        reverse=True,
    )

    return scored_results[:top_k]
'''

    if old not in text:
        raise RuntimeError(
            "Could not find expected vector ranking block. "
            "No changes were made."
        )

    VECTOR_PATH.write_text(
        text.replace(
            old,
            new,
            1,
        )
    )

    print(
        "Patched:",
        VECTOR_PATH,
    )


def patch_relevance_gate():
    text = GATE_PATH.read_text()

    helper_marker = (
        "PROGRAM_ALIASES = {"
    )

    if helper_marker not in text:
        marker = (
            "def evaluate_evidence("
        )

        index = text.find(marker)

        if index == -1:
            raise RuntimeError(
                "Could not locate evaluate_evidence()."
            )

        helper = '''PROGRAM_ALIASES = {
    "GEN3-WLC": (
        "gen-3",
        "gen3",
    ),
    "TELEMATICS-X": (
        "telematics-x",
        "telematics x",
    ),
    "WEARABLE-ORBIT": (
        "orbit wearable",
        "orbit",
    ),
    "SMARTGLASS-NOVA": (
        "nova smart glasses",
        "nova",
    ),
    "EARBUDS-PULSE": (
        "pulse earbuds",
        "pulse",
    ),
    "SMARTHOME-HALO": (
        "halo smart home",
        "halo",
    ),
}


def _explicit_program_from_query(
    query: str,
) -> str | None:
    """Return an explicitly named synthetic product program."""

    normalized = (
        query
        .casefold()
        .replace("–", "-")
        .replace("—", "-")
    )

    for program_id, aliases in PROGRAM_ALIASES.items():
        if any(
            alias in normalized
            for alias in aliases
        ):
            return program_id

    return None


'''

        text = (
            text[:index]
            + helper
            + text[index:]
        )

    scope_marker = (
        'explicit_program_evidence_missing'
    )

    if scope_marker not in text:
        needle = (
            "    combined_evidence = "
            "_evidence_text(results)\n"
        )

        if needle not in text:
            raise RuntimeError(
                "Could not locate evidence-text stage."
            )

        scope_check = '''    # Explicit program anchoring.
    #
    # If a query names a specific product/program, at least
    # one authorized retrieved result must belong to that
    # program. Similar evidence from another authorized
    # program must not make the query answerable.
    explicit_program = (
        _explicit_program_from_query(
            query
        )
    )

    if explicit_program is not None:
        result_programs = {
            result.get("program_id")
            for result in results
        }

        if (
            explicit_program
            not in result_programs
        ):
            return EvidenceGateResult(
                accepted=False,
                reason=(
                    "explicit_program_evidence_missing:"
                    f"{explicit_program}"
                ),
                top_semantic_score=top_score,
                query_coverage=0.0,
            )

'''

        text = text.replace(
            needle,
            scope_check + needle,
            1,
        )

    GATE_PATH.write_text(text)

    print(
        "Patched:",
        GATE_PATH,
    )


def main():
    backup(VECTOR_PATH)
    backup(GATE_PATH)

    patch_vector_index()
    patch_relevance_gate()

    print()
    print(
        "SUCCESS: Stage 4J.3E retrieval-quality "
        "patch applied."
    )


if __name__ == "__main__":
    main()
