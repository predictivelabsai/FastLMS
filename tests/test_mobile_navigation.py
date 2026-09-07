from pathlib import Path

from fasthtml.common import Div, to_xml

from components.layout import app_shell


def test_authenticated_shell_has_mobile_drawer_and_logout_controls():
    markup = to_xml(app_shell(
        Div("Dashboard"),
        user={"id": 42, "display_name": "Mobile Learner", "role": "student", "xp": 10, "streak_days": 2},
        active="dashboard",
        title="Dashboard",
    ))

    assert 'data-testid="mobile-menu-button"' in markup
    assert 'aria-controls="left-pane"' in markup
    assert 'aria-expanded="false"' in markup
    assert 'data-open-label="Open navigation menu"' in markup
    assert 'data-close-label="Close navigation menu"' in markup
    assert 'id="left-overlay"' in markup
    assert 'onclick="toggleLeftPane(false)"' in markup
    assert 'data-testid="mobile-sign-out"' in markup
    assert markup.count('href="/auth/logout"') == 2
    assert '/static/navigation.js' in markup


def test_mobile_navigation_script_manages_drawer_accessibility():
    script = Path("static/navigation.js").read_text()

    assert 'window.toggleLeftPane' in script
    assert 'aria-expanded' in script
    assert 'aria-hidden' in script
    assert 'event.key === "Escape"' in script
    assert 'button.focus()' in script


def test_sidebar_groups_use_accessible_disclosure_buttons_and_current_page():
    markup = to_xml(app_shell(
        Div("Dashboard"),
        user={"id": 42, "display_name": "Learner", "role": "student", "xp": 10, "streak_days": 2},
        active="dashboard",
        title="Dashboard",
    ))

    assert 'data-nav-key="learning"' in markup
    assert 'data-nav-key="chats"' in markup
    assert 'data-nav-key="resources"' in markup
    assert 'aria-controls="nav-section-learning"' in markup
    assert 'onclick="toggleNavSection(\'learning\')"' in markup
    assert '<span aria-hidden="true" class="nav-section-expand">›</span>' in markup
    assert '<span aria-hidden="true" class="nav-section-collapse">⌄</span>' in markup
    assert 'href="/app/dashboard" aria-current="page" class="nav-item active"' in markup


def test_staff_sidebar_groups_teaching_and_school_navigation():
    markup = to_xml(app_shell(
        Div("Manage courses"),
        user={"id": 7, "display_name": "Teacher", "role": "teacher"},
        active="manage",
        title="Manage courses",
    ))

    assert 'data-nav-key="teaching" data-default-open="true" class="nav-section open"' in markup
    assert 'data-nav-key="school"' in markup
    assert 'aria-label="Teaching"' in markup
    assert 'aria-label="School"' in markup


def test_desktop_sidebar_has_collapse_and_restore_controls():
    markup = to_xml(app_shell(
        Div("Dashboard"),
        user={"id": 42, "display_name": "Learner", "role": "student"},
        active="dashboard",
    ))

    assert 'data-testid="desktop-sidebar-collapse"' in markup
    assert 'onclick="toggleSidebar(false)"' in markup
    assert 'data-testid="desktop-sidebar-expand"' in markup
    assert 'onclick="toggleSidebar(true)"' in markup
    assert 'aria-label="Collapse navigation menu"' in markup
    assert 'aria-label="Expand navigation menu"' in markup


def test_navigation_script_persists_disclosures_and_sidebar_state():
    script = Path("static/navigation.js").read_text()

    assert 'window.toggleNavSection' in script
    assert 'fastlearn.nav.sections' in script
    assert 'containsCurrentPage' in script
    assert 'window.toggleSidebar' in script
    assert 'fastlearn.nav.sidebar-expanded' in script
    assert 'body.hidden = !open' in script
