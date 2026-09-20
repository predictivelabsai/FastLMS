"""Disposable-PostgreSQL verification for the complete science pathway."""

import os
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from fasthtml.common import to_xml


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_INTEGRATION") != "1",
    reason="set RUN_POSTGRES_INTEGRATION=1 with a disposable DB_URL",
)


def test_science_seed_is_idempotent_and_every_lesson_has_both_modes():
    import db
    from science_catalog import CATALOG

    db.bootstrap_schema()
    db.bootstrap_schema()
    slugs = [course["slug"] for course in CATALOG]
    expected = {
        (course["slug"], lesson["title"]["en"])
        for course in CATALOG
        for module in course["modules"]
        for lesson in module["lessons"]
    }

    with db.begin() as conn:
        lessons = conn.execute(sa.text(f"""
            SELECT c.slug, l.id, l.title,
                   count(DISTINCT le.exercise_id) AS exercises,
                   count(DISTINCT qq.id) AS questions
            FROM {db.S}.courses c
            JOIN {db.S}.modules m ON m.course_id=c.id
            JOIN {db.S}.lessons l ON l.module_id=m.id
            LEFT JOIN {db.S}.lesson_exercises le ON le.lesson_id=l.id
            LEFT JOIN {db.S}.quizzes q ON q.lesson_id=l.id
            LEFT JOIN {db.S}.quiz_questions qq ON qq.quiz_id=q.id
            WHERE c.slug = ANY(:slugs)
            GROUP BY c.slug, l.id, l.title
        """), {"slugs": slugs}).mappings().all()
        canonical = [row for row in lessons if (row["slug"], row["title"]) in expected]
        assert len(canonical) == 28
        assert all(int(row["exercises"]) >= 1 for row in canonical)
        assert all(int(row["questions"]) >= 1 for row in canonical)

        course_id = conn.execute(sa.text(f"""
            SELECT id FROM {db.S}.courses WHERE slug='primary-science'
        """)).scalar_one()
        conn.execute(sa.text(f"""
            DELETE FROM {db.S}.course_learning_settings WHERE course_id=:course
        """), {"course": course_id})
        settings = db.get_course_learning_settings(conn, course_id)
        assert settings["question_source"] == "llm_reviewed"

        first = next(row for row in canonical if row["slug"] == "primary-science")
        quiz = db.get_quiz_for_lesson(conn, first["id"])
        conn.execute(sa.text(f"""
            DELETE FROM {db.S}.quiz_questions
            WHERE quiz_id=:quiz AND source_type='llm'
              AND question_text='Generated test question?'
        """), {"quiz": quiz["id"]})
        authored = db.get_quiz_questions(conn, quiz["id"])
        assert authored and {row["source_type"] for row in authored} == {"authored"}

        generated_id = conn.execute(sa.text(f"""
            INSERT INTO {db.S}.quiz_questions
                (quiz_id, question_text, options, correct_answer, explanation,
                 order_idx, difficulty_level, source_type)
            VALUES (:quiz, 'Generated test question?', '["Yes","No","Maybe"]'::jsonb,
                    'Yes', 'This approved generated answer is correct.', 99, 2, 'llm')
            RETURNING id
        """), {"quiz": quiz["id"]}).scalar_one()
        selected = db.get_quiz_questions(conn, quiz["id"])
        assert [row["id"] for row in selected] == [generated_id]

        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.course_learning_settings (course_id, question_source)
            VALUES (:course, 'fixed')
            ON CONFLICT (course_id) DO UPDATE SET question_source='fixed'
        """), {"course": course_id})
        fixed = db.get_quiz_questions(conn, quiz["id"])
        assert fixed and {row["source_type"] for row in fixed} == {"authored"}

        public_exercise = db.get_lesson_exercises(conn, first["id"])[0]
        assert "answer_payload" not in public_exercise
        protected = db.get_interactive_exercise(
            conn, public_exercise["id"], include_answer=True
        )
        assert protected["answer_payload"]


def test_every_science_lesson_renders_chat_practice_and_classic_quiz(monkeypatch):
    import db
    import learning_chat
    import main
    from science_catalog import CATALOG

    db.bootstrap_schema()
    slugs = [course["slug"] for course in CATALOG]
    with db.begin() as conn:
        user_id = conn.execute(sa.text(f"""
            INSERT INTO {db.S}.users (email, password_hash, display_name, role)
            VALUES ('science-integration@example.test', 'unused', 'Science Learner', 'student')
            ON CONFLICT (email) DO UPDATE SET display_name=EXCLUDED.display_name
            RETURNING id
        """)).scalar_one()
        lessons = conn.execute(sa.text(f"""
            SELECT c.slug, l.id, q.id AS quiz_id
            FROM {db.S}.courses c
            JOIN {db.S}.modules m ON m.course_id=c.id
            JOIN {db.S}.lessons l ON l.module_id=m.id
            JOIN {db.S}.quizzes q ON q.lesson_id=l.id
            WHERE c.slug = ANY(:slugs)
            ORDER BY c.slug, m.order_idx, l.order_idx
        """), {"slugs": slugs}).mappings().all()
        assert len(lessons) == 28
        for lesson in lessons:
            opening = learning_chat.initial_response(
                conn, user_id, "en", lesson_id=lesson["id"]
            )
            values = {choice["value"] for choice in opening["context"]["choices"]}
            assert {"practice", "quiz"} <= values
            assert opening["context"]["lesson_id"] == lesson["id"]
            assert opening["context"]["quiz_id"] == lesson["quiz_id"]

    user = {
        "id": user_id, "email": "science-integration@example.test",
        "display_name": "Science Learner", "role": "student",
        "xp": 0, "level": "Novice", "streak_days": 0,
    }
    request = SimpleNamespace(
        query_params={}, session={"user_id": user_id}, cookies={}, headers={}
    )
    monkeypatch.setattr(main, "_require_login", lambda _request: (user, None))

    for slug in slugs:
        course_markup = to_xml(main.course_detail(request, slug))
        assert "Chat mode" in course_markup
        assert "Classic mode" in course_markup
        assert "/app/chat/new?lesson_id=" in course_markup

    for lesson in lessons:
        classic_markup = to_xml(main.lesson_page(request, lesson["id"]))
        assert "Chat mode" in classic_markup
        assert "Classic mode" in classic_markup
        assert f"/app/chat/new?lesson_id={lesson['id']}" in classic_markup
        assert f"/app/quiz/{lesson['quiz_id']}?mode=classic" in classic_markup

        quiz_markup = to_xml(main.quiz_page(request, lesson["quiz_id"]))
        assert "Chat mode" in quiz_markup
        assert "Classic mode" in quiz_markup
        assert 'class="quiz-question"' in quiz_markup


def test_estonian_grade_8_course_is_complete_localized_and_mastery_gated():
    import db
    from components import api as learning_api
    from estonian_chemistry_catalog import COURSE_SLUG, PROGRAM_CODE

    db.bootstrap_schema()
    db.bootstrap_schema()
    with db.begin() as conn:
        course_id = conn.execute(sa.text(f"""
            SELECT id FROM {db.S}.courses WHERE slug=:slug
        """), {"slug": COURSE_SLUG}).scalar_one()
        summary = conn.execute(sa.text(f"""
            SELECT count(DISTINCT l.id) AS lessons,
                   count(DISTINCT l.id) FILTER (WHERE l.lesson_kind='prelude') AS preludes,
                   count(DISTINCT qq.id) FILTER (WHERE qq.order_idx>=100) AS questions,
                   count(DISTINCT le.exercise_id) AS exercises
            FROM {db.S}.modules m
            JOIN {db.S}.lessons l ON l.module_id=m.id
            LEFT JOIN {db.S}.quizzes q ON q.lesson_id=l.id
            LEFT JOIN {db.S}.quiz_questions qq ON qq.quiz_id=q.id
            LEFT JOIN {db.S}.lesson_exercises le ON le.lesson_id=l.id
            WHERE m.course_id=:course
        """), {"course": course_id}).mappings().one()
        assert dict(summary) == {"lessons": 47, "preludes": 12, "questions": 515, "exercises": 47}

        profile = db.course_curriculum(conn, course_id)
        assert profile["program_code"] == PROGRAM_CODE
        assert profile["country_code"] == "EE"
        assert profile["grade_code"] == "8"
        assert profile["canonical_language"] == "et"
        assert profile["supported_languages"] == ["et", "en"]
        assert profile["estimated_periods"] == 70

        outcome_coverage = conn.execute(sa.text(f"""
            SELECT count(DISTINCT o.id)
            FROM {db.S}.curriculum_outcomes o
            JOIN {db.S}.curriculum_topics t ON t.id=o.topic_id
            JOIN {db.S}.curriculum_programs p ON p.id=t.program_id
            JOIN {db.S}.lesson_curriculum_outcomes lo ON lo.outcome_id=o.id
            WHERE p.code=:program
        """), {"program": PROGRAM_CODE}).scalar_one()
        assert outcome_coverage == 50

        lessons = conn.execute(sa.text(f"""
            SELECT l.id, l.title, q.id AS quiz_id
            FROM {db.S}.lessons l JOIN {db.S}.modules m ON m.id=l.module_id
            JOIN {db.S}.quizzes q ON q.lesson_id=l.id
            WHERE m.course_id=:course ORDER BY m.order_idx,l.order_idx LIMIT 2
        """), {"course": course_id}).mappings().all()
        user_id = conn.execute(sa.text(f"""
            INSERT INTO {db.S}.users (email,password_hash,display_name,role)
            VALUES ('ee-g8-integration@example.test','unused','Keemia õppija','student')
            ON CONFLICT (email) DO UPDATE SET display_name=EXCLUDED.display_name RETURNING id
        """)).scalar_one()
        conn.execute(sa.text(f"DELETE FROM {db.S}.quiz_attempts WHERE user_id=:user"), {"user": user_id})
        conn.execute(sa.text(f"DELETE FROM {db.S}.lesson_progress WHERE user_id=:user"), {"user": user_id})
        assert db.lesson_access(conn, user_id, lessons[0]["id"])["unlocked"]
        assert not db.lesson_access(conn, user_id, lessons[1]["id"])["unlocked"]
        db.mark_lesson_complete(conn, user_id, lessons[0]["id"])
        assert not db.lesson_access(conn, user_id, lessons[1]["id"])["unlocked"]
        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.quiz_attempts (user_id,quiz_id,score,passed,completed_at)
            VALUES (:user,:quiz,100,true,now())
        """), {"user": user_id, "quiz": lessons[0]["quiz_id"]})
        assert db.lesson_access(conn, user_id, lessons[1]["id"])["unlocked"]

    payload = learning_api.course_curriculum(course_id, None)
    assert payload["course"]["title"] == "Eesti 8. klassi keemia"
    assert payload["modules"][0]["lessons"][0]["title"] == "Ese, materjal ja aine"
    english = learning_api.course_curriculum(course_id, "en")
    assert english["course"]["title"] == "Estonian Grade 8 Chemistry"
