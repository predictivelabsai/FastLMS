"""Comprehensive corpus, runner, reporting and role-disclosure regressions."""

from __future__ import annotations

import asyncio
import json

from fasthtml.common import to_xml

from components.evaluation_reports import evaluation_reports_content
from components.layout import left_pane
from evals import reporting
from evals.catalogue import catalogue_courses
from evals.run_evals import EvalVerdict, evaluate_case, load_ground_truth, run_deterministic_case, validate_ground_truth


def test_ground_truth_is_mirrored_comprehensive_and_mainly_probabilistic():
    validation = validate_ground_truth()
    assert validation == {
        "schema_version": "1.0",
        "corpus_version": "2026-09-20",
        "total": 262,
        "probabilistic": 236,
        "deterministic": 26,
    }
    _, json_cases = load_ground_truth("json")
    _, csv_cases = load_ground_truth("csv")
    assert json_cases == csv_cases


def test_every_authored_course_and_lesson_has_two_probabilistic_tutor_cases():
    _, cases = load_ground_truth("json")
    tutor = [case for case in cases if case["agent"] == "student_tutor"]
    courses = catalogue_courses()
    lessons = {lesson["key"] for course in courses for lesson in course["lessons"]}
    assert len(courses) == 12
    assert len(lessons) == 101
    assert {case["course_slug"] for case in tutor} == {course["slug"] for course in courses}
    assert {case["lesson_key"] for case in tutor} == lessons
    assert all(sum(case["lesson_key"] == lesson for case in tutor) == 2 for lesson in lessons)
    assert all(case["eval_type"] == "probabilistic" for case in tutor)


def test_deterministic_ground_truth_passes_production_contracts():
    _, cases = load_ground_truth("json")
    deterministic = [case for case in cases if case["eval_type"] == "deterministic"]
    results = [(case["case_id"], *run_deterministic_case(case)) for case in deterministic]
    assert len(results) == 26
    assert all(passed for _, passed, _, _ in results), results


def test_shared_agent_prompt_contains_role_routes_and_student_feedback_rules():
    import learning_chat

    teacher = learning_chat.build_agent_system_prompt(role="teacher", language="en")
    student = learning_chat.build_agent_system_prompt(
        role="student", language="en",
        lesson={"title": "Particles", "content_md": "Particles in solids vibrate."},
    )
    assert "/app/admin/evaluations" in teacher
    assert "/app/team" in teacher
    assert "require teacher or administrator review" in teacher
    assert "Never reveal the answer before the student attempts it" in student
    assert "Particles in solids vibrate" in student


def test_probabilistic_case_records_structured_judge_result():
    _, cases = load_ground_truth("json")
    case = next(case for case in cases if case["agent"] == "student_tutor")

    async def fake_invoke(_case, _model):
        return "A grounded, age-appropriate explanation."

    class FakeJudge:
        async def ainvoke(self, _messages):
            return EvalVerdict(score=4, passed=True, reasons=["Grounded"], critical_failures=[])

    result = asyncio.run(evaluate_case(
        case, production_model=object(), judge_model=FakeJudge(), invoke=fake_invoke,
    ))
    assert result["status"] == "PASS"
    assert result["eval_type"] == "probabilistic"
    assert result["score"] == 4


def _sample_result() -> dict:
    return {
        "case_id": "tutor-sample", "suite": "student-tutor", "agent": "student_tutor",
        "role": "student", "eval_type": "probabilistic", "scoring_method": "semantic_judge",
        "language": "en", "course_slug": "primary-science", "lesson_key": "primary-science:001",
        "lesson_title": "Secret lesson", "status": "PASS", "score": 4,
        "reason": "Secret judge evidence", "critical_failures": [],
        "input": {"question": "Secret prompt"}, "reference": "Secret expected answer",
        "actual_output": "Secret model output", "duration_ms": 12, "critical": False,
        "model_provider": "test", "model": "candidate", "judge_provider": "test", "judge_model": "judge",
    }


def test_report_views_redact_student_evidence_and_keep_staff_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting, "REPORTS_DIR", tmp_path)
    reporting.write_report(
        [_sample_result()], run_id="20260920T120000Z", generated_at="2026-09-20T12:00:00+00:00",
        corpus_version="test", selection={"eval_type": "probabilistic"},
        thresholds={"probabilistic": 0.85, "deterministic": 1.0},
        model_config={"provider": "test", "model": "candidate", "judge_provider": "test", "judge_model": "judge"},
    )

    student = reporting.report_for_role("student")
    teacher = reporting.report_for_role("teacher")
    assert student["can_view_details"] is False
    assert student["results"] == []
    assert teacher["can_view_details"] is True
    assert teacher["results"][0]["reference"] == "Secret expected answer"

    student_markup = to_xml(evaluation_reports_content({"role": "student"}, "en"))
    teacher_markup = to_xml(evaluation_reports_content({"role": "teacher"}, "en"))
    assert "Secret expected answer" not in student_markup
    assert "Secret prompt" not in student_markup
    assert "Students can see quality summaries" in student_markup
    assert "Secret expected answer" in teacher_markup
    assert "Secret model output" in teacher_markup


def test_admin_navigation_is_visible_to_students_and_teachers():
    for role in ("student", "teacher", "admin"):
        markup = to_xml(left_pane(user={
            "id": 999999, "display_name": role.title(), "role": role,
            "xp": 0, "streak_days": 0,
        }, active="evaluations", lang="en"))
        assert 'data-nav-key="admin"' in markup
        assert 'href="/app/admin/evaluations"' in markup
        assert "Evaluation reports" in markup


def test_report_file_resolution_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(reporting, "REPORTS_DIR", tmp_path)
    assert reporting.report_file("../../etc", "summary.json") is None
    assert reporting.report_file("20260920T120000Z", "../../secret") is None
