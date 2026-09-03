"""RBAC and adaptive-learning decision regressions."""

from pathlib import Path

import db


def test_only_named_account_can_be_administrator():
    assert db.role_for_email("kaljuvee@gmail.com") == "admin"
    assert db.role_for_email("KALJUVEE@GMAIL.COM") == "admin"
    assert db.role_for_email("teacher@example.com", "teacher") == "teacher"
    assert db.role_for_email("someone@example.com", "admin") == "student"


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
        "en": "Fractions", "et": "Murrud", "lt": "Trupmenos",
    }.items()}
    easy = db._question_draft_payload(lessons, 1)
    hard = db._question_draft_payload(lessons, 3)
    assert easy["en"]["question_text"] != hard["en"]["question_text"]
    for payload in (easy, hard):
        assert set(payload) == {"en", "et", "lt"}
        for variant in payload.values():
            assert variant["correct_answer"] in variant["options"]
