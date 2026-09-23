from backend.src.relevance_gate import evaluate_evidence


def result(
    document_id: str,
    title: str,
    text: str,
    score: float,
):
    return {
        "document_id": document_id,
        "title": title,
        "text": text,
        "source_type": "test",
        "semantic_score": score,
    }


def test_valid_root_cause_evidence_is_accepted():
    results = [
        result(
            "VAL-037",
            "Wireless Charger Thermal Validation Report",
            (
                "Thermal shutdown occurred due to coil "
                "misalignment. Revised coil geometry was "
                "recommended as corrective action."
            ),
            0.8249,
        )
    ]

    gate = evaluate_evidence(
        (
            "What caused the wireless charger thermal failure "
            "and what corrective action was approved?"
        ),
        results,
    )

    assert gate.accepted is True


def test_cost_question_rejects_nonfinancial_evidence():
    results = [
        result(
            "JIRA-889",
            "Thermal Shutdown Investigation",
            "Tolerance stack-up caused coil misalignment.",
            0.6896,
        )
    ]

    gate = evaluate_evidence(
        "What is the manufacturing cost per unit?",
        results,
    )

    assert gate.accepted is False
    assert gate.reason == "financial_evidence_missing"


def test_supplier_question_requires_supplier_evidence():
    results = [
        result(
            "ECR-238",
            "Approved Coil Geometry Revision",
            "Revised coil geometry was approved.",
            0.7399,
        )
    ]

    gate = evaluate_evidence(
        (
            "Which supplier will manufacture the redesigned "
            "coil in 2027?"
        ),
        results,
    )

    assert gate.accepted is False


def test_low_semantic_score_is_rejected():
    results = [
        result(
            "X",
            "Unrelated document",
            "Unrelated information.",
            0.42,
        )
    ]

    gate = evaluate_evidence(
        "Why did the charger overheat?",
        results,
    )

    assert gate.accepted is False
    assert gate.reason == "semantic_score_below_floor"
