"""Static route must not escape the static/ directory."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SESSION_SECRET", "fastlms-test-session-secret")

import main


def test_static_serves_file_inside_root(tmp_path, monkeypatch):
    root = tmp_path / "static"
    root.mkdir()
    (root / "ok.txt").write_text("hello", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    response = main.static_file("ok.txt")
    assert response.status_code == 200
    assert Path(response.path).resolve() == (root / "ok.txt").resolve()


@pytest.mark.parametrize(
    "escape",
    [
        "../main.py",
        "..%2fmain.py",
        "foo/../../main.py",
        "../../../etc/passwd",
        "..\\main.py",
    ],
)
def test_static_rejects_path_traversal(tmp_path, monkeypatch, escape):
    root = tmp_path / "static"
    root.mkdir()
    (root / "ok.txt").write_text("hello", encoding="utf-8")
    # Sibling secret outside the jail
    (tmp_path / "secret.txt").write_text("nope", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    response = main.static_file(escape)
    assert response.status_code == 404
