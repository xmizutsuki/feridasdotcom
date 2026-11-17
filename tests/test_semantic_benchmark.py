"""Synthetic semantic-contract benchmark: no real patient, no model metrics.

This checks deterministic policy and schema coverage against developer-authored
labels. It is NOT a clinical benchmark or a measure of LLM accuracy.
"""
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.semantic_audit import SemanticAuditDraft, evaluate_verdicts

DATA = json.loads(
    (Path(__file__).resolve().parents[1] / "benchmarks" / "semantic_contract_cases.json").read_text(encoding="utf-8")
)
CASES = DATA["cases"]

def semantic_case(case):
    data = {
        "hypotheses": [{
            "hypothesis_index": 0,
            "verdicts": [] if case["omit_citation"] else [{
                "citation_id": "citation-synthetic-001",
                "verdict": case["verdict"],
                "rationale": "This is a strictly synthetic citation check, not medical evidence.",
                "population_applicable": case["population"],
                "contraindication_conflict": case["contraindication_conflict"],
            }],
            "unsafe_or_overconfident_language": case["unsafe_or_overconfident_language"],
            "unsupported_clinical_assertions": (["Synthetic ungrounded assertion"]
                                                 if case["unsupported_clinical_assertion"] else []),
            "missing_critical_clinical_information": (["Missing synthetic observation"]
                                                      if case["missing_critical_information"] else []),
        }],
        "limitations": ["No clinical validation; all facts are synthetic."]
    }
    return SemanticAuditDraft.model_validate(data)

@pytest.mark.parametrize("case", CASES, ids=[item["id"] for item in CASES])
def test_synthetic_semantic_safety_contract(case):
    hypotheses=[{"citation_ids":["citation-synthetic-001"]}]
    if case["omit_citation"]:
        # Empty verdict list violates the strict schema, a fail-closed outcome.
        with pytest.raises(ValidationError):
            semantic_case(case)
    else:
        audit = semantic_case(case)
        issues = evaluate_verdicts(hypotheses, audit)
        actual = "blocked" if any(issues) else "review_required"
        assert actual == case["expected_status"]
        assert audit.hypotheses[0].hypothesis_index == 0

def test_unexpected_extra_citation_is_rejected():
    audit=SemanticAuditDraft.model_validate({
        "hypotheses":[{
            "hypothesis_index":0,
            "verdicts":[{
                "citation_id":"not-in-original",
                "verdict":"supported",
                "rationale":"A fabricated citation is an invalid source match.",
                "population_applicable":"yes",
                "contraindication_conflict":False,
            }],
            "unsafe_or_overconfident_language":False,
        }],
        "limitations":["Synthetic data"],
    })
    with pytest.raises(ValueError, match="omitiu ou inventou"):
        evaluate_verdicts([{"citation_ids":["citation-synthetic-001"]}],audit)

def test_missing_hypothesis_is_rejected():
    audit=SemanticAuditDraft.model_validate({
        "hypotheses":[{
            "hypothesis_index":1,
            "verdicts":[{
                "citation_id":"citation-synthetic-001",
                "verdict":"supported",
                "rationale":"Synthetic verification is not patient applicability.",
                "population_applicable":"yes",
                "contraindication_conflict":False,
            }],
            "unsafe_or_overconfident_language":False,
        }],
        "limitations":["Synthetic data"],
    })
    with pytest.raises(ValueError, match="omitiu hipóteses"):
        evaluate_verdicts([{"citation_ids":["citation-synthetic-001"]}],audit)
