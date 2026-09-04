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
import html
import json
import os
import secrets
from datetime import datetime, timezone

from dotenv import load_dotenv
from fasthtml.common import *
from starlette.responses import StreamingResponse

load_dotenv()

import db
import language_learning as languages
import school
from components.layout import (
    app_shell,
    auth_page,
    badge_card,
    course_card,
    progress_bar,
    xp_popup,
)
from components.landing import landing_page
from components.i18n import (
    SUPPORTED_LANGS,
    get_lang,
    is_fastlearn_host,
    localize_record,
    prompt_language_directive,
    safe_return_path,
    t,
)
from components.seo import register_seo_routes
from components.developer import developer_page
from components import account_auth, google_auth
from components.api import api

app = FastHTML(
    hdrs=[],
    static_path="static",
    secret_key=os.environ.get("SESSION_SECRET", "fastlms-dev-secret-change-me"),
)
app.mount("/api", api)


@app.get("/swagger.json")
def swagger_schema():
    return JSONResponse(api.openapi())


@app.get("/developers")
def developers():
    return developer_page()


def establish_local_account(session, account):
    import sqlalchemy as sa
    with db.begin() as conn:
        user = db.get_user_by_email(conn, account["email"])
        if not user:
            conn.execute(
                sa.text(f"INSERT INTO {db.S}.users (email, password_hash, display_name, role) VALUES (:e, :p, :n, :r)"),
                {"e": account["email"], "p": _hash_pw(os.urandom(32).hex()), "n": account["name"],
                 "r": db.role_for_email(account["email"], account.get("role", "student"))},
            )
            user = db.get_user_by_email(conn, account["email"])
    session["user_id"] = user["id"]


account_auth.register_fastapi_routes(
    app, app_name="FastLearn", success_path="/app", on_login=establish_local_account
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


def _require_teacher(req):
    user, redir = _require_login(req)
    if redir:
        return None, redir
    if user.get("role") not in ("teacher", "instructor", "admin"):
        return None, RedirectResponse("/app", status_code=303)
    return user, None


def _can_manage_or_redirect(user, course_id: int):
    with db.connect() as conn:
        allowed = db.can_manage_course(conn, user, int(course_id))
    return None if allowed else RedirectResponse("/app/manage", status_code=303)


def _consume_invitation(conn, token_hash: str, user: dict) -> bool:
    import sqlalchemy as sa
    invite = conn.execute(sa.text(f"""
        SELECT * FROM {db.S}.invitations
        WHERE token_hash = :token AND consumed_at IS NULL AND revoked_at IS NULL
    """), {"token": token_hash}).mappings().first()
    if not invite or invite["email"].lower() != user["email"].lower():
        return False
    role = db.role_for_email(user["email"], invite["role"])
    conn.execute(sa.text(f"UPDATE {db.S}.users SET role = :role WHERE id = :user"),
                 {"role": role, "user": user["id"]})
    conn.execute(sa.text(f"UPDATE {db.S}.invitations SET consumed_at = now() WHERE id = :id"),
                 {"id": invite["id"]})
    db.audit(conn, actor_id=user["id"], action="invitation.accepted", target_type="invitation",
             target_id=invite["id"], details={"role": role})
    return True


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
    return landing_page(get_lang(req), product=is_fastlearn_host(req))


@app.get("/fastlms")
def fastlms_reference(req):
    """Stable route for open-source landing capture and review."""
    return landing_page(get_lang(req), product=False)


@app.get("/fastlearn")
def fastlearn_reference(req):
    """Stable route for FastLearn product landing capture and review."""
    return landing_page(get_lang(req), product=True)


@app.get("/set-lang")
def set_language(req, lang: str = "en", next: str = "/"):
    lang = lang if lang in SUPPORTED_LANGS else "en"
    req.session["lang"] = lang
    response = RedirectResponse(safe_return_path(next), status_code=303)
    response.set_cookie("language", lang, max_age=365 * 24 * 3600, samesite="lax", secure=True)
    return response


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.get("/auth/login")
def login_page(req):
    lang = get_lang(req)
    error = req.query_params.get("error", "")
    return auth_page(
        Div(
            H2(t("sign_in", lang).title(), cls="auth-title"),
            (Div(error, cls="form-error") if error else ""),
            account_auth.google_button(t("continue_google", lang)),
            Div("or", cls="auth-divider"),
            Form(
                Div(Label(t("email", lang), cls="form-label"), Input(name="email", type="email", cls="form-input", required=True), cls="form-group"),
                Div(Label(t("password", lang), cls="form-label"), Input(name="password", type="password", cls="form-input", required=True), cls="form-group"),
                Button(t("sign_in", lang), cls="btn btn-primary btn-block", type="submit"),
                method="post",
                action="/auth/login",
            ),
            Div(A(t("create_account", lang), href="/auth/register"), cls="auth-footer"),
            cls="auth-box",
        ), lang=lang,
    )


@app.get("/auth/google")
def google_start(req):
    if not google_auth.enabled():
        return RedirectResponse("/auth/login?error=Google+sign-in+is+not+configured", status_code=303)
    state = google_auth.new_state()
    req.session["google_oauth_state"] = state
    req.session.pop("pending_signup_role", None)
    requested_role = str(req.query_params.get("role", "")).strip().lower()
    if requested_role in account_auth.SIGNUP_ROLES:
        req.session["pending_signup_role"] = requested_role
    invite = req.query_params.get("invite", "")
    if invite:
        req.session["pending_invite_hash"] = hashlib.sha256(invite.encode()).hexdigest()
    return RedirectResponse(google_auth.authorize_url(req, state), status_code=303)


@app.get("/auth/google/callback")
def google_callback(req, code: str = "", state: str = "", error: str = ""):
    if error or not code or state != req.session.pop("google_oauth_state", None):
        return RedirectResponse("/auth/login?error=Google+sign-in+failed", status_code=303)
    signup_role = account_auth.normalize_signup_role(req.session.pop("pending_signup_role", "student"))
    identity = google_auth.exchange(req, code)
    if not identity:
        return RedirectResponse("/auth/login?error=Google+account+is+not+authorised", status_code=303)
    account_auth.accounts.link_google(identity["email"], identity["name"])
    import sqlalchemy as sa
    with db.begin() as conn:
        user = db.get_user_by_email(conn, identity["email"])
        if not user:
            conn.execute(
                sa.text(f"INSERT INTO {db.S}.users (email, password_hash, display_name, role) VALUES (:e, :p, :n, :r)"),
                {"e": identity["email"], "p": _hash_pw(os.urandom(32).hex()), "n": identity["name"],
                 "r": db.role_for_email(identity["email"], signup_role)},
            )
            user = db.get_user_by_email(conn, identity["email"])
        pending_invite = req.session.pop("pending_invite_hash", "")
        if pending_invite:
            _consume_invitation(conn, pending_invite, user)
    req.session["user_id"] = user["id"]
    return RedirectResponse("/app", status_code=303)


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
    lang = get_lang(req)
    error = req.query_params.get("error", "")
    return auth_page(
        Div(
            H2(t("create_account", lang), cls="auth-title"),
            (Div(error, cls="form-error") if error else ""),
            Form(
                account_auth.signup_role_picker(lang),
                account_auth.google_button(
                    t("continue_google", lang), href="/auth/google?role=student",
                    onclick=account_auth.GOOGLE_SIGNUP_ONCLICK,
                ),
                Div("or", cls="auth-divider"),
                Div(Label("Display name", cls="form-label"), Input(name="display_name", cls="form-input", required=True), cls="form-group"),
                Div(Label(t("email", lang), cls="form-label"), Input(name="email", type="email", cls="form-input", required=True), cls="form-group"),
                Div(Label(t("password", lang), cls="form-label"), Input(name="password", type="password", cls="form-input", required=True, minlength=6), cls="form-group"),
                Button(t("create_account", lang), cls="btn btn-primary btn-block", type="submit"),
                method="post",
                action="/auth/register",
            ),
            Div(A(t("sign_in", lang), href="/auth/login"), cls="auth-footer"),
            cls="auth-box",
        ), lang=lang,
    )


@app.post("/auth/register")
async def register_post(req):
    form = await req.form()
    name = form.get("display_name", "").strip()
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    role = str(form.get("role", "")).strip().lower()
    if not name or not email or len(password) < 6 or role not in account_auth.SIGNUP_ROLES:
        return RedirectResponse("/auth/register?error=All+fields+required+and+password+min+6+chars", status_code=303)
    with db.begin() as conn:
        existing = db.get_user_by_email(conn, email)
        if existing:
            return RedirectResponse("/auth/register?error=Email+already+registered", status_code=303)
        import sqlalchemy as sa
        conn.execute(
            sa.text(f"INSERT INTO {db.S}.users (email, password_hash, display_name, role) VALUES (:e, :p, :n, :r)"),
            {"e": email, "p": _hash_pw(password), "n": name, "r": db.role_for_email(email, role)},
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
    lang = get_lang(req)

    with db.connect() as conn:
        courses = db.get_courses(conn, lang=lang)
        import sqlalchemy as sa
        lessons_done = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.lesson_progress WHERE user_id = :u AND status = 'completed'"),
            {"u": user["id"]},
        ).scalar()
        badges = db.get_user_badges(conn, user["id"], lang=lang)
        enrolments = conn.execute(
            sa.text(f"SELECT course_id FROM {db.S}.enrolments WHERE user_id = :u"),
            {"u": user["id"]},
        ).mappings().all()
        enrolled_ids = {e["course_id"] for e in enrolments}
        assigned_ids = db.get_assigned_course_ids(conn, user["id"])

        my_courses = []
        for c in courses:
            if c["id"] in enrolled_ids:
                prog = db.get_user_course_progress(conn, user["id"], c["id"])
                my_courses.append((c, prog))

    content = Div(
        Div(
            H1(t("welcome_back", lang, name=user["display_name"]), cls="page-title"),
            P(t("learning_dashboard", lang), cls="page-subtitle"),

            Div(
                Div(Div(str(user["xp"]), cls="dashboard-card-value"), Div(t("total_xp", lang), cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(user["level"], cls="dashboard-card-value"), Div(t("level", lang), cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(f"{user['streak_days']}d", cls="dashboard-card-value"), Div(t("streak", lang), cls="dashboard-card-label"), cls="dashboard-card"),
                Div(Div(str(lessons_done), cls="dashboard-card-value"), Div(t("lessons_done", lang), cls="dashboard-card-label"), cls="dashboard-card"),
                cls="dashboard-grid",
            ),

            (Div(
                H2(t("my_courses", lang), style="font-size:18px; font-weight:600; margin-bottom:16px;"),
                Div(*[course_card(c, prog, lang, assigned=c["id"] in assigned_ids) for c, prog in my_courses], cls="courses-grid"),
                style="margin-bottom:32px;",
            ) if my_courses else ""),

            (Div(
                H2(t("my_badges", lang), style="font-size:18px; font-weight:600; margin-bottom:16px;"),
                Div(*[badge_card(b) for b in badges], cls="badges-grid"),
                style="margin-bottom:32px;",
            ) if badges else ""),

            (Div(
                H2(t("courses", lang), style="font-size:18px; font-weight:600; margin-bottom:16px;"),
                Div(*[course_card(c, lang=lang, assigned=c["id"] in assigned_ids) for c in courses if c["id"] not in enrolled_ids], cls="courses-grid"),
            ) if any(c["id"] not in enrolled_ids for c in courses) else ""),

            cls="page-content",
        ),
    )
    return app_shell(content, user=user, active="dashboard", lang=lang, current_path="/app")


# ---------------------------------------------------------------------------
# Courses list
# ---------------------------------------------------------------------------

@app.get("/app/courses")
def courses_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    lang = get_lang(req)
    with db.connect() as conn:
        courses = db.get_courses(conn, lang=lang)
        import sqlalchemy as sa
        enrolments = conn.execute(
            sa.text(f"SELECT course_id FROM {db.S}.enrolments WHERE user_id = :u"),
            {"u": user["id"]},
        ).mappings().all()
        enrolled_ids = {e["course_id"] for e in enrolments}
        assigned_ids = db.get_assigned_course_ids(conn, user["id"])

        cards = []
        for c in courses:
            prog = db.get_user_course_progress(conn, user["id"], c["id"]) if c["id"] in enrolled_ids else None
            cards.append(course_card(c, prog, lang, assigned=c["id"] in assigned_ids))

    content = Div(
        H1(t("courses", lang), cls="page-title"),
        P(t("browse_all_courses", lang), cls="page-subtitle"),
        Div(*cards, cls="courses-grid") if cards else Div(
            Div(t("no_courses", lang), cls="empty-state-text"),
            cls="empty-state",
        ),
        cls="page-content",
    )
    return app_shell(content, user=user, active="courses", lang=lang, current_path="/app/courses")


# ---------------------------------------------------------------------------
# Course detail + lesson navigation
# ---------------------------------------------------------------------------

@app.get("/app/course/{slug}")
def course_detail(req, slug: str):
    user, redir = _require_login(req)
    if redir:
        return redir

    lang = get_lang(req)
    with db.connect() as conn:
        course = db.get_course(conn, slug, lang=lang)
        if not course:
            return Response("Course not found", status_code=404)

        modules = db.get_modules(conn, course["id"], lang=lang)
        import sqlalchemy as sa
        enrolled = conn.execute(
            sa.text(f"SELECT 1 FROM {db.S}.enrolments WHERE user_id = :u AND course_id = :c"),
            {"u": user["id"], "c": course["id"]},
        ).scalar()
        prog = db.get_user_course_progress(conn, user["id"], course["id"])
        assigned = course["id"] in db.get_assigned_course_ids(conn, user["id"])
        learning_path = db.get_learning_path(conn, user_id=user["id"], course_id=course["id"], lang=lang)
        recommendations = conn.execute(sa.text(f"""
            SELECT * FROM {db.S}.adaptive_recommendations
            WHERE user_id = :user AND course_id = :course AND status = 'pending'
            ORDER BY created_at DESC LIMIT 3
        """), {"user": user["id"], "course": course["id"]}).mappings().all()

        sidebar_items = []
        first_lesson_id = None
        current_module = object()
        module_names = {m["id"]: m["title"] for m in modules}
        for les in learning_path:
            if les["module_id"] != current_module:
                current_module = les["module_id"]
                sidebar_items.append(Div(module_names.get(current_module, les.get("module_title", "")), cls="module-header"))
            if first_lesson_id is None:
                first_lesson_id = les["id"]
            lp = db.get_lesson_progress(conn, user["id"], les["id"])
            done = lp and lp["status"] == "completed"
            cls = "lesson-list-item" + (" completed" if done else "")
            check_cls = "lesson-check" + (" done" if done else "")
            kind = les.get("lesson_kind", "core")
            sidebar_items.append(
                A(
                    Span("✓" if done else "", cls=check_cls),
                    Span(les["title"]),
                    (Span(t(kind, lang), cls=f"lesson-kind lesson-kind-{kind}") if kind != "core" else ""),
                    href=f"/app/lesson/{les['id']}",
                    cls=cls,
                )
            )

    hero = Div(
        Div(
            H1(course["title"]),
            P(course.get("description", "")),
            Div(
                Span(f"{t('difficulty', lang)}: {t(course.get('difficulty', 'beginner'), lang)}"),
                Span(f"{t('progress', lang)}: {prog['percent']}%"),
                (Span(t("assigned", lang), cls="course-assigned") if assigned else ""),
                cls="course-hero-meta",
            ),
            (Form(
                Button(t("enrol", lang), cls="btn btn-primary", type="submit", style="margin-top:16px;"),
                method="post",
                action=f"/app/course/{slug}/enrol",
            ) if not enrolled else ""),
            cls="course-hero-inner",
        ),
        cls="course-hero",
    )

    recommendation_notices = Div(*[
        Div(
            Strong(t("recommended_review", lang) if r["recommendation_type"] == "remedial" else t("ready_extension", lang)),
            P(r.get("reason") or ""),
            cls="adaptive-notice",
        ) for r in recommendations
    ], cls="adaptive-notices") if recommendations else ""
    body = Div(
        Div(*sidebar_items, cls="course-sidebar") if sidebar_items else "",
        Div(
            recommendation_notices,
            progress_bar(prog["percent"], f"{prog['completed']}/{prog['total']} {t('lessons', lang)}"),
            Div(
                P(t("select_lesson", lang), style="color:var(--ink-muted); margin-top:24px;"),
                cls="lesson-placeholder",
            ),
        ),
        cls="course-body",
    )

    content = Div(hero, body)
    return app_shell(content, user=user, active="courses", title=course["title"], lang=lang, current_path=f"/app/course/{slug}")


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

    lang = get_lang(req)
    import markdown as md
    import sqlalchemy as sa

    with db.connect() as conn:
        lesson = db.get_lesson(conn, lesson_id, lang=lang)
        if not lesson:
            return Response("Lesson not found", status_code=404)

        module = conn.execute(sa.text(f"SELECT * FROM {db.S}.modules WHERE id = :m"), {"m": lesson["module_id"]}).mappings().first()
        module = localize_record(dict(module), "modules", lang)
        course = conn.execute(sa.text(f"SELECT * FROM {db.S}.courses WHERE id = :c"), {"c": module["course_id"]}).mappings().first()
        course = localize_record(dict(course), "courses", lang)

        lp = db.get_lesson_progress(conn, user["id"], lesson_id)
        is_done = lp and lp["status"] == "completed"

        quiz = db.get_quiz_for_lesson(conn, lesson_id, lang=lang)
        discussions = db.get_discussions(conn, lesson_id)

        path = db.get_learning_path(conn, user_id=user["id"], course_id=course["id"], lang=lang)
        path_ids = [item["id"] for item in path]
        current_index = path_ids.index(lesson_id) if lesson_id in path_ids else -1
        next_lesson = path_ids[current_index + 1] if 0 <= current_index < len(path_ids) - 1 else None

    content_html = md.markdown(lesson.get("content_md") or "", extensions=["fenced_code", "tables", "nl2br"])

    video_embed = ""
    if lesson.get("video_url"):
        video_embed = Iframe(src=lesson["video_url"], cls="lesson-video", allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture", allowfullscreen=True)

    actions = []
    if not is_done:
        actions.append(
            Form(
                Button(t("mark_complete", lang), cls="btn btn-green", type="submit"),
                method="post",
                action=f"/app/lesson/{lesson_id}/complete",
            )
        )
    else:
        actions.append(Span(t("completed", lang), cls="btn btn-secondary", style="opacity:0.6;"))

    if quiz:
        actions.append(A(t("take_quiz", lang), href=f"/app/quiz/{quiz['id']}", cls="btn btn-blue"))

    actions.append(A(t("ai_tutor", lang), href=f"/app/chat?lesson_id={lesson_id}", cls="btn btn-secondary"))

    if next_lesson:
        actions.append(A(t("next_lesson", lang), href=f"/app/lesson/{next_lesson}", cls="btn btn-secondary"))

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
            Span(t(lesson.get("lesson_kind", "core"), lang)),
            cls="lesson-meta",
        ),
        video_embed,
        Div(NotStr(content_html), cls="lesson-content"),
        Div(*actions, cls="lesson-actions"),
        cls="lesson-layout",
    )
    return app_shell(lesson_view, user=user, active="courses", title=lesson["title"], lang=lang, current_path=f"/app/lesson/{lesson_id}")


@app.post("/app/lesson/{lesson_id:int}/complete")
async def complete_lesson(req, lesson_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir
    with db.begin() as conn:
        xp = db.mark_lesson_complete(conn, user["id"], lesson_id)
        new_badges = db.check_and_award_badges(conn, user["id"])
    return RedirectResponse(f"/app/lesson/{lesson_id}?xp={xp}", status_code=303)


@app.post("/app/activity/heartbeat")
async def activity_heartbeat(req):
    """Record at most one visible, active 30-second learning interval."""
    user, redir = _require_login(req)
    if redir:
        return JSONResponse({"error": "authentication required"}, status_code=401)
    try:
        payload = await req.json()
        resource_type = str(payload.get("resource_type", ""))
        resource_id = payload.get("resource_id")
        seconds = int(payload.get("seconds", 0))
        if seconds < 1 or seconds > 30:
            raise ValueError
        with db.begin() as conn:
            course_id = db.record_learning_time(
                conn, user_id=user["id"], resource_type=resource_type,
                resource_id=resource_id, seconds=seconds,
            )
    except (TypeError, ValueError, json.JSONDecodeError):
        return JSONResponse({"error": "invalid heartbeat"}, status_code=400)
    return JSONResponse({"ok": True, "course_id": course_id})


# ---------------------------------------------------------------------------
# Native-to-target language learning
# ---------------------------------------------------------------------------

def _language_options(codes, selected):
    return [
        Option(languages.language_label(code), value=code, selected=code == selected)
        for code in codes
    ]


@app.get("/app/languages")
def language_learning_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir
    lang = get_lang(req)
    with db.connect() as conn:
        profile = db.get_language_profile(conn, user["id"])
        if not profile:
            native, target = languages.default_language_pair(lang)
            profile = {"native_language": native, "target_language": target, "daily_goal": 10}
            reviews = []
            stats = {"expressions_seen": 0, "mastered": 0, "due_now": 0, "reviewed_today": 0}
        else:
            reviews = db.get_language_reviews(
                conn, user_id=user["id"], target_language=profile["target_language"]
            )
            stats = db.get_language_stats(
                conn, user_id=user["id"], target_language=profile["target_language"]
            )
    cards = languages.build_session(
        reviews,
        native_language=profile["native_language"],
        target_language=profile["target_language"],
        limit=profile["daily_goal"],
    )
    target_meta = languages.LANGUAGE_META[profile["target_language"]]
    practice = Div(P(t("all_caught_up", lang), cls="language-caught-up"), cls="language-practice")
    if cards:
        card = cards[0]
        target = card["target"]
        native = card["native"]
        practice = Article(
            Div(
                Span(
                    t("due_now", lang) if card.get("review") else t("new_expression", lang),
                    cls="language-status due" if card.get("review") else "language-status new",
                ),
                Span(t("frequency_rank", lang, rank=card["rank"]), cls="language-rank"),
                cls="language-card-meta",
            ),
            P(t("practice_prompt", lang, language=target_meta["autonym"]), cls="language-prompt"),
            H2(
                native["text"],
                dir=languages.LANGUAGE_META[profile["native_language"]]["direction"],
                cls="language-native",
            ),
            Details(
                Summary(t("reveal_answer", lang), cls="btn btn-primary language-reveal"),
                Div(
                    H3(target["text"], dir=target_meta["direction"], cls="language-target"),
                    P(target.get("romanization", ""), cls="language-romanization") if target.get("romanization") else "",
                    Button(
                        f"🔊 {t('listen', lang)}",
                        type="button",
                        cls="btn btn-secondary language-listen",
                        data_speak=target["text"],
                        data_voice=target_meta["voice"],
                    ),
                    Div(*[
                        Form(
                            Input(type="hidden", name="concept_id", value=card["id"]),
                            Input(type="hidden", name="rating", value=rating),
                            Button(t(label, lang), type="submit", cls=f"recall-button recall-{rating}"),
                            method="post", action="/app/languages/review",
                        )
                        for rating, label in (("again", "recall_again"), ("hard", "recall_hard"), ("good", "recall_good"))
                    ], cls="recall-actions"),
                    cls="language-answer",
                ),
            ),
            cls="language-card",
        )
    content = Div(
        H1(t("language_learning_title", lang), cls="page-title"),
        P(t("language_learning_subtitle", lang), cls="page-subtitle"),
        (Div(t("language_pair_error", lang), cls="alert alert-error") if req.query_params.get("error") else ""),
        Div(
            Form(
                Div(
                    Label(t("native_language", lang), cls="form-label"),
                    Select(*_language_options(languages.NATIVE_LANGUAGE_CODES, profile["native_language"]), name="native_language", cls="form-input"),
                    cls="form-group",
                ),
                Div(
                    Label(t("target_language", lang), cls="form-label"),
                    Select(*_language_options(languages.TARGET_LANGUAGE_CODES, profile["target_language"]), name="target_language", cls="form-input"),
                    cls="form-group",
                ),
                Div(
                    Label(t("daily_goal", lang), cls="form-label"),
                    Input(name="daily_goal", type="number", min=5, max=50, value=profile["daily_goal"], cls="form-input"),
                    cls="form-group",
                ),
                Button(t("save_language_pair", lang), type="submit", cls="btn btn-primary"),
                method="post", action="/app/languages/preferences", cls="language-settings-form",
            ),
            Div(
                Div(Strong(str(stats["reviewed_today"])), Span(t("reviewed_today", lang)), cls="language-stat"),
                Div(Strong(str(stats["expressions_seen"])), Span(t("language_progress", lang)), cls="language-stat"),
                Div(Strong(str(stats["mastered"])), Span(t("mastered", lang)), cls="language-stat"),
                cls="language-stats",
            ),
            cls="language-top",
        ),
        Div(
            Div(H2(t("language_method_title", lang)), P(t("language_method_body", lang)), cls="language-method"),
            practice,
            cls="language-workspace",
        ),
        cls="page-content language-page",
    )
    return app_shell(
        content, user=user, active="languages", title=t("language_learning", lang),
        lang=lang, current_path="/app/languages",
    )


@app.post("/app/languages/preferences")
async def save_language_preferences(req):
    user, redir = _require_login(req)
    if redir:
        return redir
    form = await req.form()
    try:
        with db.begin() as conn:
            db.save_language_profile(
                conn,
                user_id=user["id"],
                native_language=str(form.get("native_language", "")),
                target_language=str(form.get("target_language", "")),
                daily_goal=int(form.get("daily_goal", 10)),
            )
    except (TypeError, ValueError):
        return RedirectResponse("/app/languages?error=pair", status_code=303)
    return RedirectResponse("/app/languages", status_code=303)


@app.post("/app/languages/review")
async def review_language_expression(req):
    user, redir = _require_login(req)
    if redir:
        return redir
    form = await req.form()
    try:
        with db.begin() as conn:
            profile = db.get_language_profile(conn, user["id"])
            if not profile:
                native, target = languages.default_language_pair(get_lang(req))
                profile = db.save_language_profile(
                    conn, user_id=user["id"], native_language=native,
                    target_language=target, daily_goal=10,
                )
            db.record_language_review(
                conn,
                user_id=user["id"],
                native_language=profile["native_language"],
                target_language=profile["target_language"],
                concept_id=str(form.get("concept_id", "")),
                rating=str(form.get("rating", "")),
            )
    except ValueError:
        return RedirectResponse("/app/languages?error=pair", status_code=303)
    return RedirectResponse("/app/languages", status_code=303)


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------

@app.get("/app/quiz/{quiz_id:int}")
def quiz_page(req, quiz_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir

    lang = get_lang(req)
    with db.connect() as conn:
        import sqlalchemy as sa
        quiz = conn.execute(sa.text(f"SELECT * FROM {db.S}.quizzes WHERE id = :q"), {"q": quiz_id}).mappings().first()
        if not quiz:
            return Response("Quiz not found", status_code=404)
        quiz = localize_record(dict(quiz), "quizzes", lang)
        learner_level = conn.execute(sa.text(f"""
            SELECT CASE WHEN cls.strategy = 'adaptive' THEN COALESCE(lcs.difficulty_level, 2) ELSE 2 END
            FROM {db.S}.quizzes q JOIN {db.S}.lessons l ON l.id=q.lesson_id
            JOIN {db.S}.modules m ON m.id=l.module_id
            LEFT JOIN {db.S}.course_learning_settings cls ON cls.course_id=m.course_id
            LEFT JOIN {db.S}.learner_course_state lcs ON lcs.course_id=m.course_id AND lcs.user_id=:user
            WHERE q.id=:quiz
        """), {"user": user["id"], "quiz": quiz_id}).scalar() or 2
        questions = db.get_quiz_questions(conn, quiz_id, lang=lang, learner_level=learner_level)
        lesson = db.get_lesson(conn, quiz["lesson_id"], lang=lang)

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
                Div(t("question", lang, number=i + 1), style="font-size:11px; color:var(--ink-dim); margin-bottom:8px;"),
                Div(q["question_text"], cls="quiz-question-text"),
                Div(*option_els, cls="quiz-options"),
                cls="quiz-question",
            )
        )

    content = Div(
        Div(
            A(t("back_to_lesson", lang), href=f"/app/lesson/{quiz['lesson_id']}", style="font-size:13px; color:var(--ink-muted);"),
            cls="lesson-breadcrumb",
        ),
        H1(quiz["title"], cls="page-title"),
        P(t("pass_threshold", lang, threshold=quiz["pass_threshold"], xp=quiz["xp_reward"]), cls="page-subtitle"),
        Form(
            Input(type="hidden", name="presented_question_ids", value=",".join(str(q["id"]) for q in questions)),
            *q_items,
            Button(t("submit_quiz", lang), cls="btn btn-primary", type="submit", style="margin-top:24px;"),
            method="post",
            action=f"/app/quiz/{quiz_id}/submit",
        ),
        cls="quiz-container",
    )
    return app_shell(content, user=user, active="courses", title=quiz["title"], lang=lang, current_path=f"/app/quiz/{quiz_id}")


@app.post("/app/quiz/{quiz_id:int}/submit")
async def submit_quiz(req, quiz_id: int):
    user, redir = _require_login(req)
    if redir:
        return redir

    lang = get_lang(req)
    form = await req.form()
    import sqlalchemy as sa

    with db.begin() as conn:
        quiz = conn.execute(sa.text(f"SELECT * FROM {db.S}.quizzes WHERE id = :q"), {"q": quiz_id}).mappings().first()
        questions = db.get_quiz_questions(conn, quiz_id, lang=lang)
        presented = {int(value) for value in str(form.get("presented_question_ids", "")).split(",") if value.isdigit()}
        if presented:
            questions = [question for question in questions if question["id"] in presented]

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
        adaptive_decision = db.update_adaptive_state(
            conn, user_id=user["id"], quiz_id=quiz_id, score=score
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
                    Div(t("your_answer", lang, answer=r["user_answer"]), cls=cls),
                    (Div(t("correct_answer", lang, answer=r["correct_answer"]), cls="quiz-option correct") if not r["is_correct"] else ""),
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
            Div(t("passed", lang) if passed else t("not_passed", lang), style=f"font-size:18px; color: {'var(--green)' if passed else 'var(--red)'}; margin-bottom:8px;"),
            (Div(f"+{xp_earned} XP earned!", style="color:var(--accent-text); font-weight:600;") if xp_earned else ""),
            (Div(
                t("recommended_review", lang) if adaptive_decision["recommendation"] == "remedial" else t("ready_extension", lang),
                cls="adaptive-result",
            ) if adaptive_decision and adaptive_decision["recommendation"] != "hold" else ""),
            cls="quiz-result",
        ),
        *result_items,
        Div(
            A(t("back_to_lesson", lang).lstrip("← "), href=f"/app/lesson/{quiz['lesson_id']}", cls="btn btn-secondary"),
            (A(t("retry", lang), href=f"/app/quiz/{quiz_id}", cls="btn btn-primary") if not passed else ""),
            style="display:flex; gap:12px; justify-content:center; margin-top:24px;",
        ),
        cls="quiz-container",
    )
    return app_shell(content, user=user, active="courses", title=t("courses", lang), lang=lang, current_path=f"/app/quiz/{quiz_id}")


# ---------------------------------------------------------------------------
# Chat (AI Tutor)
# ---------------------------------------------------------------------------

@app.get("/app/chat")
def chat_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    lang = get_lang(req)
    lesson_id = req.query_params.get("lesson_id", "")

    with db.connect() as conn:
        history = db.get_chat_history(conn, user["id"], int(lesson_id) if lesson_id else None, limit=50)

    msg_els = []
    for m in history:
        cls = "msg msg-user" if m["role"] == "user" else "msg msg-assistant"
        if m["role"] == "assistant":
            msg_els.append(Div(
                Div(Span(t("ai_tutor", lang)), cls="msg-header"),
                Div(NotStr(m["content"]), cls="msg-content"),
                cls=cls,
            ))
        else:
            msg_els.append(Div(m["content"], cls=cls))

    content = Div(
        Div(t("ai_tutor", lang), cls="chat-header"),
        Div(*msg_els, id="chat-messages", cls="chat-messages"),
        Div(*[
            Button(t(key, lang), type="button", cls="prompt-chip", data_prompt=t(key, lang))
            for key in ("prompt_explain", "prompt_example", "prompt_quiz")
        ], cls="prompt-suggestions"),
        Div(
            Form(
                Div(
                    Textarea(placeholder=t("ask_placeholder", lang), id="chat-input", cls="chat-input", rows=1),
                    Button(t("send", lang), cls="chat-send", type="submit"),
                    cls="chat-input-row",
                ),
                id="chat-form",
                data_lesson_id=lesson_id,
                data_thinking=t("thinking", lang),
                data_tutor=t("ai_tutor", lang),
                data_connection_error=t("connection_error", lang),
            ),
            cls="chat-input-area",
        ),
        cls="chat-container",
    )
    return app_shell(content, user=user, active="chat", title=t("ai_tutor", lang), lang=lang, current_path="/app/chat")


@app.get("/app/chat/stream")
async def chat_stream(req):
    user = _get_session_user(req)
    if not user:
        return Response("Unauthorized", status_code=401)

    lang = get_lang(req)
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
            lesson = db.get_lesson(conn, lesson_id_int, lang=lang)
            if lesson:
                lesson_context = f"\n\nThe student is currently studying the lesson: '{lesson['title']}'\nLesson content:\n{lesson.get('content_md', '')[:2000]}"

    async def generate():
        try:
            provider = os.environ.get("MODEL_PROVIDER", "xai")
            model = os.environ.get("DEFAULT_MODEL", "grok-4-1-fast-reasoning")

            system_prompt = f"""You are an AI tutor on FastLearn, a multilingual learning platform.
Help students understand course material, answer questions, and guide them through concepts.
Be encouraging, clear, and concise. Use examples when helpful.
If the student seems stuck, break down the problem into smaller steps.
Format responses in Markdown when appropriate.
{prompt_language_directive(lang)}{lesson_context}"""

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

    lang = get_lang(req)
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
        H1(t("leaderboard", lang), cls="page-title"),
        P(t("top_learners", lang), cls="page-subtitle"),
        Table(
            Thead(Tr(Th("#"), Th("Name"), Th("Level"), Th("XP"), Th("Streak"))),
            Tbody(*rows),
            cls="leaderboard-table",
        ) if rows else Div(Div("No learners yet", cls="empty-state-text"), cls="empty-state"),
        cls="page-content",
    )
    return app_shell(content, user=user, active="leaderboard", lang=lang, current_path="/app/leaderboard")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@app.get("/app/profile")
def profile_page(req):
    user, redir = _require_login(req)
    if redir:
        return redir

    lang = get_lang(req)
    with db.connect() as conn:
        badges = db.get_user_badges(conn, user["id"], lang=lang)
        import sqlalchemy as sa
        lessons_done = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.lesson_progress WHERE user_id = :u AND status = 'completed'"),
            {"u": user["id"]},
        ).scalar()
        quizzes_passed = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.quiz_attempts WHERE user_id = :u AND passed = true"),
            {"u": user["id"]},
        ).scalar()
        active_seconds = conn.execute(
            sa.text(f"SELECT COALESCE(sum(seconds_active), 0) FROM {db.S}.learning_time WHERE user_id = :u"),
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
            Div(Div(_duration(active_seconds), cls="dashboard-card-value"), Div(t("time_spent", lang), cls="dashboard-card-label"), cls="dashboard-card"),
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
    return app_shell(content, user=user, active=None, lang=lang, current_path="/app/profile")


# ---------------------------------------------------------------------------
# Manage courses (instructor)
# ---------------------------------------------------------------------------

@app.get("/app/manage")
def manage_page(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir

    with db.connect() as conn:
        courses = db.get_managed_courses(conn, user)

    rows = []
    for c in courses:
        status_cls = "status-pill status-published" if c["is_published"] else "status-pill status-draft"
        rows.append(Tr(
            Td(A(c["title"], href=f"/app/course/{c['slug']}")),
            Td(c.get("category", "")),
            Td(c.get("difficulty", "").title()),
            Td(Span("Published" if c["is_published"] else "Draft", cls=status_cls)),
            Td(A(t("learning_strategy", get_lang(req)), href=f"/app/course/{c['id']}/strategy", cls="btn btn-sm")),
        ))

    content = Div(
        Div(
            H1("Manage Courses", cls="page-title"),
            A("+ New Course", href="/app/manage/new", cls="btn btn-primary btn-sm"),
            style="display:flex; justify-content:space-between; align-items:center;",
        ),
        Table(
            Thead(Tr(Th("Title"), Th("Category"), Th("Difficulty"), Th("Status"), Th(t("learning_strategy", get_lang(req))))),
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
    user, redir = _require_teacher(req)
    if redir:
        return redir

    step = req.query_params.get("step", "1")
    course_id = req.query_params.get("course_id", "")
    module_id = req.query_params.get("module_id", "")
    lesson_id = req.query_params.get("lesson_id", "")
    msg = req.query_params.get("msg", "")
    error = req.query_params.get("error", "")

    if course_id:
        if not course_id.isdigit():
            return RedirectResponse("/app/configure", status_code=303)
        denied = _can_manage_or_redirect(user, int(course_id))
        if denied:
            return denied
    if module_id and not module_id.isdigit():
        return RedirectResponse("/app/configure", status_code=303)
    if lesson_id and not lesson_id.isdigit():
        return RedirectResponse("/app/configure", status_code=303)

    import sqlalchemy as sa

    with db.connect() as conn:
        courses = db.get_managed_courses(conn, user)
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
                if course_id and selected_module["course_id"] != int(course_id):
                    return RedirectResponse("/app/configure", status_code=303)
                lessons = db.get_lessons(conn, int(module_id))

        if lesson_id:
            selected_lesson = db.get_lesson(conn, int(lesson_id))
            if selected_lesson and module_id and selected_lesson["module_id"] != int(module_id):
                return RedirectResponse("/app/configure", status_code=303)

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
                    Div(Label("Difficulty", cls="form-label"), Select(
                        Option("Easier", value="1"), Option("Standard", value="2", selected=True),
                        Option("Harder", value="3"), name="difficulty_level", cls="form-input"), cls="form-group"),
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
    user, redir = _require_teacher(req)
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
    user, redir = _require_teacher(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    order_idx = int(form.get("order_idx", "0"))

    if not course_id.isdigit() or _can_manage_or_redirect(user, int(course_id)):
        return RedirectResponse("/app/manage", status_code=303)

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
    user, redir = _require_teacher(req)
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

    if not module_id.isdigit():
        return RedirectResponse("/app/manage", status_code=303)
    import sqlalchemy as sa
    with db.connect() as conn:
        actual_course_id = conn.execute(
            sa.text(f"SELECT course_id FROM {db.S}.modules WHERE id = :module"),
            {"module": int(module_id)},
        ).scalar()
    if not actual_course_id or _can_manage_or_redirect(user, actual_course_id):
        return RedirectResponse("/app/manage", status_code=303)
    course_id = str(actual_course_id)

    if not title or not module_id:
        return RedirectResponse(
            f"/app/configure?step=3&course_id={course_id}&module_id={module_id}&error=Title+is+required",
            status_code=303,
        )

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
    user, redir = _require_teacher(req)
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
    with db.connect() as conn:
        actual_course_id = conn.execute(sa.text(f"""
            SELECT m.course_id FROM {db.S}.lessons l
            JOIN {db.S}.modules m ON m.id = l.module_id WHERE l.id = :lesson
        """), {"lesson": int(lesson_id or 0)}).scalar()
    if not actual_course_id or _can_manage_or_redirect(user, actual_course_id):
        return RedirectResponse("/app/manage", status_code=303)
    course_id = str(actual_course_id)
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
    user, redir = _require_teacher(req)
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
    difficulty_level = max(1, min(3, int(form.get("difficulty_level", "2"))))

    options = [o for o in [option_a, option_b, option_c, option_d] if o]

    import sqlalchemy as sa
    with db.connect() as conn:
        actual_course_id = conn.execute(sa.text(f"""
            SELECT m.course_id FROM {db.S}.quiz_questions qq
            JOIN {db.S}.quizzes q ON q.id = qq.quiz_id
            JOIN {db.S}.lessons l ON l.id = q.lesson_id
            JOIN {db.S}.modules m ON m.id = l.module_id
            WHERE qq.quiz_id = :quiz LIMIT 1
        """), {"quiz": int(quiz_id or 0)}).scalar()
        if not actual_course_id:
            actual_course_id = conn.execute(sa.text(f"""
                SELECT m.course_id FROM {db.S}.quizzes q
                JOIN {db.S}.lessons l ON l.id = q.lesson_id
                JOIN {db.S}.modules m ON m.id = l.module_id WHERE q.id = :quiz
            """), {"quiz": int(quiz_id or 0)}).scalar()
    if not actual_course_id or _can_manage_or_redirect(user, actual_course_id):
        return RedirectResponse("/app/manage", status_code=303)
    course_id = str(actual_course_id)
    with db.begin() as conn:
        count = conn.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.quiz_questions WHERE quiz_id = :q"), {"q": int(quiz_id)}
        ).scalar()
        conn.execute(
            sa.text(f"""
                INSERT INTO {db.S}.quiz_questions (quiz_id, question_text, options, correct_answer, explanation, order_idx, difficulty_level)
                VALUES (:q, :qt, :opts, :ca, :ex, :o, :level)
            """),
            {"q": int(quiz_id), "qt": question_text, "opts": json.dumps(options), "ca": correct_answer,
             "ex": explanation, "o": count, "level": difficulty_level},
        )

    return RedirectResponse(
        f"/app/configure?step=4&course_id={course_id}&module_id={module_id}&lesson_id={lesson_id}&msg=Question+added!",
        status_code=303,
    )


@app.post("/app/configure/toggle-publish")
async def toggle_publish(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir

    form = await req.form()
    course_id = form.get("course_id", "")

    if not course_id.isdigit() or _can_manage_or_redirect(user, int(course_id)):
        return RedirectResponse("/app/manage", status_code=303)

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
# Team, invitations, assignments, reports and adaptive strategy
# ---------------------------------------------------------------------------

def _duration(seconds: int) -> str:
    seconds = int(seconds or 0)
    if 0 < seconds < 60:
        return f"{seconds}s"
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


@app.get("/invite/{token}")
def invitation_page(req, token: str):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    import sqlalchemy as sa
    with db.connect() as conn:
        invite = conn.execute(sa.text(f"""
            SELECT * FROM {db.S}.invitations
            WHERE token_hash = :token AND consumed_at IS NULL AND revoked_at IS NULL
        """), {"token": token_hash}).mappings().first()
    if not invite:
        return auth_page(Div(H2("Invitation unavailable", cls="auth-title"),
                             P("This invitation has already been used or revoked."), cls="auth-box"))
    current = _get_session_user(req)
    if current and current["email"].lower() == invite["email"].lower():
        with db.begin() as conn:
            _consume_invitation(conn, token_hash, current)
        return RedirectResponse("/app", status_code=303)
    return auth_page(Div(
        H2("Join FastLearn", cls="auth-title"),
        P(f"You were invited as {invite['role']}.", cls="page-subtitle"),
        account_auth.google_button("Continue with Google", href=f"/auth/google?invite={token}"),
        Div("or create a password", cls="auth-divider"),
        Form(
            Input(type="hidden", name="token", value=token),
            Input(name="display_name", placeholder="Name", required=True, cls="form-input"),
            Input(name="email", type="email", value=invite["email"], readonly=True, cls="form-input"),
            Input(name="password", type="password", minlength=10, required=True, placeholder="Password (10+ characters)", cls="form-input"),
            Button("Accept invitation", type="submit", cls="btn btn-primary btn-block"),
            method="post", action="/invite/accept",
        ),
        cls="auth-box",
    ))


@app.post("/invite/accept")
async def accept_invitation(req):
    form = await req.form()
    token = str(form.get("token", ""))
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    name = str(form.get("display_name", "")).strip()
    password = str(form.get("password", ""))
    if not name or len(password) < 10:
        return RedirectResponse(f"/invite/{token}", status_code=303)
    import sqlalchemy as sa
    with db.begin() as conn:
        invite = conn.execute(sa.text(f"""
            SELECT * FROM {db.S}.invitations
            WHERE token_hash = :token AND consumed_at IS NULL AND revoked_at IS NULL
        """), {"token": token_hash}).mappings().first()
        if not invite:
            return RedirectResponse(f"/invite/{token}", status_code=303)
        user = db.get_user_by_email(conn, invite["email"])
        if user:
            return RedirectResponse(f"/invite/{token}", status_code=303)
        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.users (email, password_hash, display_name, role)
            VALUES (:email, :password, :name, :role)
        """), {
            "email": invite["email"], "password": _hash_pw(password), "name": name,
            "role": db.role_for_email(invite["email"], invite["role"]),
        })
        user = db.get_user_by_email(conn, invite["email"])
        _consume_invitation(conn, token_hash, user)
    req.session["user_id"] = user["id"]
    return RedirectResponse("/app", status_code=303)


@app.get("/app/team")
def team_page(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    lang = get_lang(req)
    import sqlalchemy as sa
    with db.connect() as conn:
        if user["role"] == "admin":
            people = conn.execute(sa.text(f"SELECT * FROM {db.S}.users ORDER BY created_at DESC")).mappings().all()
            invitations = conn.execute(sa.text(f"""
                SELECT i.*, u.display_name AS inviter_name FROM {db.S}.invitations i
                JOIN {db.S}.users u ON u.id = i.invited_by
                WHERE i.consumed_at IS NULL AND i.revoked_at IS NULL ORDER BY i.created_at DESC
            """)).mappings().all()
        else:
            people = conn.execute(sa.text(f"SELECT * FROM {db.S}.users WHERE role = 'student' ORDER BY created_at DESC")).mappings().all()
            invitations = conn.execute(sa.text(f"""
                SELECT i.*, u.display_name AS inviter_name FROM {db.S}.invitations i
                JOIN {db.S}.users u ON u.id = i.invited_by
                WHERE i.invited_by = :user AND i.consumed_at IS NULL AND i.revoked_at IS NULL
                ORDER BY i.created_at DESC
            """), {"user": user["id"]}).mappings().all()
        courses = db.get_managed_courses(conn, user, lang=lang)
        managed_ids = [course["id"] for course in courses]
        if user["role"] == "admin":
            assignments = conn.execute(sa.text(f"""
                SELECT ca.user_id, ca.course_id, c.title FROM {db.S}.course_assignments ca
                JOIN {db.S}.courses c ON c.id = ca.course_id
            """)).mappings().all()
            teacher_access = conn.execute(sa.text(f"""
                SELECT a.teacher_id AS user_id, a.course_id, c.title FROM {db.S}.teacher_course_access a
                JOIN {db.S}.courses c ON c.id = a.course_id
            """)).mappings().all()
        elif managed_ids:
            assignments = conn.execute(sa.text(f"""
                SELECT ca.user_id, ca.course_id, c.title FROM {db.S}.course_assignments ca
                JOIN {db.S}.courses c ON c.id = ca.course_id WHERE ca.course_id = ANY(:courses)
            """), {"courses": managed_ids}).mappings().all()
            teacher_access = []
        else:
            assignments, teacher_access = [], []
    assigned_by_user = {}
    for assignment in [*assignments, *teacher_access]:
        assigned_by_user.setdefault(assignment["user_id"], []).append(dict(assignment))
    rows = []
    for person in people:
        person_assignments = assigned_by_user.get(person["id"], [])
        role_control = Span(t(person["role"], lang), cls=f"role-pill role-{person['role']}")
        if user["role"] == "admin" and person["email"].lower() != db.ADMIN_EMAIL:
            role_control = Form(
                Input(type="hidden", name="user_id", value=person["id"]),
                Select(
                    Option(t("student", lang), value="student", selected=person["role"] == "student"),
                    Option(t("teacher", lang), value="teacher", selected=person["role"] in ("teacher", "instructor")),
                    name="role", cls="form-input compact",
                ), Button(t("save_settings", lang), cls="btn btn-sm", type="submit"),
                method="post", action="/app/team/role", cls="inline-form",
            )
        can_assign = person["role"] == "student" or (user["role"] == "admin" and person["role"] in ("teacher", "instructor"))
        assignment_form = Form(
            Input(type="hidden", name="user_id", value=person["id"]),
            Select(*[Option(c["title"], value=c["id"]) for c in courses], name="course_id", cls="form-input compact"),
            Button(t("assign_course", lang), cls="btn btn-sm", type="submit"),
            method="post", action="/app/team/assign", cls="inline-form",
        ) if can_assign and courses else ""
        chips = Div(*[
            Form(
                Input(type="hidden", name="user_id", value=person["id"]),
                Input(type="hidden", name="course_id", value=item["course_id"]),
                Span(item["title"]), Button("×", title=t("remove", lang), type="submit", cls="chip-remove"),
                method="post", action="/app/team/unassign", cls="assignment-chip",
            ) for item in person_assignments
        ], cls="assignment-chips")
        rows.append(Tr(Td(person["display_name"], Br(), Small(person["email"])), Td(role_control), Td(chips, assignment_form)))
    invite_roles = [Option(t("student", lang), value="student")]
    if user["role"] == "admin":
        invite_roles.append(Option(t("teacher", lang), value="teacher"))
    content = Div(
        H1(t("team_title", lang), cls="page-title"), P(t("team_subtitle", lang), cls="page-subtitle"),
        (Div(req.query_params.get("msg"), cls="alert alert-success") if req.query_params.get("msg") else ""),
        (Div(req.query_params.get("error"), cls="alert alert-error") if req.query_params.get("error") else ""),
        Div(H2(t("invite_person", lang)), Form(
            Input(name="email", type="email", placeholder=t("email", lang), required=True, cls="form-input"),
            Select(*invite_roles, name="role", cls="form-input"),
            Button(t("invite", lang), type="submit", cls="btn btn-primary"),
            method="post", action="/app/team/invite", cls="team-invite-form",
        ), cls="team-panel"),
        H2(t("people", lang)),
        Table(Thead(Tr(Th(t("people", lang)), Th(t("role", lang)), Th(t("course_assignments", lang)))),
              Tbody(*rows), cls="manage-table"),
        (Div(H2(t("pending_invitations", lang)), Table(
            Thead(Tr(Th(t("email", lang)), Th(t("role", lang)), Th(""))),
            Tbody(*[Tr(Td(inv["email"]), Td(t(inv["role"], lang)), Td(Form(
                Input(type="hidden", name="invitation_id", value=inv["id"]),
                Button(t("revoke", lang), type="submit", cls="btn btn-sm"), method="post", action="/app/team/revoke",
            ))) for inv in invitations]), cls="manage-table"), cls="team-panel") if invitations else ""),
        cls="page-content",
    )
    return app_shell(content, user=user, active="team", lang=lang, current_path="/app/team")


@app.post("/app/team/invite")
async def invite_person(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    form = await req.form()
    email = str(form.get("email", "")).strip().lower()
    role = str(form.get("role", "student"))
    if "@" not in email or role not in {"student", "teacher"} or (role == "teacher" and user["role"] != "admin"):
        return RedirectResponse("/app/team?error=Invalid+invitation", status_code=303)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    import sqlalchemy as sa
    with db.begin() as conn:
        if db.get_user_by_email(conn, email):
            return RedirectResponse("/app/team?error=That+person+already+has+an+account", status_code=303)
        conn.execute(sa.text(f"""
            UPDATE {db.S}.invitations SET revoked_at = now()
            WHERE lower(email) = :email AND consumed_at IS NULL AND revoked_at IS NULL
        """), {"email": email})
        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.invitations (email, role, token_hash, invited_by)
            VALUES (:email, :role, :token, :by)
        """), {"email": email, "role": role, "token": token_hash, "by": user["id"]})
        db.audit(conn, actor_id=user["id"], action="invitation.created", target_type="user",
                 target_id=email, details={"role": role})
    base = os.getenv("FASTLEARN_PUBLIC_URL", "https://fastlearn.fun").rstrip("/")
    invite_url = f"{base}/invite/{token}"
    sent = account_auth.send_email(
        email, "You are invited to FastLearn",
        f"<p>Hello,</p><p>{html.escape(user['display_name'])} invited you to FastLearn as a {html.escape(role)}.</p>"
        f"<p><a href=\"{html.escape(invite_url, quote=True)}\">Accept your invitation</a></p>"
        "<p>This invitation does not expire, can be used once, and may be revoked by the sender.</p>",
    )
    result = "Invitation+sent" if sent else "Invitation+created,+but+email+delivery+is+not+configured"
    return RedirectResponse(f"/app/team?msg={result}", status_code=303)


@app.post("/app/team/revoke")
async def revoke_invitation(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    form = await req.form()
    invitation_id = int(form.get("invitation_id", 0))
    import sqlalchemy as sa
    with db.begin() as conn:
        params = {"id": invitation_id, "user": user["id"]}
        scope = "" if user["role"] == "admin" else "AND invited_by = :user"
        conn.execute(sa.text(f"""
            UPDATE {db.S}.invitations SET revoked_at = now()
            WHERE id = :id AND consumed_at IS NULL {scope}
        """), params)
        db.audit(conn, actor_id=user["id"], action="invitation.revoked", target_type="invitation",
                 target_id=invitation_id)
    return RedirectResponse("/app/team?msg=Invitation+revoked", status_code=303)


@app.post("/app/team/role")
async def change_role(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    if user["role"] != "admin":
        return RedirectResponse("/app/team?error=Administrator+access+required", status_code=303)
    form = await req.form()
    target_id = int(form.get("user_id", 0))
    role = str(form.get("role", "student"))
    if role not in {"teacher", "student"}:
        return RedirectResponse("/app/team?error=Invalid+role", status_code=303)
    import sqlalchemy as sa
    with db.begin() as conn:
        conn.execute(sa.text(f"""
            UPDATE {db.S}.users SET role = :role
            WHERE id = :id AND lower(email) <> :admin_email
        """), {"role": role, "id": target_id, "admin_email": db.ADMIN_EMAIL})
        db.audit(conn, actor_id=user["id"], action="user.role_changed", target_type="user",
                 target_id=target_id, details={"role": role})
    return RedirectResponse("/app/team?msg=Role+updated", status_code=303)


@app.post("/app/team/assign")
async def assign_team_course(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    form = await req.form()
    target_id, course_id = int(form.get("user_id", 0)), int(form.get("course_id", 0))
    import sqlalchemy as sa
    with db.begin() as conn:
        target = db.get_user(conn, target_id)
        if not target or not db.can_manage_course(conn, user, course_id):
            return RedirectResponse("/app/team?error=Assignment+not+allowed", status_code=303)
        if target["role"] == "student":
            db.assign_course(conn, user_id=target_id, course_id=course_id, assigned_by=user["id"])
        elif target["role"] in ("teacher", "instructor") and user["role"] == "admin":
            conn.execute(sa.text(f"""
                INSERT INTO {db.S}.teacher_course_access (teacher_id, course_id, granted_by)
                VALUES (:teacher, :course, :by) ON CONFLICT DO NOTHING
            """), {"teacher": target_id, "course": course_id, "by": user["id"]})
        else:
            return RedirectResponse("/app/team?error=Assignment+not+allowed", status_code=303)
        db.audit(conn, actor_id=user["id"], action="course.assigned", target_type="user",
                 target_id=target_id, details={"course_id": course_id})
    return RedirectResponse("/app/team?msg=Course+assigned", status_code=303)


@app.post("/app/team/unassign")
async def unassign_team_course(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    form = await req.form()
    target_id, course_id = int(form.get("user_id", 0)), int(form.get("course_id", 0))
    import sqlalchemy as sa
    with db.begin() as conn:
        target = db.get_user(conn, target_id)
        if not target or not db.can_manage_course(conn, user, course_id):
            return RedirectResponse("/app/team?error=Removal+not+allowed", status_code=303)
        if target["role"] == "student":
            db.unassign_course(conn, user_id=target_id, course_id=course_id)
        elif user["role"] == "admin":
            conn.execute(sa.text(f"""
                DELETE FROM {db.S}.teacher_course_access WHERE teacher_id = :teacher AND course_id = :course
            """), {"teacher": target_id, "course": course_id})
        db.audit(conn, actor_id=user["id"], action="course.unassigned", target_type="user",
                 target_id=target_id, details={"course_id": course_id})
    return RedirectResponse("/app/team?msg=Course+assignment+removed", status_code=303)


@app.get("/app/reports")
def learning_reports(req):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    lang = get_lang(req)
    with db.connect() as conn:
        courses = db.get_managed_courses(conn, user, lang=lang)
        report = db.learning_time_report(conn, None if user["role"] == "admin" else [c["id"] for c in courses])
    rows = [Tr(
        Td(row["display_name"], Br(), Small(row["email"])), Td(row.get("course_title") or "AI Tutor"),
        Td(f"{row['completed_lessons']}/{row['total_lessons']}"),
        Td(f"{int(row['average_score'])}%" if row.get("average_score") is not None else "—"),
        Td(str(row["difficulty_level"])),
        Td(_duration(row["seconds_active"])), Td(_duration(row["lesson_seconds"])),
        Td(_duration(row["quiz_seconds"])), Td(_duration(row["tutor_seconds"])),
    ) for row in report]
    content = Div(
        H1(t("learning_reports", lang), cls="page-title"),
        P("Active time pauses when the tab is hidden or the learner is inactive for 90 seconds.", cls="page-subtitle"),
        Table(Thead(Tr(Th(t("student", lang)), Th(t("courses", lang)), Th(t("progress", lang)), Th("Average score"), Th(t("difficulty", lang)), Th(t("time_spent", lang)),
                           Th(t("lesson_time", lang)), Th(t("quiz_time", lang)), Th(t("tutor_time", lang)))),
              Tbody(*rows) if rows else Tbody(Tr(Td("No tracked activity yet.", colspan="9"))), cls="manage-table"),
        cls="page-content",
    )
    return app_shell(content, user=user, active="reports", lang=lang, current_path="/app/reports")


@app.get("/app/course/{course_id:int}/strategy")
def course_strategy(req, course_id: int):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    denied = _can_manage_or_redirect(user, course_id)
    if denied:
        return denied
    lang = get_lang(req)
    import sqlalchemy as sa
    with db.begin() as conn:
        course = conn.execute(sa.text(f"SELECT * FROM {db.S}.courses WHERE id = :course"), {"course": course_id}).mappings().first()
        settings = db.get_course_learning_settings(conn, course_id)
        lessons = conn.execute(sa.text(f"""
            SELECT l.id, l.title FROM {db.S}.lessons l JOIN {db.S}.modules m ON m.id = l.module_id
            WHERE m.course_id = :course ORDER BY m.order_idx, l.order_idx
        """), {"course": course_id}).mappings().all()
        drafts = conn.execute(sa.text(f"""
            SELECT * FROM {db.S}.content_drafts WHERE course_id = :course ORDER BY created_at DESC
        """), {"course": course_id}).mappings().all()
    draft_cards = []
    for draft in drafts:
        payload = draft["content"] if isinstance(draft["content"], dict) else json.loads(draft["content"])
        english = payload.get("en", {})
        draft_heading = english.get("question_text") if draft["draft_type"] == "quiz_variant" else english.get("title")
        draft_preview = english.get("explanation") if draft["draft_type"] == "quiz_variant" else english.get("content_md")
        actions = ""
        if draft["status"] == "pending":
            actions = Div(
                Form(Input(type="hidden", name="draft_id", value=draft["id"]), Input(type="hidden", name="action", value="approve"),
                     Button(t("approve", lang), type="submit", cls="btn btn-primary btn-sm"), method="post", action=f"/app/course/{course_id}/draft"),
                Form(Input(type="hidden", name="draft_id", value=draft["id"]), Input(type="hidden", name="action", value="reject"),
                     Button(t("reject", lang), type="submit", cls="btn btn-sm"), method="post", action=f"/app/course/{course_id}/draft"),
                cls="inline-form",
            )
        draft_cards.append(Div(
            Div(Span(draft["draft_type"].replace("_", " ").title(), cls="role-pill"), Span(draft["status"].title(), cls="status-pill"), cls="course-meta"),
            H3(draft_heading or "Generated material"),
            P((draft_preview or "").replace("#", "")[:240]),
            Div("EN · ET · LT", cls="page-subtitle"), actions, cls="draft-card",
        ))
    content = Div(
        A("← " + t("manage_courses", lang), href="/app/manage"), H1(course["title"], cls="page-title"),
        H2(t("learning_strategy", lang)), P(t("strategy_help", lang), cls="page-subtitle"),
        Form(
            Select(Option(t("linear", lang), value="linear", selected=settings["strategy"] == "linear"),
                   Option(t("adaptive", lang), value="adaptive", selected=settings["strategy"] == "adaptive"),
                   name="strategy", cls="form-input"),
            Div(Label("Support below (%)", cls="form-label"), Input(name="low_threshold", type="number", min=1, max=99, value=settings["low_threshold"], cls="form-input"),
                Label("Challenge at (%)", cls="form-label"), Input(name="high_threshold", type="number", min=1, max=100, value=settings["high_threshold"], cls="form-input"), cls="strategy-grid"),
            Label(Input(name="allow_reorder", type="checkbox", value="1", checked=settings["allow_reorder"]), " Reorder learning path"),
            Label(Input(name="allow_remedial", type="checkbox", value="1", checked=settings["allow_remedial"]), " Generate support lessons"),
            Button(t("save_settings", lang), type="submit", cls="btn btn-primary"), method="post", action=f"/app/course/{course_id}/strategy", cls="strategy-form",
        ),
        H2(t("content_drafts", lang)),
        Form(
            Select(*[Option(item["title"], value=item["id"]) for item in lessons], name="lesson_id", cls="form-input"),
            Select(Option(t("remedial", lang), value="remedial"), Option(t("optional", lang), value="extension"),
                   Option(t("question_variant", lang), value="quiz_variant"), name="draft_type", cls="form-input"),
            Select(Option("Easier", value="1"), Option("Standard", value="2", selected=True), Option("Harder", value="3"),
                   name="difficulty_level", cls="form-input"),
            Button("Generate EN · ET · LT draft", type="submit", cls="btn btn-secondary"),
            method="post", action=f"/app/course/{course_id}/draft/generate", cls="team-invite-form",
        ) if lessons else "",
        Div(*draft_cards, cls="draft-grid") if draft_cards else Div("No drafts awaiting review.", cls="empty-state"),
        cls="page-content",
    )
    return app_shell(content, user=user, active="manage", lang=lang, current_path=f"/app/course/{course_id}/strategy")


@app.post("/app/course/{course_id:int}/strategy")
async def save_course_strategy(req, course_id: int):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    denied = _can_manage_or_redirect(user, course_id)
    if denied:
        return denied
    form = await req.form()
    strategy = str(form.get("strategy", "linear"))
    low, high = int(form.get("low_threshold", 60)), int(form.get("high_threshold", 85))
    if strategy not in {"linear", "adaptive"} or not 1 <= low < high <= 100:
        return RedirectResponse(f"/app/course/{course_id}/strategy?error=Invalid+settings", status_code=303)
    import sqlalchemy as sa
    with db.begin() as conn:
        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.course_learning_settings
                (course_id, strategy, low_threshold, high_threshold, allow_reorder, allow_remedial, updated_by)
            VALUES (:course, :strategy, :low, :high, :reorder, :remedial, :user)
            ON CONFLICT (course_id) DO UPDATE SET strategy=EXCLUDED.strategy,
                low_threshold=EXCLUDED.low_threshold, high_threshold=EXCLUDED.high_threshold,
                allow_reorder=EXCLUDED.allow_reorder, allow_remedial=EXCLUDED.allow_remedial,
                updated_by=EXCLUDED.updated_by, updated_at=now()
        """), {"course": course_id, "strategy": strategy, "low": low, "high": high,
                 "reorder": bool(form.get("allow_reorder")), "remedial": bool(form.get("allow_remedial")), "user": user["id"]})
        db.audit(conn, actor_id=user["id"], action="learning_strategy.updated", target_type="course",
                 target_id=course_id, details={"strategy": strategy, "low": low, "high": high})
    return RedirectResponse(f"/app/course/{course_id}/strategy?msg=Settings+saved", status_code=303)


@app.post("/app/course/{course_id:int}/draft/generate")
async def generate_course_draft(req, course_id: int):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    denied = _can_manage_or_redirect(user, course_id)
    if denied:
        return denied
    form = await req.form()
    lesson_id, kind = int(form.get("lesson_id", 0)), str(form.get("draft_type", "remedial"))
    requested_level = max(1, min(3, int(form.get("difficulty_level", 2))))
    if kind not in {"remedial", "extension", "quiz_variant"}:
        return RedirectResponse(f"/app/course/{course_id}/strategy", status_code=303)
    import sqlalchemy as sa
    with db.begin() as conn:
        actual_course = db.resource_course_id(conn, "lesson", lesson_id)
        if actual_course != course_id:
            return RedirectResponse("/app/manage", status_code=303)
        lesson_by_lang = {code: db.get_lesson(conn, lesson_id, lang=code) for code in SUPPORTED_LANGS}
        payload = (db._question_draft_payload(lesson_by_lang, requested_level) if kind == "quiz_variant" else
                   db._draft_payload(kind, lesson_by_lang, 100 if kind == "extension" else 50))
        module_id = lesson_by_lang["en"]["module_id"]
        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.content_drafts
                (course_id, module_id, source_lesson_id, draft_type, difficulty_level, content, created_by)
            VALUES (:course, :module, :lesson, :kind, :level, :content, :user)
        """), {"course": course_id, "module": module_id, "lesson": lesson_id, "kind": kind,
                 "level": 1 if kind == "remedial" else (3 if kind == "extension" else requested_level),
                 "content": json.dumps(payload), "user": user["id"]})
        db.audit(conn, actor_id=user["id"], action="content_draft.generated", target_type="course",
                 target_id=course_id, details={"draft_type": kind, "source_lesson_id": lesson_id})
    return RedirectResponse(f"/app/course/{course_id}/strategy?msg=Draft+generated+for+review", status_code=303)


@app.post("/app/course/{course_id:int}/draft")
async def review_course_draft(req, course_id: int):
    user, redir = _require_teacher(req)
    if redir:
        return redir
    denied = _can_manage_or_redirect(user, course_id)
    if denied:
        return denied
    form = await req.form()
    draft_id, action = int(form.get("draft_id", 0)), str(form.get("action", "reject"))
    import sqlalchemy as sa
    with db.begin() as conn:
        draft = conn.execute(sa.text(f"""
            SELECT * FROM {db.S}.content_drafts WHERE id = :id AND course_id = :course AND status = 'pending'
        """), {"id": draft_id, "course": course_id}).mappings().first()
        if not draft:
            return RedirectResponse(f"/app/course/{course_id}/strategy", status_code=303)
        if action == "approve":
            payload = draft["content"] if isinstance(draft["content"], dict) else json.loads(draft["content"])
            english = payload["en"]
            if draft["draft_type"] == "quiz_variant":
                quiz_id = conn.execute(sa.text(f"SELECT id FROM {db.S}.quizzes WHERE lesson_id = :lesson"),
                                       {"lesson": draft["source_lesson_id"]}).scalar()
                if not quiz_id:
                    lesson_title = conn.execute(sa.text(f"SELECT title FROM {db.S}.lessons WHERE id = :lesson"),
                                                {"lesson": draft["source_lesson_id"]}).scalar()
                    quiz_id = conn.execute(sa.text(f"""
                        INSERT INTO {db.S}.quizzes (lesson_id, title) VALUES (:lesson, :title) RETURNING id
                    """), {"lesson": draft["source_lesson_id"], "title": f"Practice: {lesson_title}"}).scalar()
                order_idx = conn.execute(sa.text(f"SELECT COALESCE(max(order_idx), -1) + 1 FROM {db.S}.quiz_questions WHERE quiz_id = :quiz"),
                                         {"quiz": quiz_id}).scalar()
                question_id = conn.execute(sa.text(f"""
                    INSERT INTO {db.S}.quiz_questions
                        (quiz_id, question_text, options, correct_answer, explanation, order_idx, difficulty_level)
                    VALUES (:quiz, :question, :options, :answer, :explanation, :order_idx, :level) RETURNING id
                """), {"quiz": quiz_id, "question": english["question_text"], "options": json.dumps(english["options"]),
                         "answer": english["correct_answer"], "explanation": english["explanation"],
                         "order_idx": order_idx, "level": draft["difficulty_level"]}).scalar()
                for code in ("et", "lt", "es"):
                    translated = payload[code]
                    conn.execute(sa.text(f"""
                        INSERT INTO {db.S}.content_translations
                            (entity_type, entity_id, language, question_text, options, correct_answer, explanation)
                        VALUES ('quiz_questions', :question_id, :language, :question, :options, :answer, :explanation)
                    """), {"question_id": question_id, "language": code, "question": translated["question_text"],
                             "options": json.dumps(translated["options"]), "answer": translated["correct_answer"],
                             "explanation": translated["explanation"]})
            else:
                order_idx = conn.execute(sa.text(f"SELECT COALESCE(max(order_idx), -1) + 1 FROM {db.S}.lessons WHERE module_id = :module"),
                                         {"module": draft["module_id"]}).scalar()
                result = conn.execute(sa.text(f"""
                    INSERT INTO {db.S}.lessons
                        (module_id, title, content_md, duration_min, xp_reward, order_idx, lesson_kind, difficulty_level)
                    VALUES (:module, :title, :content, 10, 25, :order_idx, :kind, :level) RETURNING id
                """), {"module": draft["module_id"], "title": english["title"], "content": english["content_md"],
                         "order_idx": order_idx, "kind": "remedial" if draft["draft_type"] == "remedial" else "optional",
                         "level": draft["difficulty_level"]})
                lesson_id = result.scalar()
                for code in ("et", "lt", "es"):
                    translated = payload[code]
                    conn.execute(sa.text(f"""
                        INSERT INTO {db.S}.content_translations (entity_type, entity_id, language, title, content_md)
                        VALUES ('lessons', :lesson, :language, :title, :content)
                    """), {"lesson": lesson_id, "language": code, "title": translated["title"], "content": translated["content_md"]})
            conn.execute(sa.text(f"""
                UPDATE {db.S}.content_drafts SET status='approved', approved_by=:user, reviewed_at=now() WHERE id=:id
            """), {"user": user["id"], "id": draft_id})
            if draft["draft_type"] != "quiz_variant":
                conn.execute(sa.text(f"""
                    UPDATE {db.S}.adaptive_recommendations SET target_lesson_id = :lesson
                    WHERE course_id = :course AND recommendation_type = :kind AND status = 'pending'
                """), {"lesson": lesson_id, "course": course_id, "kind": draft["draft_type"]})
        else:
            conn.execute(sa.text(f"""
                UPDATE {db.S}.content_drafts SET status='rejected', approved_by=:user, reviewed_at=now() WHERE id=:id
            """), {"user": user["id"], "id": draft_id})
        db.audit(conn, actor_id=user["id"], action=f"content_draft.{action}", target_type="content_draft",
                 target_id=draft_id, details={"course_id": course_id})
    return RedirectResponse(f"/app/course/{course_id}/strategy?msg=Draft+reviewed", status_code=303)


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
    return _require_teacher(req)


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


register_seo_routes(app)

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
