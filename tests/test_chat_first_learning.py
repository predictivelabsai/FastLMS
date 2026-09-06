"""Regressions for the persistent, chat-first student experience."""

from pathlib import Path
from types import SimpleNamespace

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


def test_catalogue_course_opens_as_a_new_conversation():
    markup = to_xml(course_card({
        "id": 1, "slug": "mathematics-foundations", "title": "Mathematics Foundations",
        "description": "Learn maths", "difficulty": "beginner", "category": "Mathematics",
    }))
    assert 'href="/app/chat/new?course=mathematics-foundations"' in markup
    assert 'href="/app/course/' not in markup


def test_chat_client_posts_thread_id_and_renders_sse_choices():
    script = Path("static/chat.js").read_text(encoding="utf-8")
    assert "form.dataset.chatId" in script
    assert "data.choices" in script
    assert "requestSubmit()" in script
    assert "lesson_id: lessonId" not in script


def test_signed_in_entry_point_and_student_course_routes_open_chat(monkeypatch):
    import main

    request = SimpleNamespace(query_params={}, session={}, cookies={}, headers={})
    monkeypatch.setattr(main, "_require_login", lambda _req: ({"id": 9, "role": "student"}, None))
    home = main.app_home(request)
    course = main.course_detail(request, "art-history")
    lesson = main.lesson_page(request, 17)
    quiz = main.quiz_page(request, 22)

    assert home.headers["location"] == "/app/chat"
    assert course.headers["location"] == "/app/chat/new?course=art-history"
    assert lesson.headers["location"] == "/app/chat/new?lesson_id=17"
    assert quiz.headers["location"] == "/app/chat/new?quiz_id=22"


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
