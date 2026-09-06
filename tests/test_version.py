"""Release version stays consistent across UI and API surfaces."""

from fasthtml.common import to_xml

from app_version import APP_VERSION
from components.api import api, health
from components.landing import fastlearn_landing
from components.layout import left_pane, page_head


def test_release_version_is_bumped_and_used_by_api():
    assert APP_VERSION == "1.2.0"
    assert api.version == APP_VERSION
    assert health()["version"] == APP_VERSION


def test_release_version_is_visible_in_subdued_ui_labels():
    sidebar = to_xml(left_pane(user={
        "id": 987654321, "display_name": "Learner", "role": "student",
        "xp": 0, "streak_days": 0,
    }))
    landing = to_xml(fastlearn_landing())
    assert f">v{APP_VERSION}<" in sidebar
    assert 'class="app-version"' in sidebar
    assert f">v{APP_VERSION}<" in landing
    assert 'class="site-version"' in landing
    assert ">14<" in landing
    assert "art and music" in landing


def test_authenticated_app_head_uses_the_product_favicon():
    head = to_xml(page_head("Dashboard"))
    assert 'rel="icon"' in head
    assert 'type="image/svg+xml"' in head
    assert 'href="/static/favicon.svg"' in head
