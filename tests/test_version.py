"""Release version stays consistent across UI and API surfaces."""

from fasthtml.common import to_xml

from app_version import APP_VERSION
from components.api import api, health
from components.landing import fastlearn_landing
from components.layout import left_pane


def test_release_version_is_bumped_and_used_by_api():
    assert APP_VERSION == "1.1.0"
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
