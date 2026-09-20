"""Regressions for the persistent, chat-first student experience."""

from pathlib import Path

from fasthtml.common import to_xml

import db
from components.layout import course_card, left_pane
import learning_chat
from learning_chat import _choices, resolve_choice


def test_choice_can_be_selected_by_letter_or_label():
    choices = [
        {"key": "A", "label": "Start the lesson", "value": 41},
        {"key": "B", "label": "Take the quiz", "value": 42},
    ]
    assert resolve_choice("A", choices)["value"] == 41
    assert resolve_choice("b", choices)["value"] == 42
    assert resolve_choice("Take the quiz", choices)["value"] == 42
    assert resolve_choice("explain it differently", choices) is None


def test_large_catalogues_keep_every_course_and_teacher_action_selectable():
    choices = _choices((f"Course {index}", index) for index in range(30))
    assert len(choices) == 30
    assert choices[25]["key"] == "Z"
    assert choices[26]["key"] == "AA"
    assert resolve_choice("AD", choices)["value"] == 29


def test_database_has_owned_persistent_chat_threads():
    assert "CREATE TABLE IF NOT EXISTS fastlms.chat_sessions" in db.SCHEMA_SQL
    assert "session_id      VARCHAR(36)" in db.SCHEMA_SQL
    assert "idx_chat_messages_session" in db.SCHEMA_SQL


def test_navigation_leads_with_new_chat_and_keeps_dashboard_secondary():
    markup = to_xml(left_pane(
        user={"id": 123456789, "display_name": "Learner", "role": "student", "xp": 0, "streak_days": 0},
        lang="en",
    ))
    assert 'href="/app/chat/new"' in markup
    assert 'href="/app/dashboard"' in markup
    assert markup.index("New Chat") < markup.index("Dashboard")


def test_catalogue_course_defaults_to_chat_mode():
    markup = to_xml(course_card({
        "id": 1, "slug": "mathematics-foundations", "title": "Mathematics Foundations",
        "description": "Learn maths", "difficulty": "beginner", "category": "Mathematics",
    }))
    assert 'href="/app/chat/new?course=mathematics-foundations"' in markup


def test_chat_client_posts_thread_id_and_renders_sse_choices():
    script = Path("static/chat.js").read_text(encoding="utf-8")
    assert "form.dataset.chatId" in script
    assert "data.choices" in script
    assert "requestSubmit()" in script
    assert "lesson_id: lessonId" not in script


def test_student_lesson_routes_offer_chat_and_classic_modes():
    source = Path("main.py").read_text(encoding="utf-8")
    course_route = source.split('def course_detail(req, slug: str):', 1)[1].split(
        '@app.post("/app/course/{course_id:int}/clone")', 1
    )[0]
    lesson_route = source.split('def lesson_page(req, lesson_id: int):', 1)[1].split(
        '@app.post("/app/lesson/{lesson_id:int}/complete")', 1
    )[0]
    quiz_route = source.split('def quiz_page(req, quiz_id: int):', 1)[1].split(
        '@app.post("/app/quiz/{quiz_id:int}/submit")', 1
    )[0]

    assert "role\") == \"student\"" not in course_route
    assert "role\") == \"student\"" not in lesson_route
    assert "role\") == \"student\"" not in quiz_route
    assert '/app/chat/new?course=' in course_route
    assert '/app/chat/new?lesson_id=' in lesson_route
    assert '?mode=classic' in lesson_route
    assert '/app/chat/new?lesson_id=' in quiz_route


def test_typed_chemistry_review_answers_use_choice_payload():
    chemistry = {"engine": "chemistry", "exercise_type": "multiple_choice"}
    chess = {"engine": "chess", "exercise_type": "multiple_choice"}

    assert learning_chat._typed_exercise_answer("B", chemistry) == {"choice": 1}
    assert learning_chat._typed_exercise_answer("B", chess) == {"answer": 1}


def test_global_chat_feedback_reveals_correction_and_reasoning():
    exercise = {
        "concepts": ["particle-model"],
        "choices": ["Solid", "Liquid", "Gas"],
        "answer_payload": {
            "choice": 0,
            "feedback": {
                "en": {
                    "correct_answer": "Solid",
                    "explanation": "Solid particles are packed most closely.",
                }
            },
        },
    }

    correct = learning_chat.exercise_feedback(exercise, "en", True)
    incorrect = learning_chat.exercise_feedback(exercise, "en", False)
    assert "Correct" in correct and "packed most closely" in correct
    assert "Not quite" in incorrect and "Solid" in incorrect
    assert "packed most closely" in incorrect


def test_free_form_and_voice_tutors_share_the_global_feedback_rule():
    main_source = Path("main.py").read_text(encoding="utf-8")
    voice_source = Path("voice.py").read_text(encoding="utf-8")
    rule = learning_chat.CHAT_FEEDBACK_RULE.lower()

    assert "explicitly say whether it is correct" in rule
    assert "state the correct answer" in rule
    assert "learning_chat.build_agent_system_prompt" in main_source
    assert learning_chat.CHAT_FEEDBACK_RULE in learning_chat.build_agent_system_prompt(
        role="student", language="en"
    )
    assert "CHAT_FEEDBACK_RULE" in voice_source


def test_teacher_chat_uses_complete_catalogue_and_management_paths(monkeypatch):
    monkeypatch.setattr(learning_chat.db, "get_courses", lambda _conn, lang="en": [
        {"id": 1, "slug": "default-maths", "title": "Default Maths"},
        {"id": 2, "slug": "default-art", "title": "Default Art"},
    ])
    result = learning_chat.initial_response(object(), 7, "en", role="teacher")
    labels = [choice["label"] for choice in result["context"]["choices"]]
    assert result["context"]["phase"] == "staff_picker"
    assert result["title"] == "Teacher workspace"
    assert result["content"].startswith("What would you like your students to learn?")
    assert labels[:2] == ["Default Maths", "Default Art"]
    assert "Assign courses to students" in labels
    assert "Preview the student experience" in labels

    next_step = learning_chat.handle_guided_message(
        object(), 7, result["context"], "A", "en"
    )
    assert next_step["redirect_url"] == "/app/course/default-maths"


def test_admin_and_student_openings_remain_role_specific(monkeypatch):
    monkeypatch.setattr(learning_chat.db, "get_courses", lambda _conn, lang="en": [])
    teacher = learning_chat.initial_response(object(), 1, "en", role="admin")
    student = learning_chat.initial_response(object(), 2, "en", role="student")
    assert teacher["content"].startswith("What would you like to manage?")
    assert student["content"].startswith("What would you like to learn?")


def test_default_chat_does_not_reopen_student_thread_for_teacher(monkeypatch, tmp_path):
    monkeypatch.setenv("FASTSME_AUTH_DB", str(tmp_path / "accounts.sqlite"))
    from main import _latest_session_for_role

    sessions = [
        {"id": "student-old", "context": {"phase": "course_picker"}},
        {"id": "teacher-current", "context": {"phase": "staff_picker", "role": "teacher"}},
    ]
    assert _latest_session_for_role(sessions, "teacher")["id"] == "teacher-current"
    assert _latest_session_for_role(sessions, "instructor")["id"] == "teacher-current"
    assert _latest_session_for_role(sessions, "student")["id"] == "student-old"
    assert _latest_session_for_role([sessions[0]], "teacher") is None
