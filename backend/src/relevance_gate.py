import re
from dataclasses import dataclass
from typing import Any


STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "what", "which", "who", "why", "how",
    "and", "or", "to", "of", "for", "in", "on",
    "at", "by", "with", "from", "this", "that",
    "did", "does", "do", "will", "would", "could",
    "per",
}


SYNONYMS = {
    "overheat": {"thermal", "heat", "overheating", "shutdown"},
    "overheated": {"thermal", "heat", "overheating", "shutdown"},
    "failure": {"failure", "shutdown", "issue"},
    "failed": {"failure", "shutdown", "issue"},
    "cause": {"cause", "caused", "root"},
    "caused": {"cause", "caused", "root"},
    "fix": {"corrective", "action", "revision", "revised"},
    "corrective": {"corrective", "action", "revision", "revised"},
    "economics": {"economics", "cost", "margin", "price"},
}


@dataclass
class EvidenceGateResult:
    accepted: bool
    reason: str
    top_semantic_score: float
    query_coverage: float


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z0-9]+", text)
        if token.lower() not in STOPWORDS
    }


def _evidence_text(results: list[dict[str, Any]]) -> str:
    parts = []

    for result in results:
        parts.extend([
            str(result.get("title", "")),
            str(result.get("text", "")),
            str(result.get("source_type", "")),
        ])

    return " ".join(parts).lower()


def _concept_matches(
    query_term: str,
    evidence_tokens: set[str],
) -> bool:

    if query_term in evidence_tokens:
        return True

    alternatives = SYNONYMS.get(query_term, set())

    return bool(alternatives & evidence_tokens)


PROGRAM_ALIASES = {
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


def evaluate_evidence(
    query: str,
    results: list[dict[str, Any]],
    semantic_floor: float = 0.60,
    minimum_query_coverage: float = 0.30,
) -> EvidenceGateResult:

    if not results:
        return EvidenceGateResult(
            accepted=False,
            reason="no_candidates",
            top_semantic_score=0.0,
            query_coverage=0.0,
        )

    top_score = max(
        float(result.get("semantic_score", 0.0))
        for result in results
    )

    if top_score < semantic_floor:
        return EvidenceGateResult(
            accepted=False,
            reason="semantic_score_below_floor",
            top_semantic_score=top_score,
            query_coverage=0.0,
        )

    # Explicit program anchoring.
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

    combined_evidence = _evidence_text(results)
    evidence_tokens = _tokens(combined_evidence)
    query_tokens = _tokens(query)

    # Product-specific answerability anchors.
    # These are deliberately conservative for the MVP.

    if {"supplier", "vendor"} & query_tokens:
        supplier_terms = {
            "supplier",
            "vendor",
            "sourcing",
            "source",
        }

        if not supplier_terms & evidence_tokens:
            return EvidenceGateResult(
                accepted=False,
                reason="supplier_evidence_missing",
                top_semantic_score=top_score,
                query_coverage=0.0,
            )

    if {
        "cost",
        "economics",
        "price",
        "margin",
    } & query_tokens:

        finance_terms = {
            "cost",
            "economics",
            "price",
            "margin",
            "bom",
        }

        if not finance_terms & evidence_tokens:
            return EvidenceGateResult(
                accepted=False,
                reason="financial_evidence_missing",
                top_semantic_score=top_score,
                query_coverage=0.0,
            )

    requested_years = set(
        re.findall(r"\b20\d{2}\b", query)
    )

    for year in requested_years:
        if year not in combined_evidence:
            return EvidenceGateResult(
                accepted=False,
                reason=f"requested_year_missing:{year}",
                top_semantic_score=top_score,
                query_coverage=0.0,
            )

    meaningful_terms = {
        token
        for token in query_tokens
        if not token.isdigit()
    }

    if not meaningful_terms:
        coverage = 1.0

    else:
        matched = sum(
            1
            for term in meaningful_terms
            if _concept_matches(
                term,
                evidence_tokens,
            )
        )

        coverage = matched / len(meaningful_terms)

    if coverage < minimum_query_coverage:
        return EvidenceGateResult(
            accepted=False,
            reason="insufficient_query_concept_coverage",
            top_semantic_score=top_score,
            query_coverage=coverage,
        )

    return EvidenceGateResult(
        accepted=True,
        reason="accepted",
        top_semantic_score=top_score,
        query_coverage=coverage,
    )
