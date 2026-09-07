"""Signup-role and Google-button regressions."""

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

from fasthtml.common import to_xml

import db
from components.layout import left_pane

_AUTH_TEMP = tempfile.TemporaryDirectory(prefix="fastlearn-auth-tests-")
os.environ["FASTSME_AUTH_DB"] = str(Path(_AUTH_TEMP.name) / "accounts.sqlite")

from components import account_auth


def test_signup_role_is_limited_to_student_or_teacher():
    assert account_auth.normalize_signup_role("student") == "student"
    assert account_auth.normalize_signup_role("teacher") == "teacher"
    assert account_auth.normalize_signup_role("admin") == "student"
    assert db.role_for_email("learner@example.com", "teacher") == "teacher"
    assert db.role_for_email(db.ADMIN_EMAIL, "student") == "admin"


def test_landing_signup_has_role_choices_and_google_branding():
    markup = to_xml(account_auth.auth_modal("FastLearn", "en"))
    assert markup.count('type="radio" name="role" value="student"') == 2
    assert markup.count('type="radio" name="role" value="teacher"') == 2
    assert "Sign in as" in markup
    assert 'href="/auth/google?role=student"' in markup
    assert "this.closest('form')" in markup
    assert "#4285F4" in markup
    assert "Continue with Google" in markup


def test_role_survives_local_email_verification_store(tmp_path, monkeypatch):
    monkeypatch.setenv("FASTSME_AUTH_DB", str(tmp_path / "accounts.sqlite"))
    store = account_auth.AccountStore()
    monkeypatch.setattr(store, "_send_action", lambda *args: True)
    ok, _ = store.register("teacher@example.com", "long-enough-password", "Teacher", "teacher")
    assert ok
    with store._db() as connection:
        role = connection.execute(
            "SELECT role FROM accounts WHERE email=?", ("teacher@example.com",)
        ).fetchone()["role"]
    assert role == "teacher"


def test_full_registration_page_has_the_same_choices():
    import main

    request = SimpleNamespace(
        query_params={}, session={}, cookies={},
        headers={"host": "fastlearn.fun", "accept-language": "en"},
    )
    markup = to_xml(main.register_page(request))
    assert 'value="student"' in markup
    assert 'value="teacher"' in markup
    assert 'href="/auth/google?role=student"' in markup


def test_full_login_page_has_role_choices_for_local_and_google_signin():
    import main

    request = SimpleNamespace(
        query_params={}, session={}, cookies={},
        headers={"host": "fastlearn.fun", "accept-language": "en"},
    )
    markup = to_xml(main.login_page(request))
    assert "Sign in as" in markup
    assert 'name="role" value="student"' in markup
    assert 'name="role" value="teacher"' in markup
    assert 'href="/auth/google?role=student"' in markup
    assert "this.closest('form')" in markup


def test_navigation_profile_shows_effective_role_next_to_name():
    for role, label in (("admin", "Admin"), ("teacher", "Teacher"), ("student", "Student")):
        markup = to_xml(left_pane(
            user={"display_name": "Test User", "role": role, "xp": 0, "streak_days": 0},
            lang="en",
        ))
        assert f"({label})" in markup
        assert f"user-role-{role}" in markup


def test_staff_sidebar_uses_operational_metrics_not_student_gamification():
    markup = to_xml(left_pane(
        user={"id": 99999999, "display_name": "Teacher", "role": "teacher", "xp": 0, "streak_days": 0},
        lang="en",
    ))
    assert "Students" in markup
    assert "Active courses" in markup
    assert "Approvals" in markup
    assert " XP" not in markup
    assert "Streak" not in markup


def test_google_start_preserves_only_a_safe_signup_role(monkeypatch):
    import main

    monkeypatch.setattr(main.google_auth, "enabled", lambda: True)
    monkeypatch.setattr(main.google_auth, "new_state", lambda: "oauth-state")
    monkeypatch.setattr(main.google_auth, "authorize_url", lambda req, state: f"https://accounts.example/{state}")
    request = SimpleNamespace(query_params={"role": "teacher"}, session={})
    response = main.google_start(request)
    assert response.status_code == 303
    assert request.session["pending_signup_role"] == "teacher"

    unsafe = SimpleNamespace(query_params={"role": "admin"}, session={"pending_signup_role": "teacher"})
    main.google_start(unsafe)
    assert "pending_signup_role" not in unsafe.session


def test_mobile_google_signin_preserves_only_the_fixed_app_handoff(monkeypatch):
    import main

    mobile_page = SimpleNamespace(
        query_params={"return_to": "mobile"}, session={}, cookies={},
        headers={"host": "fastlearn.fun", "accept-language": "en"},
    )
    markup = to_xml(main.login_page(mobile_page))
    assert 'href="/auth/google?role=student&amp;return_to=mobile"' in markup
    assert 'href="/auth/register?return_to=mobile"' in markup

    monkeypatch.setattr(main.google_auth, "enabled", lambda: True)
    monkeypatch.setattr(main.google_auth, "new_state", lambda: "oauth-state")
    monkeypatch.setattr(main.google_auth, "authorize_url", lambda req, state: f"https://accounts.example/{state}")

    request = SimpleNamespace(query_params={"return_to": "mobile"}, session={})
    main.google_start(request)
    assert request.session["google_oauth_return_to"] == "mobile"
    assert main._google_success_destination(request.session["google_oauth_return_to"]) == "fastlearn://auth/complete"

    unsafe = SimpleNamespace(query_params={"return_to": "https://evil.example"}, session={})
    main.google_start(unsafe)
    assert "google_oauth_return_to" not in unsafe.session
    assert main._google_success_destination("https://evil.example") == "/app"


def test_google_role_picker_keeps_existing_mobile_return_parameter():
    assert "new URL(this.href,location.origin)" in account_auth.GOOGLE_SIGNUP_ONCLICK
    assert "searchParams.set('role',r.value)" in account_auth.GOOGLE_SIGNUP_ONCLICK
