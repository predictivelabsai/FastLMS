"""3-pane layout components — left nav, center content, right canvas.

Modelled after the liquidround 3-pane architecture:
  Left (280px)  — navigation, courses, interactivity stats
  Center (flex) — main content area (lessons, chat, dashboard)
  Right (400px) — slide-in canvas for resources, quiz, discussions
"""

from urllib.parse import urlencode

from fasthtml.common import *

from app_version import APP_VERSION
from .i18n import LANG_META, SUPPORTED_LANGS, t


def page_head(title="FastLearn", lang="en"):
    return Head(
        Title(title if "FastLearn" in title else f"{title} · FastLearn"),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg"),
        Link(rel="stylesheet", href="/static/app.css"),
        Script(src="https://unpkg.com/htmx.org@2.0.4"),
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
        Script(src="/static/vendor/plotly-3.6.0.min.js", defer=True),
        Script(src="/static/visualizations.js", defer=True),
        Script(src="/static/chat.js", defer=True),
        Script(src="/static/voice.js", defer=True),
        Script(src="/static/activity.js", defer=True),
        Script(src="/static/language.js", defer=True),
        Script(src="/static/navigation.js", defer=True),
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


def _nav_group(key: str, label: str, *children, opened: bool = False):
    """Accessible, persisted disclosure group for the application sidebar."""
    body_id = f"nav-section-{key}"
    return Div(
        Button(
            Span(label, cls="nav-section-name"),
            Span("›", cls="nav-section-expand", aria_hidden="true"),
            Span("⌄", cls="nav-section-collapse", aria_hidden="true"),
            type="button",
            cls="nav-section-toggle",
            aria_expanded="true" if opened else "false",
            aria_controls=body_id,
            onclick=f"toggleNavSection('{key}')",
        ),
        Div(*children, id=body_id, cls="nav-section-body", hidden=not opened),
        cls="nav-section open" if opened else "nav-section",
        data_nav_key=key,
        data_default_open="true" if opened else "false",
    )


def _chat_history(user, lang: str, current_chat_id: str | None = None):
    if not user:
        return ""
    try:
        import db
        with db.connect() as conn:
            sessions = db.list_chat_sessions(conn, user["id"], limit=20)
    except Exception:
        sessions = []

    def chat_link(session):
        active = str(session["id"]) == str(current_chat_id or "")
        return A(
            session.get("title") or t("new_chat", lang),
            href=f"/app/chat?chat={session['id']}",
            cls="chat-history-item active" if active else "chat-history-item",
            aria_current="page" if active else None,
        )

    recent = [chat_link(session) for session in sessions[:5]]
    older = [chat_link(session) for session in sessions[5:]]
    return _nav_group(
        "chats",
        t("chat_history", lang),
        Nav(
            *recent,
            (Details(Summary(t("more_chats", lang)), *older, cls="chat-history-more") if older else ""),
            aria_label=t("chat_history", lang),
        ),
        opened=True,
    )


def left_pane(user=None, active=None, lang="en", current_path="/app", current_chat_id=None):
    learning_items = [
        ("dashboard", t("dashboard", lang), "/app/dashboard"),
        ("courses", t("courses", lang), "/app/courses"),
        ("languages", t("language_learning", lang), "/app/languages"),
        ("leaderboard", t("leaderboard", lang), "/app/leaderboard"),
    ]

    teaching_items = []
    if user and user.get("role") in ("teacher", "instructor", "admin"):
        teaching_items = [
            ("manage", t("manage_courses", lang), "/app/manage"),
            ("configure", t("course_config", lang), "/app/configure"),
            ("team", t("team", lang), "/app/team"),
            ("reports", t("reports", lang), "/app/reports"),
        ]

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

    def nav_links(items):
        links = []
        for key, label, href in items:
            is_active = active == key
            links.append(A(
                label,
                href=href,
                cls="nav-item active" if is_active else "nav-item",
                aria_current="page" if is_active else None,
            ))
        return links

    learning_links = nav_links(learning_items)
    teaching_links = nav_links(teaching_items)

    school_nav = ""
    if school_items:
        links = nav_links(school_items)
        school_nav = _nav_group(
            "school",
            t("school_nav", lang),
            Nav(*links, cls="nav-list", aria_label=t("school_nav", lang)),
            opened=any(active == key for key, _, _ in school_items),
        )

    learning_nav = _nav_group(
        "learning",
        t("learning_nav", lang),
        Nav(*learning_links, cls="nav-list", aria_label=t("learning_nav", lang)),
        opened=not teaching_items or any(active == key for key, _, _ in learning_items),
    )

    teaching_nav = ""
    if teaching_items:
        teaching_nav = _nav_group(
            "teaching",
            t("teaching_nav", lang),
            Nav(*teaching_links, cls="nav-list", aria_label=t("teaching_nav", lang)),
            opened=any(active == key for key, _, _ in teaching_items),
        )

    resources_active = active == "developers"
    resources_nav = _nav_group(
        "resources",
        t("resources_nav", lang),
        Nav(
            A(
                t("developers", lang),
                href="/developers",
                cls="nav-item active" if resources_active else "nav-item",
                aria_current="page" if resources_active else None,
            ),
            cls="nav-list",
            aria_label=t("resources_nav", lang),
        ),
        opened=resources_active,
    )

    stats = []
    role = "teacher" if user and user.get("role") == "instructor" else (user.get("role", "student") if user else "student")
    if user and role in {"teacher", "admin"}:
        try:
            import db
            with db.connect() as conn:
                metrics = db.get_role_metrics(conn, user)
        except Exception:
            metrics = {"people": 0, "courses": 0, "approvals": 0}
        labels = (
            ("people", "staff_users" if role == "admin" else "staff_students"),
            ("courses", "staff_published" if role == "admin" else "staff_courses"),
            ("approvals", "staff_approvals"),
        )
        stats = Div(*[
            Div(Span(str(metrics[key]), cls="stat-value"), Span(t(label, lang), cls="stat-label"), cls="stat-box")
            for key, label in labels
        ], cls="stats-grid role-stats")
    elif user:
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

    role_label = "Admin" if role == "admin" and lang == "en" else t(role, lang)

    return Div(
        Div(
            A(
                Span("F", cls="brand-icon"),
                Span("FastLearn", cls="brand-text"),
                href="/app" if user else "/",
                cls="brand",
            ),
            Div(
                Button(
                    "‹",
                    type="button",
                    cls="desktop-sidebar-collapse",
                    aria_label=t("collapse_menu", lang),
                    aria_controls="left-pane",
                    aria_expanded="true",
                    data_testid="desktop-sidebar-collapse",
                    onclick="toggleSidebar(false)",
                ),
                Button(
                    NotStr('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>'),
                    type="button",
                    cls="mobile-drawer-close",
                    aria_label=t("close_menu", lang),
                    onclick="toggleLeftPane(false)",
                ),
                cls="pane-header-actions",
            ),
            cls="pane-header",
        ),
        Div(
            stats,
            Nav(
                A(
                    t("new_chat", lang),
                    href="/app/chat/new",
                    cls="nav-item tutor-link" + (" active" if active == "chat" else ""),
                    aria_current="page" if active == "chat" else None,
                ),
                cls="nav-list nav-chat-primary",
                aria_label=t("new_chat", lang),
            ),
            _chat_history(user, lang, current_chat_id),
            learning_nav,
            teaching_nav,
            school_nav,
            resources_nav,
            cls="left-pane-scroll",
        ),
        Div(
            (Div(
                A(user["display_name"], href="/app/profile", cls="user-name"),
                Span(f"({role_label})", cls=f"user-role user-role-{role}"),
                cls="user-identity",
            ) if user else ""),
            _language_picker(lang, current_path),
            (A(t("sign_out", lang), href="/auth/logout", cls="sign-out") if user else A(t("sign_in", lang), href="/auth/login", cls="sign-in")),
            Span(f"v{APP_VERSION}", cls="app-version"),
            cls="pane-footer",
        ),
        cls="left-pane",
        id="left-pane",
    )


def mobile_header(user=None, title="FastLearn", lang="en"):
    account_action = (
        A(t("sign_out", lang), href="/auth/logout", cls="mobile-account-action", data_testid="mobile-sign-out")
        if user else
        A(t("sign_in", lang), href="/auth/login", cls="mobile-account-action")
    )
    return Header(
        Button(
            NotStr('<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'),
            type="button",
            id="mobile-menu-button",
            cls="mobile-menu-button",
            aria_label=t("open_menu", lang),
            aria_controls="left-pane",
            aria_expanded="false",
            data_open_label=t("open_menu", lang),
            data_close_label=t("close_menu", lang),
            data_testid="mobile-menu-button",
            onclick="toggleLeftPane()",
        ),
        A(
            Span("F", cls="mobile-brand-icon"),
            Span(
                Span("FastLearn", cls="mobile-brand-name"),
                (Span(title, cls="mobile-page-name") if title != "FastLearn" else ""),
                cls="mobile-title-group",
            ),
            href="/app" if user else "/",
            cls="mobile-brand",
        ),
        account_action,
        cls="mobile-app-header",
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


def app_shell(center_content, user=None, active=None, title="FastLearn", lang="en", current_path="/app", current_chat_id=None):
    return Html(
        page_head(title, lang),
        Body(
            Div(
                mobile_header(user, title, lang),
                left_pane(user, active, lang, current_path, current_chat_id),
                Button(
                    "›",
                    type="button",
                    id="desktop-sidebar-expand",
                    cls="desktop-sidebar-expand",
                    aria_label=t("expand_menu", lang),
                    aria_controls="left-pane",
                    aria_expanded="false",
                    data_testid="desktop-sidebar-expand",
                    onclick="toggleSidebar(true)",
                ),
                Div(id="left-overlay", cls="left-overlay", aria_hidden="true", onclick="toggleLeftPane(false)"),
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


def course_card(course, progress=None, lang="en", assigned=False, href=None):
    prog = progress_bar(progress["percent"], f"{progress['completed']}/{progress['total']}") if progress else ""
    difficulty_cls = f"difficulty-{course.get('difficulty', 'beginner')}"
    return A(
        Div(
            Div(
                Span(course.get("category", "General"), cls="course-category"),
                Span(t(course.get("difficulty", "beginner"), lang), cls=f"course-difficulty {difficulty_cls}"),
                (Span(t("assigned", lang), cls="course-assigned") if assigned else ""),
                (Span(t("default_course", lang), cls="course-default") if course.get("is_default") else ""),
                cls="course-meta",
            ),
            H3(course["title"], cls="course-title"),
            P(course.get("description", "")[:120], cls="course-desc"),
            prog,
            cls="course-card-body",
        ),
        href=href or f"/app/chat/new?course={course['slug']}",
        cls="course-card",
    )
