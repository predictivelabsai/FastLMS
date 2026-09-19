"""Chrome smoke test for the locally vendored guided molecular activity."""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_guided_water_activity_renders_in_local_chrome_and_submits_answer():
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        pytest.skip("Google Chrome or Chromium is not installed")
    port = _free_port()
    server = subprocess.Popen(
        ["python", "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(ROOT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.25)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=chrome, headless=True)
            page = browser.new_page(viewport={"width": 900, "height": 700})
            page.goto(f"http://127.0.0.1:{port}/tests/chemistry_playwright.html", wait_until="networkidle")
            assert page.evaluate("Boolean(window.$3Dmol)")
            assert page.locator(".chemistry-card").is_visible()
            assert page.locator(".chemistry-viewer").is_visible()
            page.get_by_role("button", name="A. Bent").click()
            page.get_by_role("button", name="Check geometry").click()
            assert page.evaluate("window.__chemistryAnswer") == {
                "answer": {"choice": 0}, "label": "A. Bent",
            }
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
