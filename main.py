"""FastLMS — FastHTML learning management system with interactivity and AI tutor.

3-pane layout (left nav / center content / right canvas), SSE streaming chat,
PostgreSQL backend, XP + streaks + badges + leaderboard interactivity.

Usage:
    python main.py                     # http://localhost:5001
    python main.py --port 8000         # custom port
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fasthtml.common import *
from starlette.responses import StreamingResponse

import db
import school
from components.layout import (
    app_shell,
    auth_page,
    badge_card,
    course_card,
    progress_bar,
    xp_popup,
)

load_dotenv()

app = FastHTML(
    hdrs=[],
    static_path="static",
    secret_key=os.environ.get("SESSION_SECRET", "fastlms-dev-secret-change-me"),
)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _get_session_user(req) -> dict | None:
    uid = req.session.get("user_id")
    if not uid:
        return None
    with db.connect() as conn:
        return db.get_user(conn, uid)


def _require_login(req):
    user = _get_session_user(req)
    if not user:
        return None, RedirectResponse("/auth/login", status_code=303)
    return user, None


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

@app.get("/static/{path:path}")
def static_file(path: str):
    from starlette.responses import FileResponse
    fpath = f"static/{path}"
    if os.path.isfile(fpath):
        return FileResponse(fpath)
    return Response("Not found", status_code=404)


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

@app.get("/")
def landing(req):
    user = _get_session_user(req)
    if user:
        return RedirectResponse("/app", status_code=303)

    return Html(
        Head(
            Title("FastLMS"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Link(rel="stylesheet", href="/static/app.css"),
        ),
        Body(
            Div(
                Div(
                    Span("F", cls="brand-icon"),
                    Span("FastLMS", cls="brand-text"),
                    cls="brand",
                    style="justify-content: center; margin-bottom: 24px;",
                ),
                H1("Learn. Level up. Lead.", style="text-align:center; font-size:32px; margin-bottom:12px;"),
                P(
                    "Open-source learning platform with AI tutoring, interactivity, and real-time progress tracking.",
                    style="text-align:center; color:var(--ink-muted); max-width:500px; margin:0 auto 32px;",
                ),
                Div(
                    A("Get Started", href="/auth/register", cls="btn btn-primary", style="font-size:16px; padding:14px 32px;"),
                    A("Sign In", href="/auth/login", cls="btn btn-secondary", style="font-size:16px; padding:14px 32px;"),
                    style="display:flex; gap:16px; justify-content:center;",
                ),
                style="padding: 120px 24px;",
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.get("/auth/login")
def login_page(req):
    error = req.query_params.get("error", "")
    return auth_page(
        Div(
            H2("Sign in", cls="auth-title"),
            (Div(error, cls="form-error") if error else ""),
            Form(
                Div(Label("Email", cls="form-label"), Input(name="email", type="email", cls="form-input", required=True), cls="form-group"),
                Div(Label("Password", cls="form-label"), Input(name="password", type="password", cls="form-input", required=True), cls="form-group"),
                Button("Sign in", cls="btn btn-primary btn-block", type="submit"),
                method="post",
                action="/auth/login",
            ),
            Div(A("Create an account", href="/auth/register"), cls="auth-footer"),
            cls="auth-box",
        ),
    )


@app.post("/auth/login")
async def login_post(req):
    form = await req.form()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    with db.connect() as conn:
        user = db.get_user_by_email(conn, email)
    if not user or user["password_hash"] != _hash_pw(password):
        return RedirectResponse("/auth/login?error=Invalid+email+or+password", status_code=303)
    req.session["user_id"] = user["id"]
    return RedirectResponse("/app", status_code=303)


@app.get("/auth/register")
def register_page(req):
    error = req.query_params.get("error", "")
    return auth_page(
        Div(
            H2("Create account", cls="auth-title"),
            (Div(error, cls="form-error") if error else ""),
            Form(
                Div(Label("Display name", cls="form-label"), Input(name="display_name", cls="form-input", required=True), cls="form-group"),
                Div(Label("Email", cls="form-label"), Input(name="email", type="email", cls="form-input", required=True), cls="form-group"),
                Div(Label("Password", cls="form-label"), Input(name="password", type="password", cls="form-input", required=True, minlength=6), cls="form-group"),
                Button("Create account", cls="btn btn-primary btn-block", type="submit"),
                method="post",
                action="/auth/register",
            ),
            Div(A("Already have an account? Sign in", href="/auth/login"), cls="auth-footer"),
            cls="auth-box",
        ),
    )


@app.post("/auth/register")
async def register_post(req):
    form = await req.form()
    name = form.get("display_name", "").strip()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    if not name or not email or len(password) < 6:
        return RedirectResponse("/auth/register?error=All+fields+required+and+password+min+6+chars", status_code=303)
    with db.begin() as conn:
        existing = db.get_user_by_email(conn, email)
        if existing:
            return RedirectResponse("/auth/register?error=Email+already+registered", status_code=303)
        import sqlalchemy as sa
        conn.execute(
            sa.text(f"INSERT INTO {db.S}.users (email, password_hash, display_name) VALUES (:e, :p, :n)"),
            {"e": email, "p": _hash_pw(password), "n": name},
        )
        user = db.get_user_by_email(conn, email)
    req.session["user_id"] = user["id"]
    return RedirectResponse("/app", status_code=303)


@app.get("/auth/logout")
def logout(req):
    req.session.clear()
    return RedirectResponse("/", status_code=303)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/app")
def dashboard(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    with db.connect() as conn:
        courses = db.get_courses(conn)
        import sqlalchemy as sa
        lessons_done = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.lesson_progress WHERE user_id = :u AND status = 'completed'"),
            {"u": user["id"]},
        ).scalar()
        badges = db.get_user_badges(conn, user["id"])
        enrolments = conn.execute(
            sa.text(f"SELECT course_id FROM {db.S}.enrolments WHERE user_id = :u"),
            {"u": user["id"]},
        ).mappings().all()
        enrolled_ids = {e["course_id"] for e in enrolments}

        my_courses = []
        for c in courses:
            if c["id"] in enrolled_ids:
                prog = db.get_user_course_progress(conn, user["id"], c["id"])
                my_courses.append((c, prog))

    content = Div(
        Div(
            H1(f"Welcome back, {user['display_name']}", cls="page-title"),
            P("Your learning dashboard", cls="page-subtitle"),

            Div(
                Div(Div(str(user["xp"]), cls="dashboard-card-value"), Div("Total XP", cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(user["level"], cls="dashboard-card-value"), Div("Level", cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(f"{user['streak_days']}d", cls="dashboard-card-value"), Div("Streak", cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(str(lessons_done), cls="dashboard-card-value"), Div("Lessons Done", cls="dashboard-card-label"), cls="dashboard-card"),
                cls="dashboard-grid",
            ),

            (Div(
                H2("My Courses", style="font-size:18px; font-weight:600; margin-bottom:16px;"),
                Div(*[course_card(c, prog) for c, prog in my_courses], cls="courses-grid"),
                style="margin-bottom:32px;",
            ) if my_courses else ""),

            (Div(
                H2("My Badges", style="font-size:18px; font-weight:600; margin-bottom:16px;"),
                Div(*[badge_card(b) for b in badges], cls="badges-grid"),
                style="margin-bottom:32px;",
            ) if badges else ""),

            (Div(
                H2("Browse Courses", style="font-size:18px; font-weight:600; margin-bottom:16px;"),
                Div(*[course_card(c) for c in courses if c["id"] not in enrolled_ids], cls="courses-grid"),
            ) if any(c["id"] not in enrolled_ids for c in courses) else ""),

            cls="page-content",
        ),
    )
    return app_shell(content, user=user, active="dashboard")


# ---------------------------------------------------------------------------
# Courses list
# ---------------------------------------------------------------------------

@app.get("/app/courses")
def courses_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    with db.connect() as conn:
        courses = db.get_courses(conn)
        import sqlalchemy as sa
        enrolments = conn.execute(
            sa.text(f"SELECT course_id FROM {db.S}.enrolments WHERE user_id = :u"),
            {"u": user["id"]},
        ).mappings().all()
        enrolled_ids = {e["course_id"] for e in enrolments}

        cards = []
        for c in courses:
            prog = db.get_user_course_progress(conn, user["id"], c["id"]) if c["id"] in enrolled_ids else None
            cards.append(course_card(c, prog))

    content = Div(
        H1("Courses", cls="page-title"),
        P("Browse all available courses", cls="page-subtitle"),
        Div(*cards, cls="courses-grid") if cards else Div(
            Div("No courses yet", cls="empty-state-text"),
            cls="empty-state",
        ),
        cls="page-content",
    )
    return app_shell(content, user=user, active="courses")


# ---------------------------------------------------------------------------
# Course detail + lesson navigation
# ---------------------------------------------------------------------------

@app.get("/app/course/{slug}")
def course_detail(req, slug: str):
    user, redir = _require_login(req)
    if redir:
        return redir

    with db.connect() as conn:
        course = db.get_course(conn, slug)
        if not course:
            return Response("Course not found", status_code=404)

        modules = db.get_modules(conn, course["id"])
        import sqlalchemy as sa
        enrolled = conn.execute(
            sa.text(f"SELECT 1 FROM {db.S}.enrolments WHERE user_id = :u AND course_id = :c"),
            {"u": user["id"], "c": course["id"]},
        ).scalar()
        prog = db.get_user_course_progress(conn, user["id"], course["id"])

        sidebar_items = []
        first_lesson_id = None
        for m in modules:
            lessons = db.get_lessons(conn, m["id"])
            sidebar_items.append(Div(m["title"], cls="module-header"))
            for les in lessons:
                if first_lesson_id is None:
                    first_lesson_id = les["id"]
                lp = db.get_lesson_progress(conn, user["id"], les["id"])
                done = lp and lp["status"] == "completed"
                cls = "lesson-list-item" + (" completed" if done else "")
                check_cls = "lesson-check" + (" done" if done else "")
                sidebar_items.append(
                    A(
                        Span("✓" if done else "", cls=check_cls),
                        Span(les["title"]),
                        href=f"/app/lesson/{les['id']}",
                        cls=cls,
                    )
                )

    hero = Div(
        Div(
            H1(course["title"]),
            P(course.get("description", "")),
            Div(
                Span(f"Difficulty: {course.get('difficulty', 'beginner').title()}"),
                Span(f"Progress: {prog['percent']}%"),
                cls="course-hero-meta",
            ),
            (Form(
                Button("Enrol", cls="btn btn-primary", type="submit", style="margin-top:16px;"),
                method="post",
                action=f"/app/course/{slug}/enrol",
            ) if not enrolled else ""),
            cls="course-hero-inner",
        ),
        cls="course-hero",
    )

    body = Div(
        Div(*sidebar_items, cls="course-sidebar") if sidebar_items else "",
        Div(
            progress_bar(prog["percent"], f"{prog['completed']}/{prog['total']} lessons"),
            Div(
                P("Select a lesson from the sidebar to begin.", style="color:var(--ink-muted); margin-top:24px;"),
                cls="lesson-placeholder",
            ),
        ),
        cls="course-body",
    )

    content = Div(hero, body)
    return app_shell(content, user=user, active="courses", title=course["title"])


@app.post("/app/course/{slug}/enrol")
async def enrol(req, slug: str):
    user, redir = _require_login(req)
    if redir:
        return redir
    with db.begin() as conn:
        course = db.get_course(conn, slug)
        if not course:
            return Response("Not found", status_code=404)
        import sqlalchemy as sa
        conn.execute(
            sa.text(f"INSERT INTO {db.S}.enrolments (user_id, course_id) VALUES (:u, :c) ON CONFLICT DO NOTHING"),
            {"u": user["id"], "c": course["id"]},
        )
    return RedirectResponse(f"/app/course/{slug}", status_code=303)


# ---------------------------------------------------------------------------
# Lesson view
# ---------------------------------------------------------------------------

@app.get("/app/lesson/{lesson_id:int}")
def lesson_page(req, lesson_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir

    import markdown as md
    import sqlalchemy as sa

    with db.connect() as conn:
        lesson = db.get_lesson(conn, lesson_id)
        if not lesson:
            return Response("Lesson not found", status_code=404)

        module = conn.execute(sa.text(f"SELECT * FROM {db.S}.modules WHERE id = :m"), {"m": lesson["module_id"]}).mappings().first()
        course = conn.execute(sa.text(f"SELECT * FROM {db.S}.courses WHERE id = :c"), {"c": module["course_id"]}).mappings().first()

        lp = db.get_lesson_progress(conn, user["id"], lesson_id)
        is_done = lp and lp["status"] == "completed"

        quiz = db.get_quiz_for_lesson(conn, lesson_id)
        discussions = db.get_discussions(conn, lesson_id)

        # Get next lesson
        next_lesson = conn.execute(
            sa.text(f"""
                SELECT l.id FROM {db.S}.lessons l
                WHERE l.module_id = :m AND l.order_idx > :o
                ORDER BY l.order_idx LIMIT 1
            """),
            {"m": lesson["module_id"], "o": lesson["order_idx"]},
        ).scalar()

    content_html = md.markdown(lesson.get("content_md") or "", extensions=["fenced_code", "tables", "nl2br"])

    video_embed = ""
    if lesson.get("video_url"):
        video_embed = Iframe(src=lesson["video_url"], cls="lesson-video", allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture", allowfullscreen=True)

    actions = []
    if not is_done:
        actions.append(
            Form(
                Button("Mark Complete", cls="btn btn-green", type="submit"),
                method="post",
                action=f"/app/lesson/{lesson_id}/complete",
            )
        )
    else:
        actions.append(Span("Completed", cls="btn btn-secondary", style="opacity:0.6;"))

    if quiz:
        actions.append(A("Take Quiz", href=f"/app/quiz/{quiz['id']}", cls="btn btn-blue"))

    actions.append(A("AI Tutor", href=f"/app/chat?lesson_id={lesson_id}", cls="btn btn-secondary"))

    if next_lesson:
        actions.append(A("Next Lesson", href=f"/app/lesson/{next_lesson}", cls="btn btn-secondary"))

    lesson_view = Div(
        Div(
            A(course["title"], href=f"/app/course/{course['slug']}"),
            Span(" / ", style="color:var(--ink-dim)"),
            Span(module["title"]),
            cls="lesson-breadcrumb",
        ),
        H1(lesson["title"], cls="lesson-title"),
        Div(
            Span(f"{lesson.get('duration_min', 0)} min") if lesson.get("duration_min") else "",
            Span(f"+{lesson.get('xp_reward', 25)} XP"),
            Span(f"{lesson.get('content_type', 'text').title()}"),
            cls="lesson-meta",
        ),
        video_embed,
        Div(NotStr(content_html), cls="lesson-content"),
        Div(*actions, cls="lesson-actions"),
        cls="lesson-layout",
    )
    return app_shell(lesson_view, user=user, active="courses", title=lesson["title"])


@app.post("/app/lesson/{lesson_id:int}/complete")
async def complete_lesson(req, lesson_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir
    with db.begin() as conn:
        xp = db.mark_lesson_complete(conn, user["id"], lesson_id)
        new_badges = db.check_and_award_badges(conn, user["id"])
    return RedirectResponse(f"/app/lesson/{lesson_id}?xp={xp}", status_code=303)


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------

@app.get("/app/quiz/{quiz_id:int}")
def quiz_page(req, quiz_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir

    with db.connect() as conn:
        import sqlalchemy as sa
        quiz = conn.execute(sa.text(f"SELECT * FROM {db.S}.quizzes WHERE id = :q"), {"q": quiz_id}).mappings().first()
        if not quiz:
            return Response("Quiz not found", status_code=404)
        questions = db.get_quiz_questions(conn, quiz_id)
        lesson = db.get_lesson(conn, quiz["lesson_id"])

    q_items = []
    for i, q in enumerate(questions):
        options = q["options"] if isinstance(q["options"], list) else json.loads(q["options"])
        option_els = []
        for opt in options:
            option_els.append(
                Div(
                    Input(type="radio", name=f"q_{q['id']}", value=opt, id=f"q_{q['id']}_{opt}"),
                    Label(opt, _for=f"q_{q['id']}_{opt}"),
                    cls="quiz-option",
                )
            )
        q_items.append(
            Div(
                Div(f"Question {i + 1}", style="font-size:11px; color:var(--ink-dim); margin-bottom:8px;"),
                Div(q["question_text"], cls="quiz-question-text"),
                Div(*option_els, cls="quiz-options"),
                cls="quiz-question",
            )
        )

    content = Div(
        Div(
            A(f"← Back to lesson", href=f"/app/lesson/{quiz['lesson_id']}", style="font-size:13px; color:var(--ink-muted);"),
            cls="lesson-breadcrumb",
        ),
        H1(quiz["title"], cls="page-title"),
        P(f"Pass threshold: {quiz['pass_threshold']}%  •  +{quiz['xp_reward']} XP on pass", cls="page-subtitle"),
        Form(
            *q_items,
            Button("Submit Quiz", cls="btn btn-primary", type="submit", style="margin-top:24px;"),
            method="post",
            action=f"/app/quiz/{quiz_id}/submit",
        ),
        cls="quiz-container",
    )
    return app_shell(content, user=user, active="courses", title=quiz["title"])


@app.post("/app/quiz/{quiz_id:int}/submit")
async def submit_quiz(req, quiz_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    import sqlalchemy as sa

    with db.begin() as conn:
        quiz = conn.execute(sa.text(f"SELECT * FROM {db.S}.quizzes WHERE id = :q"), {"q": quiz_id}).mappings().first()
        questions = db.get_quiz_questions(conn, quiz_id)

        correct = 0
        total = len(questions)
        answers = {}
        results = []

        for q in questions:
            user_answer = form.get(f"q_{q['id']}", "")
            answers[str(q["id"])] = user_answer
            is_correct = user_answer == q["correct_answer"]
            if is_correct:
                correct += 1
            results.append({
                "question": q["question_text"],
                "user_answer": user_answer,
                "correct_answer": q["correct_answer"],
                "is_correct": is_correct,
                "explanation": q.get("explanation", ""),
            })

        score = round(correct / total * 100) if total else 0
        passed = score >= quiz["pass_threshold"]

        conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.quiz_attempts (user_id, quiz_id, score, passed, answers, completed_at)
                VALUES (:u, :q, :s, :p, :a, now())
            """),
            {"u": user["id"], "q": quiz_id, "s": score, "p": passed, "a": json.dumps(answers)},
        )

        xp_earned = 0
        if passed:
            xp_earned = quiz["xp_reward"]
            conn.execute(sa.text(f"UPDATE {db.S}.users SET xp = xp + :xp WHERE id = :u"), {"xp": xp_earned, "u": user["id"]})
            db._update_streak(conn, user["id"])
            db._update_level(conn, user["id"])
            db.check_and_award_badges(conn, user["id"])

    result_items = []
    for r in results:
        cls = "quiz-option correct" if r["is_correct"] else "quiz-option incorrect"
        result_items.append(
            Div(
                Div(r["question"], cls="quiz-question-text"),
                Div(
                    Div(f"Your answer: {r['user_answer']}", cls=cls),
                    (Div(f"Correct answer: {r['correct_answer']}", cls="quiz-option correct") if not r["is_correct"] else ""),
                    (Div(r["explanation"], cls="quiz-explanation") if r.get("explanation") else ""),
                    cls="quiz-options",
                ),
                cls="quiz-question",
            )
        )

    score_cls = "quiz-score pass" if passed else "quiz-score fail"
    content = Div(
        Div(
            Div(f"{score}%", cls=score_cls),
            Div("Passed!" if passed else "Not passed", style=f"font-size:18px; color: {'var(--green)' if passed else 'var(--red)'}; margin-bottom:8px;"),
            (Div(f"+{xp_earned} XP earned!", style="color:var(--accent-text); font-weight:600;") if xp_earned else ""),
            cls="quiz-result",
        ),
        *result_items,
        Div(
            A("Back to lesson", href=f"/app/lesson/{quiz['lesson_id']}", cls="btn btn-secondary"),
            (A("Retry", href=f"/app/quiz/{quiz_id}", cls="btn btn-primary") if not passed else ""),
            style="display:flex; gap:12px; justify-content:center; margin-top:24px;",
        ),
        cls="quiz-container",
    )
    return app_shell(content, user=user, active="courses", title="Quiz Results")


# ---------------------------------------------------------------------------
# Chat (AI Tutor)
# ---------------------------------------------------------------------------

@app.get("/app/chat")
def chat_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    lesson_id = req.query_params.get("lesson_id", "")

    with db.connect() as conn:
        history = db.get_chat_history(conn, user["id"], int(lesson_id) if lesson_id else None, limit=50)

    msg_els = []
    for m in history:
        cls = "msg msg-user" if m["role"] == "user" else "msg msg-assistant"
        if m["role"] == "assistant":
            msg_els.append(Div(
                Div(Span("AI Tutor"), cls="msg-header"),
                Div(NotStr(m["content"]), cls="msg-content"),
                cls=cls,
            ))
        else:
            msg_els.append(Div(m["content"], cls=cls))

    content = Div(
        Div("AI Tutor", cls="chat-header"),
        Div(*msg_els, id="chat-messages", cls="chat-messages"),
        Div(
            Form(
                Div(
                    Textarea(placeholder="Ask anything about the lesson...", id="chat-input", cls="chat-input", rows=1),
                    Button("Send", cls="chat-send", type="submit"),
                    cls="chat-input-row",
                ),
                id="chat-form",
                data_lesson_id=lesson_id,
            ),
            cls="chat-input-area",
        ),
        cls="chat-container",
    )
    return app_shell(content, user=user, active="chat", title="AI Tutor")


@app.get("/app/chat/stream")
async def chat_stream(req):
    user = _get_session_user(req)
    if not user:
        return Response("Unauthorized", status_code=401)

    message = req.query_params.get("message", "").strip()
    lesson_id = req.query_params.get("lesson_id", "")
    lesson_id_int = int(lesson_id) if lesson_id else None

    if not message:
        return Response("No message", status_code=400)

    import sqlalchemy as sa
    with db.begin() as conn:
        conn.execute(
            sa.text(f"INSERT INTO {db.S}.chat_messages (user_id, lesson_id, role, content) VALUES (:u, :l, 'user', :c)"),
            {"u": user["id"], "l": lesson_id_int, "c": message},
        )

    lesson_context = ""
    if lesson_id_int:
        with db.connect() as conn:
            lesson = db.get_lesson(conn, lesson_id_int)
            if lesson:
                lesson_context = f"\n\nThe student is currently studying the lesson: '{lesson['title']}'\nLesson content:\n{lesson.get('content_md', '')[:2000]}"

    async def generate():
        try:
            provider = os.environ.get("MODEL_PROVIDER", "xai")
            model = os.environ.get("DEFAULT_MODEL", "grok-4-1-fast-reasoning")

            system_prompt = f"""You are an AI tutor on FastLMS, an open-source learning platform.
Help students understand course material, answer questions, and guide them through concepts.
Be encouraging, clear, and concise. Use examples when helpful.
If the student seems stuck, break down the problem into smaller steps.
Format responses in Markdown when appropriate.{lesson_context}"""

            full_response = ""

            if provider == "xai":
                import httpx
                api_key = os.environ.get("XAI_API_KEY", "")
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}], "stream": True},
                        timeout=60,
                    )
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                chunk = json.loads(line[6:])
                                token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if token:
                                    full_response += token
                                    yield f"data: {json.dumps({'token': token})}\n\n"
                            except json.JSONDecodeError:
                                pass

            elif provider == "openai":
                import httpx
                api_key = os.environ.get("OPENAI_API_KEY", "")
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}], "stream": True},
                        timeout=60,
                    )
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                chunk = json.loads(line[6:])
                                token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if token:
                                    full_response += token
                                    yield f"data: {json.dumps({'token': token})}\n\n"
                            except json.JSONDecodeError:
                                pass

            elif provider == "anthropic":
                import httpx
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                        json={"model": model, "max_tokens": 4096, "system": system_prompt, "messages": [{"role": "user", "content": message}], "stream": True},
                        timeout=60,
                    )
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                chunk = json.loads(line[6:])
                                if chunk.get("type") == "content_block_delta":
                                    token = chunk.get("delta", {}).get("text", "")
                                    if token:
                                        full_response += token
                                        yield f"data: {json.dumps({'token': token})}\n\n"
                            except json.JSONDecodeError:
                                pass
            else:
                full_response = "No LLM provider configured. Set MODEL_PROVIDER in .env to 'xai', 'openai', or 'anthropic'."
                yield f"data: {json.dumps({'token': full_response})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

            with db.begin() as conn:
                conn.execute(
                    sa.text(f"INSERT INTO {db.S}.chat_messages (user_id, lesson_id, role, content) VALUES (:u, :l, 'assistant', :c)"),
                    {"u": user["id"], "l": lesson_id_int, "c": full_response},
                )

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

@app.get("/app/leaderboard")
def leaderboard_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    with db.connect() as conn:
        leaders = db.get_leaderboard(conn)

    rows = []
    for i, l in enumerate(leaders, 1):
        rank_cls = f"rank-{i}" if i <= 3 else ""
        level_cls = f"level-badge level-{l['level']}"
        rows.append(Tr(
            Td(str(i), cls=rank_cls),
            Td(l["display_name"], cls=rank_cls),
            Td(Span(l["level"], cls=level_cls)),
            Td(f"{l['xp']:,}"),
            Td(f"{l['streak_days']}d"),
        ))

    content = Div(
        H1("Leaderboard", cls="page-title"),
        P("Top learners ranked by XP", cls="page-subtitle"),
        Table(
            Thead(Tr(Th("#"), Th("Name"), Th("Level"), Th("XP"), Th("Streak"))),
            Tbody(*rows),
            cls="leaderboard-table",
        ) if rows else Div(Div("No learners yet", cls="empty-state-text"), cls="empty-state"),
        cls="page-content",
    )
    return app_shell(content, user=user, active="leaderboard")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@app.get("/app/profile")
def profile_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    with db.connect() as conn:
        badges = db.get_user_badges(conn, user["id"])
        import sqlalchemy as sa
        lessons_done = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.lesson_progress WHERE user_id = :u AND status = 'completed'"),
            {"u": user["id"]},
        ).scalar()
        quizzes_passed = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.quiz_attempts WHERE user_id = :u AND passed = true"),
            {"u": user["id"]},
        ).scalar()

    # XP to next level
    current_xp = user["xp"]
    next_level = None
    for threshold, name in db.LEVELS:
        if threshold > current_xp:
            next_level = (threshold, name)
            break

    content = Div(
        H1(user["display_name"], cls="page-title"),
        P(user["email"], cls="page-subtitle"),

        Div(
            Div(Div(str(current_xp), cls="dashboard-card-value"), Div("Total XP", cls="dashboard-card-label"), cls="dashboard-card"),
            Div(Div(user["level"], cls="dashboard-card-value"), Div("Level", cls="dashboard-card-label"), cls="dashboard-card"),
            Div(Div(f"{user['streak_days']}d", cls="dashboard-card-value"), Div("Streak", cls="dashboard-card-label"), cls="dashboard-card"),
            Div(Div(str(lessons_done), cls="dashboard-card-value"), Div("Lessons", cls="dashboard-card-label"), cls="dashboard-card"),
            Div(Div(str(quizzes_passed), cls="dashboard-card-value"), Div("Quizzes Passed", cls="dashboard-card-label"), cls="dashboard-card"),
            cls="dashboard-grid",
        ),

        (Div(
            H2("Next Level", style="font-size:16px; margin:24px 0 12px;"),
            P(f"{next_level[1]} — {next_level[0] - current_xp} XP to go", style="color:var(--ink-muted); margin-bottom:8px;"),
            progress_bar(round(current_xp / next_level[0] * 100)),
        ) if next_level else ""),

        (Div(
            H2("Badges", style="font-size:16px; margin:24px 0 12px;"),
            Div(*[badge_card(b) for b in badges], cls="badges-grid"),
        ) if badges else ""),

        cls="page-content",
    )
    return app_shell(content, user=user, active=None)


# ---------------------------------------------------------------------------
# Manage courses (instructor)
# ---------------------------------------------------------------------------

@app.get("/app/manage")
def manage_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir
    if user["role"] not in ("instructor", "admin"):
        return RedirectResponse("/app", status_code=303)

    with db.connect() as conn:
        courses = db.get_courses(conn, published_only=False)

    rows = []
    for c in courses:
        status_cls = "status-pill status-published" if c["is_published"] else "status-pill status-draft"
        rows.append(Tr(
            Td(A(c["title"], href=f"/app/course/{c['slug']}")),
            Td(c.get("category", "")),
            Td(c.get("difficulty", "").title()),
            Td(Span("Published" if c["is_published"] else "Draft", cls=status_cls)),
        ))

    content = Div(
        Div(
            H1("Manage Courses", cls="page-title"),
            A("+ New Course", href="/app/manage/new", cls="btn btn-primary btn-sm"),
            style="display:flex; justify-content:space-between; align-items:center;",
        ),
        Table(
            Thead(Tr(Th("Title"), Th("Category"), Th("Difficulty"), Th("Status"))),
            Tbody(*rows),
            cls="manage-table",
        ) if rows else Div(Div("No courses yet", cls="empty-state-text"), cls="empty-state"),
        cls="page-content",
    )
    return app_shell(content, user=user, active="manage")


# ---------------------------------------------------------------------------
# Course Configuration (instructor wizard)
# ---------------------------------------------------------------------------

@app.get("/app/configure")
def configure_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir
    if user["role"] not in ("instructor", "admin"):
        return RedirectResponse("/app", status_code=303)

    step = req.query_params.get("step", "1")
    course_id = req.query_params.get("course_id", "")
    module_id = req.query_params.get("module_id", "")
    lesson_id = req.query_params.get("lesson_id", "")
    msg = req.query_params.get("msg", "")
    error = req.query_params.get("error", "")

    import sqlalchemy as sa

    with db.connect() as conn:
        courses = db.get_courses(conn, published_only=False)
        selected_course = None
        modules = []
        lessons = []
        selected_module = None
        selected_lesson = None

        if course_id:
            selected_course = conn.execute(
                sa.text(f"SELECT * FROM {db.S}.courses WHERE id = :c"), {"c": int(course_id)}
            ).mappings().first()
            if selected_course:
                selected_course = dict(selected_course)
                modules = db.get_modules(conn, int(course_id))

        if module_id:
            selected_module = conn.execute(
                sa.text(f"SELECT * FROM {db.S}.modules WHERE id = :m"), {"m": int(module_id)}
            ).mappings().first()
            if selected_module:
                selected_module = dict(selected_module)
                lessons = db.get_lessons(conn, int(module_id))

        if lesson_id:
            selected_lesson = db.get_lesson(conn, int(lesson_id))

    steps_bar = Div(
        *[Div(
            Span(str(i), cls="step-num" + (" active" if step == str(i) else "")),
            Span(label, cls="step-label"),
            cls="step-item",
        ) for i, label in [(1, "Course"), (2, "Modules"), (3, "Lessons"), (4, "Quizzes"), (5, "Publish")]],
        cls="steps-bar",
    )

    alert = ""
    if msg:
        alert = Div(msg, cls="alert alert-success")
    if error:
        alert = Div(error, cls="alert alert-error")

    body = Div("Select a step above.")

    if step == "1":
        body = Div(
            H2("Create or select a course", style="font-size:18px; margin-bottom:16px;"),
            (Div(
                H3("Existing courses", style="font-size:14px; color:var(--ink-muted); margin-bottom:8px;"),
                *[Div(
                    A(c["title"], href=f"/app/configure?step=2&course_id={c['id']}",
                      style="color:var(--accent-text); font-weight:500;"),
                    Span(f" — {c.get('category', '')} / {c.get('difficulty', '').title()}", style="color:var(--ink-muted); font-size:13px;"),
                    Span(" (Draft)" if not c["is_published"] else " (Published)", style="font-size:12px; color:var(--ink-dim);"),
                    style="padding:6px 0;",
                ) for c in courses],
                style="margin-bottom:24px; border-bottom:1px solid var(--border); padding-bottom:16px;",
            ) if courses else ""),
            H3("New course", style="font-size:14px; color:var(--ink-muted); margin-bottom:12px;"),
            Form(
                Div(Label("Title", cls="form-label"), Input(name="title", cls="form-input", required=True, placeholder="e.g. Introduction to Data Science"), cls="form-group"),
                Div(Label("Category", cls="form-label"), Input(name="category", cls="form-input", placeholder="e.g. Computer Science"), cls="form-group"),
                Div(
                    Label("Difficulty", cls="form-label"),
                    Select(
                        Option("Beginner", value="beginner"),
                        Option("Intermediate", value="intermediate"),
                        Option("Advanced", value="advanced"),
                        name="difficulty", cls="form-input",
                    ),
                    cls="form-group",
                ),
                Div(Label("Description", cls="form-label"), Textarea(name="description", cls="form-input", rows=3, placeholder="A short description of what students will learn..."), cls="form-group"),
                Button("Create Course", cls="btn btn-primary", type="submit"),
                method="post",
                action="/app/configure/create-course",
            ),
        )

    elif step == "2" and selected_course:
        module_list = ""
        if modules:
            module_list = Div(
                H3("Existing modules", style="font-size:14px; color:var(--ink-muted); margin-bottom:8px;"),
                *[Div(
                    A(m["title"], href=f"/app/configure?step=3&course_id={course_id}&module_id={m['id']}",
                      style="color:var(--accent-text); font-weight:500;"),
                    Span(f" (order: {m['order_idx']})", style="color:var(--ink-dim); font-size:12px;"),
                    style="padding:6px 0;",
                ) for m in modules],
                style="margin-bottom:24px; border-bottom:1px solid var(--border); padding-bottom:16px;",
            )

        body = Div(
            A("← Back to courses", href="/app/configure?step=1", style="font-size:13px; color:var(--ink-muted);"),
            H2(f"Modules for: {selected_course['title']}", style="font-size:18px; margin:12px 0 16px;"),
            module_list,
            H3("Add module", style="font-size:14px; color:var(--ink-muted); margin-bottom:12px;"),
            Form(
                Input(type="hidden", name="course_id", value=course_id),
                Div(Label("Title", cls="form-label"), Input(name="title", cls="form-input", required=True, placeholder="e.g. Module 1: Foundations"), cls="form-group"),
                Div(Label("Description", cls="form-label"), Textarea(name="description", cls="form-input", rows=2, placeholder="Module overview..."), cls="form-group"),
                Div(Label("Order", cls="form-label"), Input(name="order_idx", type="number", cls="form-input", value=str(len(modules))), cls="form-group"),
                Button("Add Module", cls="btn btn-primary", type="submit"),
                method="post",
                action="/app/configure/create-module",
            ),
            Div(
                A("Skip to Publish →", href=f"/app/configure?step=5&course_id={course_id}", cls="btn btn-secondary", style="margin-top:16px;"),
            ),
        )

    elif step == "3" and selected_module:
        lesson_list = ""
        if lessons:
            lesson_list = Div(
                H3("Existing lessons", style="font-size:14px; color:var(--ink-muted); margin-bottom:8px;"),
                *[Div(
                    A(l["title"], href=f"/app/configure?step=4&course_id={course_id}&module_id={module_id}&lesson_id={l['id']}",
                      style="color:var(--accent-text); font-weight:500;"),
                    Span(f" (+{l['xp_reward']} XP, {l.get('duration_min', 0)}min)", style="color:var(--ink-dim); font-size:12px;"),
                    style="padding:6px 0;",
                ) for l in lessons],
                style="margin-bottom:24px; border-bottom:1px solid var(--border); padding-bottom:16px;",
            )

        body = Div(
            A(f"← Back to modules", href=f"/app/configure?step=2&course_id={course_id}", style="font-size:13px; color:var(--ink-muted);"),
            H2(f"Lessons for: {selected_module['title']}", style="font-size:18px; margin:12px 0 16px;"),
            lesson_list,
            H3("Add lesson", style="font-size:14px; color:var(--ink-muted); margin-bottom:12px;"),
            Form(
                Input(type="hidden", name="course_id", value=course_id),
                Input(type="hidden", name="module_id", value=module_id),
                Div(Label("Title", cls="form-label"), Input(name="title", cls="form-input", required=True, placeholder="e.g. Variables and Data Types"), cls="form-group"),
                Div(
                    Label("Content (Markdown)", cls="form-label"),
                    Textarea(name="content_md", cls="form-input", rows=12, placeholder="# Lesson Title\n\nWrite your lesson content in **Markdown**...\n\n```python\nprint('Hello')\n```"),
                    cls="form-group",
                ),
                Div(
                    Div(Label("XP Reward", cls="form-label"), Input(name="xp_reward", type="number", cls="form-input", value="25"), cls="form-group"),
                    Div(Label("Duration (min)", cls="form-label"), Input(name="duration_min", type="number", cls="form-input", value="15"), cls="form-group"),
                    Div(Label("Order", cls="form-label"), Input(name="order_idx", type="number", cls="form-input", value=str(len(lessons))), cls="form-group"),
                    style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px;",
                ),
                Div(Label("Video URL (optional)", cls="form-label"), Input(name="video_url", cls="form-input", placeholder="https://youtube.com/embed/..."), cls="form-group"),
                Button("Add Lesson", cls="btn btn-primary", type="submit"),
                method="post",
                action="/app/configure/create-lesson",
            ),
        )

    elif step == "4" and selected_lesson:
        with db.connect() as conn:
            quiz = db.get_quiz_for_lesson(conn, int(lesson_id))
            questions = db.get_quiz_questions(conn, quiz["id"]) if quiz else []

        existing_q = ""
        if questions:
            existing_q = Div(
                H3("Existing questions", style="font-size:14px; color:var(--ink-muted); margin-bottom:8px;"),
                *[Div(
                    Span(f"Q{i+1}: ", style="font-weight:600;"),
                    Span(q["question_text"]),
                    Span(f" (Answer: {q['correct_answer']})", style="color:var(--ink-dim); font-size:12px;"),
                    style="padding:6px 0; font-size:13px;",
                ) for i, q in enumerate(questions)],
                style="margin-bottom:24px; border-bottom:1px solid var(--border); padding-bottom:16px;",
            )

        quiz_form = ""
        if not quiz:
            quiz_form = Div(
                H3("Create quiz for this lesson", style="font-size:14px; color:var(--ink-muted); margin-bottom:12px;"),
                Form(
                    Input(type="hidden", name="course_id", value=course_id),
                    Input(type="hidden", name="module_id", value=module_id),
                    Input(type="hidden", name="lesson_id", value=lesson_id),
                    Div(Label("Quiz Title", cls="form-label"), Input(name="title", cls="form-input", required=True, value=f"Quiz: {selected_lesson['title']}"), cls="form-group"),
                    Div(
                        Div(Label("Pass Threshold (%)", cls="form-label"), Input(name="pass_threshold", type="number", cls="form-input", value="70"), cls="form-group"),
                        Div(Label("XP Reward", cls="form-label"), Input(name="xp_reward", type="number", cls="form-input", value="50"), cls="form-group"),
                        style="display:grid; grid-template-columns:1fr 1fr; gap:12px;",
                    ),
                    Button("Create Quiz", cls="btn btn-primary", type="submit"),
                    method="post",
                    action="/app/configure/create-quiz",
                ),
            )
        else:
            quiz_form = Div(
                existing_q,
                H3("Add question", style="font-size:14px; color:var(--ink-muted); margin-bottom:12px;"),
                Form(
                    Input(type="hidden", name="course_id", value=course_id),
                    Input(type="hidden", name="module_id", value=module_id),
                    Input(type="hidden", name="lesson_id", value=lesson_id),
                    Input(type="hidden", name="quiz_id", value=str(quiz["id"])),
                    Div(Label("Question", cls="form-label"), Textarea(name="question_text", cls="form-input", rows=2, required=True, placeholder="What is the capital of France?"), cls="form-group"),
                    Div(Label("Option A", cls="form-label"), Input(name="option_a", cls="form-input", required=True), cls="form-group"),
                    Div(Label("Option B", cls="form-label"), Input(name="option_b", cls="form-input", required=True), cls="form-group"),
                    Div(Label("Option C", cls="form-label"), Input(name="option_c", cls="form-input"), cls="form-group"),
                    Div(Label("Option D", cls="form-label"), Input(name="option_d", cls="form-input"), cls="form-group"),
                    Div(Label("Correct Answer (exact text of correct option)", cls="form-label"), Input(name="correct_answer", cls="form-input", required=True), cls="form-group"),
                    Div(Label("Explanation", cls="form-label"), Textarea(name="explanation", cls="form-input", rows=2, placeholder="Why this is the correct answer..."), cls="form-group"),
                    Button("Add Question", cls="btn btn-primary", type="submit"),
                    method="post",
                    action="/app/configure/create-question",
                ),
            )

        body = Div(
            A(f"← Back to lessons", href=f"/app/configure?step=3&course_id={course_id}&module_id={module_id}", style="font-size:13px; color:var(--ink-muted);"),
            H2(f"Quiz for: {selected_lesson['title']}", style="font-size:18px; margin:12px 0 16px;"),
            quiz_form,
        )

    elif step == "5" and selected_course:
        with db.connect() as conn:
            modules = db.get_modules(conn, int(course_id))
            total_lessons = 0
            total_quizzes = 0
            for m in modules:
                ls = db.get_lessons(conn, m["id"])
                total_lessons += len(ls)
                for l in ls:
                    q = db.get_quiz_for_lesson(conn, l["id"])
                    if q:
                        total_quizzes += 1

        body = Div(
            A("← Back to course", href=f"/app/configure?step=2&course_id={course_id}", style="font-size:13px; color:var(--ink-muted);"),
            H2(f"Publish: {selected_course['title']}", style="font-size:18px; margin:12px 0 16px;"),
            Div(
                Div(Div(str(len(modules)), cls="dashboard-card-value"), Div("Modules", cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(str(total_lessons), cls="dashboard-card-value"), Div("Lessons", cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(str(total_quizzes), cls="dashboard-card-value"), Div("Quizzes", cls="dashboard-card-label"), cls="dashboard-card"),
                Div(
                    Div("Published" if selected_course["is_published"] else "Draft", cls="dashboard-card-value"),
                    Div("Status", cls="dashboard-card-label"),
                    cls="dashboard-card",
                ),
                cls="dashboard-grid",
                style="margin-bottom:24px;",
            ),
            (Form(
                Input(type="hidden", name="course_id", value=course_id),
                Button("Publish Course" if not selected_course["is_published"] else "Unpublish Course",
                       cls="btn btn-primary" if not selected_course["is_published"] else "btn btn-secondary",
                       type="submit"),
                method="post",
                action="/app/configure/toggle-publish",
            )),
        )

    content = Div(
        H1("Course Configuration", cls="page-title"),
        P("Create and configure courses step by step", cls="page-subtitle"),
        steps_bar,
        alert,
        body,
        cls="page-content configure-page",
    )
    return app_shell(content, user=user, active="configure")


@app.post("/app/configure/create-course")
async def create_course(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    title = form.get("title", "").strip()
    category = form.get("category", "").strip()
    difficulty = form.get("difficulty", "beginner")
    description = form.get("description", "").strip()

    if not title:
        return RedirectResponse("/app/configure?step=1&error=Title+is+required", status_code=303)

    import re
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    import sqlalchemy as sa
    with db.begin() as conn:
        existing = db.get_course(conn, slug)
        if existing:
            return RedirectResponse(f"/app/configure?step=1&error=Course+slug+'{slug}'+already+exists", status_code=303)
        conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.courses (title, slug, description, category, difficulty, instructor_id, is_published)
                VALUES (:t, :s, :d, :cat, :diff, :i, false)
            """),
            {"t": title, "s": slug, "d": description, "cat": category, "diff": difficulty, "i": user["id"]},
        )
        course = db.get_course(conn, slug)

    return RedirectResponse(f"/app/configure?step=2&course_id={course['id']}&msg=Course+created!", status_code=303)


@app.post("/app/configure/create-module")
async def create_module(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    order_idx = int(form.get("order_idx", "0"))

    if not title or not course_id:
        return RedirectResponse(f"/app/configure?step=2&course_id={course_id}&error=Title+is+required", status_code=303)

    import sqlalchemy as sa
    with db.begin() as conn:
        result = conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.modules (course_id, title, description, order_idx)
                VALUES (:c, :t, :d, :o) RETURNING id
            """),
            {"c": int(course_id), "t": title, "d": description, "o": order_idx},
        )
        module_id = result.scalar()

    return RedirectResponse(
        f"/app/configure?step=3&course_id={course_id}&module_id={module_id}&msg=Module+added!", status_code=303
    )


@app.post("/app/configure/create-lesson")
async def create_lesson(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")
    module_id = form.get("module_id", "")
    title = form.get("title", "").strip()
    content_md = form.get("content_md", "").strip()
    xp_reward = int(form.get("xp_reward", "25"))
    duration_min = int(form.get("duration_min", "15"))
    order_idx = int(form.get("order_idx", "0"))
    video_url = form.get("video_url", "").strip() or None

    if not title or not module_id:
        return RedirectResponse(
            f"/app/configure?step=3&course_id={course_id}&module_id={module_id}&error=Title+is+required",
            status_code=303,
        )

    import sqlalchemy as sa
    with db.begin() as conn:
        result = conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.lessons (module_id, title, content_md, xp_reward, duration_min, order_idx, video_url)
                VALUES (:m, :t, :c, :xp, :dur, :o, :v) RETURNING id
            """),
            {"m": int(module_id), "t": title, "c": content_md, "xp": xp_reward, "dur": duration_min, "o": order_idx, "v": video_url},
        )
        lesson_id = result.scalar()

    return RedirectResponse(
        f"/app/configure?step=3&course_id={course_id}&module_id={module_id}&msg=Lesson+added!",
        status_code=303,
    )


@app.post("/app/configure/create-quiz")
async def create_quiz(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")
    module_id = form.get("module_id", "")
    lesson_id = form.get("lesson_id", "")
    title = form.get("title", "").strip()
    pass_threshold = int(form.get("pass_threshold", "70"))
    xp_reward = int(form.get("xp_reward", "50"))

    import sqlalchemy as sa
    with db.begin() as conn:
        conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.quizzes (lesson_id, title, pass_threshold, xp_reward)
                VALUES (:l, :t, :p, :xp)
            """),
            {"l": int(lesson_id), "t": title, "p": pass_threshold, "xp": xp_reward},
        )

    return RedirectResponse(
        f"/app/configure?step=4&course_id={course_id}&module_id={module_id}&lesson_id={lesson_id}&msg=Quiz+created!+Now+add+questions.",
        status_code=303,
    )


@app.post("/app/configure/create-question")
async def create_question(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")
    module_id = form.get("module_id", "")
    lesson_id = form.get("lesson_id", "")
    quiz_id = form.get("quiz_id", "")
    question_text = form.get("question_text", "").strip()
    option_a = form.get("option_a", "").strip()
    option_b = form.get("option_b", "").strip()
    option_c = form.get("option_c", "").strip()
    option_d = form.get("option_d", "").strip()
    correct_answer = form.get("correct_answer", "").strip()
    explanation = form.get("explanation", "").strip()

    options = [o for o in [option_a, option_b, option_c, option_d] if o]

    import sqlalchemy as sa
    with db.begin() as conn:
        count = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.quiz_questions WHERE quiz_id = :q"), {"q": int(quiz_id)}
        ).scalar()
        conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.quiz_questions (quiz_id, question_text, options, correct_answer, explanation, order_idx)
                VALUES (:q, :qt, :opts, :ca, :ex, :o)
            """),
            {"q": int(quiz_id), "qt": question_text, "opts": json.dumps(options), "ca": correct_answer, "ex": explanation, "o": count},
        )

    return RedirectResponse(
        f"/app/configure?step=4&course_id={course_id}&module_id={module_id}&lesson_id={lesson_id}&msg=Question+added!",
        status_code=303,
    )


@app.post("/app/configure/toggle-publish")
async def toggle_publish(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")

    import sqlalchemy as sa
    with db.begin() as conn:
        course = conn.execute(
            sa.text(f"SELECT * FROM {db.S}.courses WHERE id = :c"), {"c": int(course_id)}
        ).mappings().first()
        new_state = not course["is_published"]
        conn.execute(
            sa.text(f"UPDATE {db.S}.courses SET is_published = :p WHERE id = :c"),
            {"p": new_state, "c": int(course_id)},
        )

    action = "Published" if new_state else "Unpublished"
    return RedirectResponse(f"/app/configure?step=5&course_id={course_id}&msg=Course+{action}!", status_code=303)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
# School administration (frappe/education layer): students, programmes,
# gradebook, attendance and fees — on top of FastLMS's course-delivery core.
# ---------------------------------------------------------------------------

_SCHOOL_CSS = Style("""
.sch-kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:16px 0 24px;}
.sch-kpi{background:var(--surface,#fff);border:1px solid var(--line,#e2e8f0);border-radius:12px;padding:16px;}
.sch-kpi-value{font-size:26px;font-weight:700;}
.sch-kpi-label{font-size:12px;color:var(--ink-muted,#64748b);text-transform:uppercase;letter-spacing:.4px;margin-top:4px;}
.sch-bar{height:8px;background:var(--line,#e2e8f0);border-radius:4px;overflow:hidden;min-width:90px;}
.sch-bar>span{display:block;height:100%;background:var(--accent,#f59e0b);}
.status-pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:600;}
.status-paid{background:#dcfce7;color:#166534;} .status-overdue{background:#fee2e2;color:#991b1b;}
.status-unpaid{background:#f1f5f9;color:#475569;} .status-partly{background:#fef3c7;color:#92400e;}
.sch-seg{display:inline-flex;gap:6px;margin-bottom:14px;flex-wrap:wrap;}
.sch-seg a{padding:6px 12px;border:1px solid var(--line,#e2e8f0);border-radius:8px;font-size:13px;text-decoration:none;color:inherit;}
.sch-seg a.active{background:var(--accent,#f59e0b);color:#fff;}
""")


def _school_guard(req):
    user, redir = _require_login(req)
    if redir:
        return None, redir
    if user["role"] not in ("instructor", "admin"):
        return None, RedirectResponse("/app", status_code=303)
    return user, None


def _kpi(label, value):
    return Div(Div(str(value), cls="sch-kpi-value"), Div(label, cls="sch-kpi-label"), cls="sch-kpi")


def _fee_pill(status):
    cls = {"Paid": "status-paid", "Overdue": "status-overdue", "Unpaid": "status-unpaid",
           "Partly Paid": "status-partly"}.get(status, "status-unpaid")
    return Span(status, cls=f"status-pill {cls}")


@app.get("/app/school")
def school_overview(req):
    user, redir = _school_guard(req)
    if redir:
        return redir
    with db.connect() as conn:
        k = school.school_kpis(conn)
        progs = school.list_programs(conn)
        fees = school.fees_summary(conn)
    prog_rows = [Tr(Td(p["name"]), Td(str(p["students"])), Td(str(p["courses"]))) for p in progs]
    fee_rows = [Tr(Td(_fee_pill(f["status"])), Td(str(f["n"])), Td(f"£{float(f['outstanding']):,.0f}")) for f in fees]
    content = Div(
        _SCHOOL_CSS,
        H1("School Overview", cls="page-title"),
        Div(_kpi("Students", k["students"]), _kpi("Programmes", k["programs"]),
            _kpi("Attendance (30d)", f"{k['attendance_rate']}%"),
            _kpi("Fees outstanding", f"£{k['fees_outstanding']:,.0f}"), cls="sch-kpi-grid"),
        H2("Programmes", style="margin-top:8px;"),
        Table(Thead(Tr(Th("Programme"), Th("Students"), Th("Courses"))), Tbody(*prog_rows), cls="manage-table"),
        H2("Fees by status", style="margin-top:24px;"),
        Table(Thead(Tr(Th("Status"), Th("Invoices"), Th("Outstanding"))), Tbody(*fee_rows), cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="school")


@app.get("/app/school/students")
def school_students(req):
    user, redir = _school_guard(req)
    if redir:
        return redir
    q = req.query_params.get("q", "").strip()
    with db.connect() as conn:
        studs = school.list_students(conn, q=q or None)
    rows = [Tr(Td(A(f"{s['first_name']} {s['last_name']}", href=f"/app/school/student/{s['id']}")),
               Td(s["code"]), Td(s.get("group_name") or "—"), Td(s.get("email") or "—"))
            for s in studs]
    content = Div(
        _SCHOOL_CSS,
        H1("Students", cls="page-title"),
        Form(Input(type="search", name="q", value=q, placeholder="Search students…",
                   cls="search-input", style="max-width:320px;"),
             method="get", action="/app/school/students", style="margin-bottom:14px;"),
        Table(Thead(Tr(Th("Name"), Th("Code"), Th("Group"), Th("Email"))),
              Tbody(*rows) if rows else Tbody(Tr(Td("No students.", colspan="4"))), cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="students")


@app.get("/app/school/student/{sid:int}")
def school_student_detail(req, sid: int):
    user, redir = _school_guard(req)
    if redir:
        return redir
    with db.connect() as conn:
        s = school.student_detail(conn, sid)
        if not s:
            return app_shell(Div(H1("Student not found", cls="page-title"), cls="page-content"), user=user, active="students")
        guardians = school.student_guardians(conn, sid)
        grades = school.student_grades(conn, sid)
        att = school.student_attendance(conn, sid)
        fees = school.student_fees(conn, sid)
    present = sum(1 for a in att if a["status"] == "Present")
    att_pct = round(100 * present / len(att)) if att else 0
    grade_rows = [Tr(Td(g["name"]), Td(g.get("course") or "—"),
                     Td(f"{g['score']:.0f}/{g['max_score']:.0f}"), Td(Span(g["grade"] or "—"))) for g in grades]
    fee_rows = [Tr(Td(f.get("category") or "Fee"), Td(f"£{float(f['amount']):,.0f}"),
                   Td(f"£{float(f['paid']):,.0f}"), Td(_fee_pill(f["status"]))) for f in fees]
    content = Div(
        _SCHOOL_CSS,
        A("← Students", href="/app/school/students", cls="btn btn-sm"),
        H1(f"{s['first_name']} {s['last_name']}", cls="page-title"),
        P(f"{s['code']} · {s.get('group_name') or '—'} · {s.get('program_name') or '—'}", style="color:var(--ink-muted,#64748b);"),
        Div(_kpi("Attendance", f"{att_pct}%"), _kpi("Assessments", len(grades)),
            _kpi("Guardians", len(guardians)), cls="sch-kpi-grid", style="grid-template-columns:repeat(3,1fr);"),
        H2("Grades"),
        Table(Thead(Tr(Th("Assessment"), Th("Course"), Th("Score"), Th("Grade"))),
              Tbody(*grade_rows) if grade_rows else Tbody(Tr(Td("No grades.", colspan="4"))), cls="manage-table"),
        H2("Fees", style="margin-top:20px;"),
        Table(Thead(Tr(Th("Category"), Th("Amount"), Th("Paid"), Th("Status"))),
              Tbody(*fee_rows) if fee_rows else Tbody(Tr(Td("No fees.", colspan="4"))), cls="manage-table"),
        H2("Guardians", style="margin-top:20px;"),
        Table(Thead(Tr(Th("Name"), Th("Relation"), Th("Email"), Th("Phone"))),
              Tbody(*[Tr(Td(g["name"]), Td(g.get("relation") or "—"), Td(g.get("email") or "—"), Td(g.get("phone") or "—")) for g in guardians]),
              cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="students")


@app.get("/app/school/programs")
def school_programs(req):
    user, redir = _school_guard(req)
    if redir:
        return redir
    with db.connect() as conn:
        progs = school.list_programs(conn)
        groups = school.list_groups(conn)
    prog_rows = [Tr(Td(p["name"]), Td(p.get("description") or "—"), Td(str(p["students"])), Td(str(p["courses"]))) for p in progs]
    grp_rows = [Tr(Td(g["name"]), Td(g.get("program_name") or "—"), Td(g.get("term_name") or "—"), Td(str(g["students"]))) for g in groups]
    content = Div(
        _SCHOOL_CSS,
        H1("Programmes", cls="page-title"),
        Table(Thead(Tr(Th("Programme"), Th("Description"), Th("Students"), Th("Courses"))), Tbody(*prog_rows), cls="manage-table"),
        H2("Student groups", style="margin-top:24px;"),
        Table(Thead(Tr(Th("Group"), Th("Programme"), Th("Term"), Th("Students"))), Tbody(*grp_rows), cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="programs")


@app.get("/app/school/gradebook")
def school_gradebook(req):
    user, redir = _school_guard(req)
    if redir:
        return redir
    with db.connect() as conn:
        groups = school.list_groups(conn)
        gid = int(req.query_params.get("group", groups[0]["id"] if groups else 0) or 0)
        gb = school.gradebook(conn, gid) if gid else []
    seg = Div(*[A(g["name"], href=f"/app/school/gradebook?group={g['id']}",
                  cls="active" if g["id"] == gid else "") for g in groups], cls="sch-seg")
    rows = []
    for r in gb:
        pct = r["avg_pct"] or 0
        rows.append(Tr(Td(f"{r['first_name']} {r['last_name']}"),
                       Td(Div(Div(Span(style=f"width:{pct}%;"), cls="sch-bar"), f"{pct:.0f}%",
                              style="display:flex;align-items:center;gap:8px;")),
                       Td(str(r["n"]))))
    content = Div(
        _SCHOOL_CSS,
        H1("Gradebook", cls="page-title"),
        seg,
        Table(Thead(Tr(Th("Student"), Th("Average"), Th("Assessments"))),
              Tbody(*rows) if rows else Tbody(Tr(Td("No data.", colspan="3"))), cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="gradebook")


@app.get("/app/school/attendance")
def school_attendance(req):
    user, redir = _school_guard(req)
    if redir:
        return redir
    with db.connect() as conn:
        groups = school.list_groups(conn)
        gid = int(req.query_params.get("group", groups[0]["id"] if groups else 0) or 0)
        reg = school.attendance_register(conn, gid) if gid else []
    seg = Div(*[A(g["name"], href=f"/app/school/attendance?group={g['id']}",
                  cls="active" if g["id"] == gid else "") for g in groups], cls="sch-seg")
    rows = []
    for r in reg:
        total = r["total"] or 0
        pct = round(100 * (r["present"] or 0) / total) if total else 0
        rows.append(Tr(Td(f"{r['first_name']} {r['last_name']}"), Td(str(r["present"] or 0)),
                       Td(str(r["absent"] or 0)), Td(f"{pct}%")))
    content = Div(
        _SCHOOL_CSS,
        H1("Attendance", cls="page-title"),
        seg,
        Table(Thead(Tr(Th("Student"), Th("Present"), Th("Absent"), Th("Rate"))),
              Tbody(*rows) if rows else Tbody(Tr(Td("No data.", colspan="4"))), cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="attendance")


@app.get("/app/school/fees")
def school_fees(req):
    user, redir = _school_guard(req)
    if redir:
        return redir
    with db.connect() as conn:
        summary = school.fees_summary(conn)
        fees = school._all(conn, f"""
            SELECT f.*, s.first_name, s.last_name, fs.category FROM {school.S}.fees f
            JOIN {school.S}.students s ON s.id = f.student_id
            LEFT JOIN {school.S}.fee_structures fs ON fs.id = f.fee_structure_id
            ORDER BY (f.status='Paid'), f.due_date LIMIT 200""")
    sum_rows = [Tr(Td(_fee_pill(x["status"])), Td(str(x["n"])), Td(f"£{float(x['outstanding']):,.0f}")) for x in summary]
    fee_rows = [Tr(Td(f"{f['first_name']} {f['last_name']}"), Td(f.get("category") or "Fee"),
                   Td(f"£{float(f['amount']):,.0f}"), Td(f"£{float(f['paid']):,.0f}"),
                   Td(f"£{float(f['amount'])-float(f['paid']):,.0f}"), Td(_fee_pill(f["status"]))) for f in fees]
    content = Div(
        _SCHOOL_CSS,
        H1("Fees", cls="page-title"),
        Table(Thead(Tr(Th("Status"), Th("Invoices"), Th("Outstanding"))), Tbody(*sum_rows), cls="manage-table"),
        H2("All fees", style="margin-top:24px;"),
        Table(Thead(Tr(Th("Student"), Th("Category"), Th("Amount"), Th("Paid"), Th("Outstanding"), Th("Status"))),
              Tbody(*fee_rows), cls="manage-table"),
        cls="page-content")
    return app_shell(content, user=user, active="fees")


# ---------------------------------------------------------------------------

@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Bootstrap & run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    args = parser.parse_args()

    print("Bootstrapping database schema...")
    db.bootstrap_schema()
    print(f"Starting FastLMS on http://{args.host}:{args.port}")
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
