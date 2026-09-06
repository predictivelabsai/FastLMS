"""RBAC and adaptive-learning decision regressions."""

from pathlib import Path

from arts_catalog import ART_COURSES
import db


def test_only_named_account_can_be_administrator():
    assert db.role_for_email("kaljuvee@gmail.com") == "admin"
    assert db.role_for_email("KALJUVEE@GMAIL.COM") == "admin"
    assert db.role_for_email("teacher@example.com", "teacher") == "teacher"
    assert db.role_for_email("someone@example.com", "admin") == "student"


def test_default_courses_are_admin_editable_but_teacher_clone_only():
    admin = {"id": 1, "role": "admin"}
    teacher = {"id": 2, "role": "teacher"}
    own = {"id": 10, "instructor_id": 2, "is_default": False}
    admin_default = {"id": 11, "instructor_id": 1, "is_default": True}
    legacy_default = {"id": 12, "instructor_id": 2, "is_default": True}
    assert db.course_is_editable_by(admin, admin_default)
    assert db.course_is_editable_by(teacher, own)
    assert not db.course_is_editable_by(teacher, admin_default)
    assert not db.course_is_editable_by(teacher, legacy_default)
    assert not db.course_is_editable_by({"id": 3, "role": "student"}, own)


def test_default_catalogue_migration_and_clone_engine_are_complete():
    assert "ADD COLUMN IF NOT EXISTS is_default" in db.SCHEMA_SQL
    assert "'art-history'" in db.SCHEMA_SQL
    source = Path("db.py").read_text(encoding="utf-8")
    for authored_entity in ("modules", "lessons", "quizzes", "quiz_questions", "content_translations"):
        assert authored_entity in source[source.index("def clone_course"):]
    assert "is_default = true AND is_published = true" in source[source.index("def can_clone_course"):]


def test_teacher_reports_are_scoped_to_their_own_assignments():
    source = Path("db.py").read_text(encoding="utf-8")
    report_source = source[source.index("def learning_time_report"):]
    assert "ca.assigned_by = :assigned_by" in report_source
    main_source = Path("main.py").read_text(encoding="utf-8")
    route_source = main_source[main_source.index("def learning_reports"):]
    assert 'assigned_by=None if user["role"] == "admin" else user["id"]' in route_source


def test_adaptive_support_is_bounded_to_one_level():
    decision = db.adaptive_transition(3, 1, 40)
    assert decision == {
        "difficulty_level": 2,
        "consecutive_high": 0,
        "consecutive_low": 1,
        "recommendation": "remedial",
    }
    assert db.adaptive_transition(1, 0, 10)["difficulty_level"] == 1


def test_adaptive_challenge_requires_two_high_scores():
    first = db.adaptive_transition(2, 0, 90)
    assert first["difficulty_level"] == 2
    assert first["recommendation"] == "hold"
    second = db.adaptive_transition(2, first["consecutive_high"], 92)
    assert second["difficulty_level"] == 3
    assert second["recommendation"] == "extension"
    assert db.adaptive_transition(3, 1, 100)["difficulty_level"] == 3


def test_midrange_score_holds_and_resets_streak():
    decision = db.adaptive_transition(2, 1, 75)
    assert decision["difficulty_level"] == 2
    assert decision["consecutive_high"] == 0
    assert decision["recommendation"] == "hold"


def test_activity_client_uses_approved_limits():
    script = Path("static/activity.js").read_text(encoding="utf-8")
    assert "90000" in script
    assert "30000" in script
    assert "document.hidden" in script
    assert "Math.min(30" in script


def test_generated_question_variants_are_complete_in_every_language():
    lessons = {code: {"title": title} for code, title in {
        "en": "Fractions", "et": "Murrud", "lt": "Trupmenos", "es": "Fracciones",
    }.items()}
    easy = db._question_draft_payload(lessons, 1)
    hard = db._question_draft_payload(lessons, 3)
    assert easy["en"]["question_text"] != hard["en"]["question_text"]
    for payload in (easy, hard):
        assert set(payload) == {"en", "et", "lt", "es"}
        for variant in payload.values():
            assert variant["correct_answer"] in variant["options"]


def test_art_and_music_catalogue_is_principles_first():
    assert {course["slug"] for course in ART_COURSES} == {
        "art-history", "music-history", "art-principles", "music-principles",
    }
    assert all(course["is_published"] for course in ART_COURSES)
    art = next(course for course in ART_COURSES if course["slug"] == "art-principles")
    music = next(course for course in ART_COURSES if course["slug"] == "music-principles")
    assert art["title"] == "Art"
    assert music["title"] == "Music"
    assert "no drawing" in art["description"].lower()
    assert "without requiring singing or an instrument" in music["description"].lower()
