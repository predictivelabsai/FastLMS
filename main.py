"""FastLMS — FastHTML learning management system with gamification and AI tutor.

3-pane layout (left nav / center content / right canvas), SSE streaming chat,
PostgreSQL backend, XP + streaks + badges + leaderboard gamification.

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
                    "Open-source learning platform with AI tutoring, gamification, and real-time progress tracking.",
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
# Health check
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
