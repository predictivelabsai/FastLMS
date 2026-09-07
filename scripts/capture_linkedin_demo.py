#!/usr/bin/env python3
"""Capture the live English FastLearn journeys used by the LinkedIn GIF."""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "playwright" / "linkedin-demo"
BASE = "https://fastlearn.fun"
VIEWPORT = {"width": 1200, "height": 675}


def screenshot(page: Page, name: str) -> None:
    page.screenshot(path=OUT / name, animations="disabled")


def open_visual(page: Page, slug: str, lesson: str, image_name: str) -> dict:
    page.goto(f"{BASE}/app/chat/new?course={slug}", wait_until="networkidle")
    page.locator(".chat-choice", has_text=lesson).click()
    card = page.locator(".visual-card").last
    card.wait_for(state="visible", timeout=30_000)
    plot = card.locator(".js-plotly-plot")
    plot.wait_for(state="visible", timeout=30_000)
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(600)

    hover_target = None
    for selector in (".scatterlayer .point", ".pielayer .slice", ".sankey-link"):
        candidates = plot.locator(selector)
        if candidates.count():
            hover_target = candidates.nth(min(3, candidates.count() - 1))
            break
    if hover_target:
        hover_target.hover(force=True)
    page.wait_for_timeout(250)
    hover_labels = card.locator(".hoverlayer > *").count()
    screenshot(page, image_name)

    details = card.locator("details.visual-data")
    details.locator("summary").click()
    rows = details.locator("tbody tr").count()
    details.locator("summary").click()
    return {
        "title": card.locator(".visual-title").inner_text(),
        "modebar_buttons": card.locator(".modebar-btn").count(),
        "zoom_buttons": card.locator('.modebar-btn[data-title^="Zoom"]').count(),
        "hover_labels": hover_labels,
        "accessible_rows": rows,
        "aria_label": plot.get_attribute("aria-label"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict = {"release": None, "visuals": {}, "console_errors": [], "http_errors": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport=VIEWPORT, locale="en-GB", color_scheme="light")
        page = context.new_page()
        page.on("console", lambda message: report["console_errors"].append(message.text) if message.type == "error" else None)
        page.on(
            "response",
            lambda response: report["http_errors"].append(f"{response.status} {response.url}")
            if response.status >= 400 and response.url.startswith(BASE) else None,
        )

        health = page.request.get(f"{BASE}/healthz")
        report["release"] = health.json().get("version")
        if report["release"] != "1.4.0":
            raise RuntimeError(f"Expected production 1.4.0, got {report['release']}")

        page.goto(f"{BASE}/set-lang?lang=en&next=/", wait_until="networkidle")
        screenshot(page, "01-home.png")

        email = f"playwright-fastlearn-v14-{int(time.time())}-{secrets.token_hex(3)}@example.com"
        password = secrets.token_urlsafe(16)
        page.goto(f"{BASE}/auth/register", wait_until="networkidle")
        page.locator('input[name="role"][value="student"]').check()
        page.locator('input[name="display_name"]').fill("Demo Learner")
        page.locator('input[name="email"]').fill(email)
        page.locator('input[name="password"]').fill(password)
        page.locator('form[action="/auth/register"]').get_by_role("button", name="Create your account").click()
        page.wait_for_url("**/app/chat**", timeout=30_000)

        page.goto(f"{BASE}/app/courses", wait_until="networkidle")
        page.locator("h1").first.wait_for(state="visible")
        screenshot(page, "02-catalogue.png")

        visual_scenes = (
            ("mathematics-foundations", "Variables and Expressions", "03-mathematics.png"),
            ("physics-essentials", "Speed, Velocity, and Acceleration", "04-physics.png"),
            ("geography-physical-human", "Urbanisation and Megacities", "05-geography.png"),
            ("art-principles", "The Elements of Art", "06-art.png"),
        )
        for slug, lesson, image_name in visual_scenes:
            report["visuals"][slug] = open_visual(page, slug, lesson, image_name)

        # The last visual must survive a full reload from persisted chat context.
        page.reload(wait_until="networkidle")
        page.locator(".visual-card .js-plotly-plot").last.wait_for(state="visible", timeout=30_000)
        report["reload_visual_count"] = page.locator(".visual-card").count()

        # An explicit visual request exercises the named SSE event on the open tutor path.
        page.locator("#chat-input").fill("Show me this visually")
        page.locator("#chat-form .chat-send").click()
        page.locator(".msg-user", has_text="Show me this visually").wait_for(timeout=10_000)
        page.wait_for_function("document.querySelectorAll('.visual-card').length >= 2", timeout=90_000)
        report["explicit_request_visual_count"] = page.locator(".visual-card").count()

        # Check that the real browser exposes hover/zoom controls and tabular fallback.
        report["zoom_control"] = any(
            item["zoom_buttons"] for item in report["visuals"].values()
        )

        page.goto(f"{BASE}/app/chat/new?course=chess-foundations", wait_until="networkidle")
        page.locator(".chat-choice").first.click()
        page.locator(".chat-choice", has_text="Practise on the chessboard").click()
        board = page.locator(".chess-board").last
        board.wait_for(state="visible", timeout=30_000)
        board.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        screenshot(page, "07-chess.png")
        report["chess_squares"] = board.locator(".chess-square").count()

        page.goto(f"{BASE}/app/languages", wait_until="networkidle")
        page.locator(".chat-choice").first.wait_for(state="visible", timeout=30_000)
        screenshot(page, "08-languages.png")
        report["language_choices"] = page.locator(".chat-choice").count()

        # Responsive regression on a real chart; keep the image as supporting evidence.
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(f"{BASE}/app/chat/new?course=mathematics-foundations", wait_until="networkidle")
        page.locator(".chat-choice", has_text="Variables and Expressions").click()
        mobile_plot = page.locator(".visual-card .js-plotly-plot").last
        mobile_plot.wait_for(state="visible", timeout=30_000)
        mobile_plot.scroll_into_view_if_needed()
        page.screenshot(path=OUT.parent / "visualization-mobile.png", animations="disabled")
        box = mobile_plot.bounding_box()
        report["mobile_plot_width"] = round(box["width"], 1) if box else None

        context.close()
        browser.close()

    if report["console_errors"] or report["http_errors"]:
        raise RuntimeError(json.dumps(report, indent=2))
    if any(item["modebar_buttons"] < 1 or item["accessible_rows"] < 1 for item in report["visuals"].values()):
        raise RuntimeError(json.dumps(report, indent=2))
    if not report.get("zoom_control") or report["visuals"]["mathematics-foundations"]["hover_labels"] < 1:
        raise RuntimeError(json.dumps(report, indent=2))
    if report.get("chess_squares") != 64 or report.get("explicit_request_visual_count", 0) < 2:
        raise RuntimeError(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
