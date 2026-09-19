"""Shared pytest fixtures. Keep APP_ENV explicit so main._session_secret allows import."""

from __future__ import annotations

import os

# main.py fails fast on weak/missing SESSION_SECRET outside explicit dev/test.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SESSION_SECRET", "fastlms-test-session-secret")
