#!/usr/bin/env python3
"""Build the FastLearn guide as consistent two-column landscape pages."""

from __future__ import annotations

import html
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE = DOCS / "fastlearn_platform_guide.md"
STYLES = DOCS / "fastlearn_platform_guide.css"
OUTPUT = DOCS / "fastlearn_platform_guide.pdf"

HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
ROLE_DIVIDERS = {
    "4. Student guide": "Student",
    "5. Teacher guide": "Teacher",
    "6. Administrator guide": "Administrator",
}


@dataclass
class Section:
    level: int
    title: str
    content: str


FALLBACK_IMAGES = (
    ("contents", "img/fastlearn-platform-guide/03-student-course-catalogue.png"),
    ("platform", "img/fastlearn-platform-guide/01-home.png"),
    ("role", "img/fastlearn-platform-guide/10-team.png"),
    ("access", "img/fastlearn-platform-guide/10-team.png"),
    ("signing", "img/fastlearn-platform-guide/02-sign-in.png"),
    ("student guide", "img/fastlearn-platform-guide/03-student-course-catalogue.png"),
    ("start in new chat", "img/fastlearn-platform-guide/07-student-ai-tutor.png"),
    ("browse", "img/fastlearn-platform-guide/03-student-course-catalogue.png"),
    ("open a course", "img/fastlearn-platform-guide/04-student-course-path.png"),
    ("study a lesson", "img/fastlearn-platform-guide/05-student-lesson.png"),
    ("quiz", "img/fastlearn-platform-guide/06-student-quiz.png"),
    ("visual", "../output/playwright/16-interactive-visual.png"),
    ("chess", "../output/playwright/15-chess-guided-practice.png"),
    ("active learning time", "img/fastlearn-platform-guide/12-learning-reports.png"),
    ("adaptive", "img/fastlearn-platform-guide/11-adaptive-strategy.png"),
    ("graduated recall", "img/fastlearn-platform-guide/13-language-learning.png"),
    ("language", "img/fastlearn-platform-guide/13-language-learning.png"),
    ("teacher workspace", "../output/playwright/teacher-chat.png"),
    ("teacher guide", "../output/playwright/teacher-chat.png"),
    ("manage courses", "img/fastlearn-platform-guide/08-teacher-manage-courses.png"),
    ("build and publish", "img/fastlearn-platform-guide/09-teacher-course-setup.png"),
    ("invite", "img/fastlearn-platform-guide/10-team.png"),
    ("learning strategy", "img/fastlearn-platform-guide/11-adaptive-strategy.png"),
    ("generate material", "img/fastlearn-platform-guide/11-adaptive-strategy.png"),
    ("progress and time", "img/fastlearn-platform-guide/12-learning-reports.png"),
    ("administrator", "img/fastlearn-platform-guide/10-team.png"),
    ("data and audit", "img/fastlearn-platform-guide/12-learning-reports.png"),
    ("authentication", "img/fastlearn-platform-guide/02-sign-in.png"),
    ("chat, visuals", "../output/playwright/16-interactive-visual.png"),
    ("integration api", "../output/playwright/16-interactive-visual.png"),
    ("quick reference", "img/fastlearn-platform-guide/01-home.png"),
)


def markdown_html(markdown: str) -> str:
    result = subprocess.run(
        ["pandoc", "--from=gfm", "--to=html5", "--wrap=none"],
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
        cwd=DOCS,
    )
    return result.stdout.strip()


def split_document(source: str) -> tuple[str, list[Section]]:
    matches = list(HEADING.finditer(source))
    if not matches:
        raise ValueError("platform guide needs level-two sections")
    preamble = source[: matches[0].start()].strip()
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        sections.append(Section(len(match.group(1)), match.group(2), source[match.end():end].strip()))
    return preamble, merge_sections(sections)


def merge_sections(sections: list[Section]) -> list[Section]:
    """Avoid sparse chapter-divider pages while preserving meaningful spreads."""
    merged: list[Section] = []
    index = 0
    while index < len(sections):
        section = sections[index]
        if section.title.startswith("1. Platform overview") and index + 1 < len(sections):
            following = sections[index + 1]
            if following.title == "Platform capabilities":
                section = Section(2, section.title, f"{section.content}\n\n### {following.title}\n\n{following.content}")
                index += 1
        if section.title == "Quick reference":
            parts = [section.content]
            cursor = index + 1
            while cursor < len(sections) and sections[cursor].level == 3:
                parts.append(f"### {sections[cursor].title}\n\n{sections[cursor].content}")
                cursor += 1
            section = Section(2, section.title, "\n\n".join(part for part in parts if part))
            index = cursor - 1
        if section.title.startswith("4.11 Learn another language") and "#### How practice works" in section.content:
            selection, practice = section.content.split("#### How practice works", 1)
            merged.append(Section(section.level, section.title, selection.strip()))
            merged.append(Section(section.level, "4.12 Practise with graduated recall", practice.strip()))
            index += 1
            continue
        if section.content or section.title == "Contents":
            merged.append(section)
        index += 1
    return merged


def fallback_image(title: str) -> str:
    normalized = title.casefold()
    return next((path for keyword, path in FALLBACK_IMAGES if keyword in normalized), "img/fastlearn-platform-guide/01-home.png")


def extract_media(section: Section) -> tuple[str, str, str]:
    images = IMAGE.findall(section.content)
    content = IMAGE.sub("", section.content).strip()
    if images:
        alt, path = images[0]
    else:
        alt, path = f"FastLearn: {section.title}", fallback_image(section.title)
    image_file = (DOCS / path).resolve()
    if not image_file.is_file():
        raise FileNotFoundError(f"Missing guide image: {image_file}")
    return content, alt, path


def chapter_label(title: str) -> str:
    if title in ROLE_DIVIDERS:
        return "Role guide"
    if title.startswith("A."):
        return "Developer appendix"
    match = re.match(r"(\d+)\.", title)
    chapters = {"4": "Student guide", "5": "Teacher guide", "6": "Administrator guide"}
    return chapters.get(match.group(1), "") if match else ""


def page(section: Section) -> str:
    content, alt, image_path = extract_media(section)
    eyebrow = chapter_label(section.title)
    eyebrow_html = f'<p class="eyebrow">{html.escape(eyebrow)}</p>' if eyebrow else ""
    copy = markdown_html(content) if content else ""
    classes = "guide-page divider-page" if section.title in ROLE_DIVIDERS else "guide-page"
    return f"""
<section class="{classes}">
  <div class="guide-copy">
    {eyebrow_html}<h2>{html.escape(section.title)}</h2>
    {copy}
  </div>
  <div class="guide-media">
    <figure>
      <img src="{html.escape(image_path)}" alt="{html.escape(alt)}">
      <figcaption>{html.escape(alt)}</figcaption>
    </figure>
  </div>
</section>"""


def cover(preamble: str) -> str:
    without_title = re.sub(r"^#\s+.+?\n", "", preamble, count=1).strip()
    return f"""
<section class="guide-page cover-page">
  <div class="guide-copy">
    <p class="eyebrow">FastLearn · Product guide</p>
    <h1>FastLearn Platform Guide</h1>
    {markdown_html(without_title)}
  </div>
  <div class="guide-media">
    <figure>
      <img src="img/fastlearn-platform-guide/01-home.png" alt="FastLearn landing page">
      <figcaption>FastLearn — one clear step at a time</figcaption>
    </figure>
  </div>
</section>"""


def build() -> None:
    preamble, sections = split_document(SOURCE.read_text(encoding="utf-8"))
    document = "\n".join([cover(preamble), *(page(section) for section in sections)])
    output_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>FastLearn Platform Guide</title>
  <link rel="stylesheet" href="{STYLES.name}">
</head>
<body>{document}</body>
</html>
"""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", prefix="fastlearn-guide-", dir=DOCS, encoding="utf-8", delete=False) as handle:
            handle.write(output_html)
            temporary = Path(handle.name)
        subprocess.run(["weasyprint", str(temporary), str(OUTPUT)], cwd=DOCS, check=True)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
