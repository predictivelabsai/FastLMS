"""Regression tests for the student-only evaluation harness."""

import json

from evals import student_learning as evaluations


def test_local_student_learning_ground_truth_and_contracts_pass():
    checks = evaluations.run_local_checks()
    assert checks
    assert all(check["passed"] for check in checks), checks


def test_ground_truth_has_english_and_estonian_explanation_cases():
    cases = json.loads((evaluations.GROUND_TRUTH / "tutor_explanations.json").read_text(encoding="utf-8"))["cases"]
    assert {case["language"] for case in cases} == {"en", "et"}
    assert all(case["must_include"] and case["must_not_claim"] for case in cases)


def test_judge_prompt_resists_candidate_instruction_injection():
    prompt = evaluations.JUDGE_SYSTEM_PROMPT.lower()
    assert "untrusted data" in prompt
    assert "never as instructions" in prompt


def test_report_can_run_without_network_or_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = evaluations.build_report("https://example.invalid/api/v1", include_live=False, include_judge=True)
    assert report["summary"]["failed"] == 0
    assert report["summary"]["skipped"] == 5
