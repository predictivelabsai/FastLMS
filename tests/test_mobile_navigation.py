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
