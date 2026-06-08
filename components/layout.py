"""3-pane layout components — left nav, center content, right canvas.

Modelled after the liquidround 3-pane architecture:
  Left (280px)  — navigation, courses, gamification stats
  Center (flex) — main content area (lessons, chat, dashboard)
  Right (400px) — slide-in canvas for resources, quiz, discussions
"""

from fasthtml.common import *


def page_head(title="FastLMS"):
    return Head(
        Title(title),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="stylesheet", href="/static/app.css"),
        Script(src="https://unpkg.com/htmx.org@2.0.4"),
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(src="/static/chat.js", defer=True),
    )


def left_pane(user=None, active=None):
    nav_items = [
        ("dashboard", "Dashboard", "/app"),
        ("courses", "Courses", "/app/courses"),
        ("leaderboard", "Leaderboard", "/app/leaderboard"),
    ]

    if user and user.get("role") in ("instructor", "admin"):
        nav_items.append(("manage", "Manage Courses", "/app/manage"))

    nav_links = []
    for key, label, href in nav_items:
        cls = "nav-item active" if active == key else "nav-item"
        nav_links.append(A(label, href=href, cls=cls))

    stats = []
    if user:
        stats = Div(
            Div(
                Span(f"{user.get('xp', 0)} XP", cls="stat-value"),
                Span(user.get("level", "Novice"), cls="stat-label"),
                cls="stat-box",
            ),
            Div(
                Span(f"{user.get('streak_days', 0)}d", cls="stat-value"),
                Span("Streak", cls="stat-label"),
                cls="stat-box",
            ),
            cls="stats-grid",
        )

    return Div(
        Div(
            A(
                Span("F", cls="brand-icon"),
                Span("FastLMS", cls="brand-text"),
                href="/",
                cls="brand",
            ),
            cls="pane-header",
        ),
        stats,
        Nav(*nav_links, cls="nav-list"),
        Div(
            A("AI Tutor", href="/app/chat", cls="nav-item tutor-link" + (" active" if active == "chat" else "")),
            cls="nav-section",
        ),
        Div(
            (A(user["display_name"], href="/app/profile", cls="user-name") if user else ""),
            (A("Sign out", href="/auth/logout", cls="sign-out") if user else A("Sign in", href="/auth/login", cls="sign-in")),
            cls="pane-footer",
        ),
        cls="left-pane",
        id="left-pane",
    )


def right_pane():
    return Div(
        Div(
            Span("Canvas", cls="canvas-title"),
            Button("x", cls="canvas-close", onclick="toggleCanvas(false)"),
            cls="canvas-header",
        ),
        Div(id="canvas-content", cls="canvas-body"),
        cls="right-pane",
        id="right-pane",
    )


def app_shell(center_content, user=None, active=None, title="FastLMS"):
    return Html(
        page_head(title),
        Body(
            Div(
                left_pane(user, active),
                Div(center_content, cls="center-pane", id="center-pane"),
                right_pane(),
                cls="app-grid",
            ),
        ),
    )


def auth_page(content, title="FastLMS"):
    return Html(
        page_head(title),
        Body(Div(content, cls="auth-container")),
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


def course_card(course, progress=None):
    prog = progress_bar(progress["percent"], f"{progress['completed']}/{progress['total']}") if progress else ""
    difficulty_cls = f"difficulty-{course.get('difficulty', 'beginner')}"
    return A(
        Div(
            Div(
                Span(course.get("category", "General"), cls="course-category"),
                Span(course.get("difficulty", "beginner").title(), cls=f"course-difficulty {difficulty_cls}"),
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
