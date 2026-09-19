"""SESSION_SECRET must fail fast outside explicit dev/test."""

from __future__ import annotations

import importlib
import os
import sys

import pytest


def _reload_main(monkeypatch, **env):
    for key in ("APP_ENV", "ENV", "SESSION_SECRET"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    # Avoid a local .env reintroducing SESSION_SECRET during reload.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    sys.modules.pop("main", None)
    return importlib.import_module("main")


def test_weak_secret_allowed_in_explicit_dev(monkeypatch):
    mod = _reload_main(
        monkeypatch,
        APP_ENV="dev",
        SESSION_SECRET="fastlms-dev-secret-change-me",
    )
    assert mod._session_secret() == "fastlms-dev-secret-change-me"


def test_missing_secret_uses_dev_fallback_in_test_env(monkeypatch):
    mod = _reload_main(monkeypatch, APP_ENV="test", SESSION_SECRET="")
    assert mod._session_secret() == "fastlms-dev-secret-change-me"


def test_strong_secret_required_in_production(monkeypatch):
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        _reload_main(
            monkeypatch,
            APP_ENV="production",
            SESSION_SECRET="fastlms-dev-secret-change-me",
        )


def test_unset_env_rejects_missing_secret(monkeypatch):
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        _reload_main(monkeypatch, SESSION_SECRET="")


def test_strong_secret_ok_in_production(monkeypatch):
    mod = _reload_main(
        monkeypatch,
        APP_ENV="production",
        SESSION_SECRET="a-long-random-production-session-secret",
    )
    assert mod._session_secret() == "a-long-random-production-session-secret"
