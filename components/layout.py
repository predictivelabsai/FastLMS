"""3-pane layout components — left nav, center content, right canvas.

Modelled after the liquidround 3-pane architecture:
  Left (280px)  — navigation, courses, interactivity stats
  Center (flex) — main content area (lessons, chat, dashboard)
  Right (400px) — slide-in canvas for resources, quiz, discussions
"""

from urllib.parse import urlencode

from fasthtml.common import *

from .i18n import LANG_META, SUPPORTED_LANGS, t


def page_head(title="FastLearn", lang="en"):
    return Head(
        Title(title if "FastLearn" in title else f"{title} · FastLearn"),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="stylesheet", href="/static/app.css"),
        Script(src="https://unpkg.com/htmx.org@2.0.4"),
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(src="/static/chat.js", defer=True),
        Script(src="/static/activity.js", defer=True),
    )


def _language_picker(lang: str, current_path: str):
    return Details(
        Summary(LANG_META.get(lang, LANG_META["en"])["flag"], aria_label=t("language", lang), cls="app-lang-button"),
        Div(*[
            A(f"{LANG_META[code]['flag']} {LANG_META[code]['name']}",
              href=f"/set-lang?{urlencode({'lang': code, 'next': current_path})}",
              cls="app-lang-option active" if code == lang else "app-lang-option")
            for code in SUPPORTED_LANGS
        ], cls="app-lang-menu"), cls="app-lang",
    )


def left_pane(user=None, active=None, lang="en", current_path="/app"):
    nav_items = [
        ("dashboard", t("dashboard", lang), "/app"),
        ("courses", t("courses", lang), "/app/courses"),
        ("leaderboard", t("leaderboard", lang), "/app/leaderboard"),
    ]

    if user and user.get("role") in ("teacher", "instructor", "admin"):
        nav_items.append(("manage", t("manage_courses", lang), "/app/manage"))
        nav_items.append(("configure", t("course_config", lang), "/app/configure"))
        nav_items.append(("team", t("team", lang), "/app/team"))
        nav_items.append(("reports", t("reports", lang), "/app/reports"))

    school_items = []
    if user and user.get("role") in ("teacher", "instructor", "admin"):
        school_items = [
            ("school", "Overview", "/app/school"),
            ("students", "Students", "/app/school/students"),
            ("programs", "Programmes", "/app/school/programs"),
            ("gradebook", "Gradebook", "/app/school/gradebook"),
            ("attendance", "Attendance", "/app/school/attendance"),
            ("fees", "Fees", "/app/school/fees"),
        ]

    nav_links = []
    for key, label, href in nav_items:
        cls = "nav-item active" if active == key else "nav-item"
        nav_links.append(A(label, href=href, cls=cls))

    school_nav = ""
    if school_items:
        links = [A(label, href=href, cls="nav-item active" if active == key else "nav-item")
                 for key, label, href in school_items]
        school_nav = Div(Div("SCHOOL", cls="nav-section-label"), *links, cls="nav-section")

    stats = []
    if user:
        stats = Div(
            Div(
                Span(f"{user.get('xp', 0)} XP", cls="stat-value"),
                Span(t("level", lang), cls="stat-label"),
                cls="stat-box",
            ),
            Div(
                Span(f"{user.get('streak_days', 0)}d", cls="stat-value"),
                Span(t("streak", lang), cls="stat-label"),
                cls="stat-box",
            ),
            cls="stats-grid",
        )

    return Div(
        Div(
            A(
                Span("F", cls="brand-icon"),
                Span("FastLearn", cls="brand-text"),
                href="/",
                cls="brand",
            ),
            cls="pane-header",
        ),
        stats,
        Nav(*nav_links, cls="nav-list"),
        school_nav,
        Div(
            A(t("ai_tutor", lang), href="/app/chat", cls="nav-item tutor-link" + (" active" if active == "chat" else "")),
            A(t("developers", lang), href="/developers", cls="nav-item" + (" active" if active == "developers" else "")),
            cls="nav-section",
        ),
        Div(
            (A(user["display_name"], href="/app/profile", cls="user-name") if user else ""),
            _language_picker(lang, current_path),
            (A(t("sign_out", lang), href="/auth/logout", cls="sign-out") if user else A(t("sign_in", lang), href="/auth/login", cls="sign-in")),
            cls="pane-footer",
        ),
        cls="left-pane",
        id="left-pane",
    )


def right_pane(lang="en"):
    return Div(
        Div(
            Span(t("canvas", lang), cls="canvas-title"),
            Button("x", cls="canvas-close", onclick="toggleCanvas(false)"),
            cls="canvas-header",
        ),
        Div(id="canvas-content", cls="canvas-body"),
        cls="right-pane",
        id="right-pane",
    )


def app_shell(center_content, user=None, active=None, title="FastLearn", lang="en", current_path="/app"):
    return Html(
        page_head(title, lang),
        Body(
            Div(
                left_pane(user, active, lang, current_path),
                Div(center_content, cls="center-pane", id="center-pane"),
                right_pane(lang),
                cls="app-grid",
            ),
        ), lang=lang,
    )


def auth_page(content, title="FastLearn", lang="en"):
    return Html(
        page_head(title, lang),
        Body(Div(content, cls="auth-container")),
        lang=lang,
    )


# ---------------------------------------------------------------------------
# Reusable UI fragments
# ---------------------------------------------------------------------------

def progress_bar(percent, label=None):
    return Div(
        Div(style=f"width: {percent}%", cls="progress-fill"),
        Span(label or f"{percent}%", cls="progress-label"),
        cls="progress-bar",
    )


def badge_card(badge):
    return Div(
        Span(badge["icon"], cls="badge-icon"),
        Div(
            Span(badge["name"], cls="badge-name"),
            Span(badge.get("description", ""), cls="badge-desc"),
            cls="badge-info",
        ),
        cls="badge-card",
    )


def xp_popup(xp, message="XP earned!"):
    return Div(
        Span(f"+{xp} XP", cls="xp-amount"),
        Span(message, cls="xp-message"),
        cls="xp-popup",
        id="xp-popup",
    )


def course_card(course, progress=None, lang="en", assigned=False):
    prog = progress_bar(progress["percent"], f"{progress['completed']}/{progress['total']}") if progress else ""
    difficulty_cls = f"difficulty-{course.get('difficulty', 'beginner')}"
    return A(
        Div(
            Div(
                Span(course.get("category", "General"), cls="course-category"),
                Span(t(course.get("difficulty", "beginner"), lang), cls=f"course-difficulty {difficulty_cls}"),
                (Span(t("assigned", lang), cls="course-assigned") if assigned else ""),
                cls="course-meta",
            ),
            H3(course["title"], cls="course-title"),
            P(course.get("description", "")[:120], cls="course-desc"),
            prog,
            cls="course-card-body",
        ),
        href=f"/app/course/{course['slug']}",
        cls="course-card",
    )
