#!/usr/bin/env python3
"""Render the public Exam Prep methodology Markdown as a self-contained PDF."""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "exam_prep_methodology.md"
OUTPUT = ROOT / "docs" / "exam_prep_methodology.pdf"
STATIC_OUTPUT = ROOT / "static" / OUTPUT.name
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,3})\s+(.+)$")
ORDERED = re.compile(r"^\d+\.\s+(.+)$")


def inline(value: str) -> str:
    """Escape text while retaining the document's ordinary Markdown links."""
    escaped = html.escape(value)
    linked = LINK.sub(lambda match: (
        f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>'
    ), escaped)
    linked = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", linked)
    return re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", linked)


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")


def markdown_html(markdown: str) -> str:
    """Render the small, deliberately conventional Markdown subset used here."""
    result: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            result.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_type
        if list_type:
            result.append(f"</{list_type}>")
            list_type = None

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        heading = HEADING.match(line)
        is_bullet = line.startswith("- ")
        ordered = ORDERED.match(line)
        if list_type and raw_line[:1].isspace() and line and result[-1].startswith("<li>"):
            # Markdown continuations in the source are indented for readable
            # source text. Keep them in the preceding list item in the PDF.
            result[-1] = f"{result[-1][:-5]} {inline(line)}</li>"
        elif heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            title = heading.group(2)
            result.append(f'<h{level} id="{slug(title)}">{inline(title)}</h{level}>')
        elif not line:
            flush_paragraph()
            flush_list()
        elif is_bullet or ordered:
            flush_paragraph()
            requested = "ul" if is_bullet else "ol"
            if list_type and list_type != requested:
                flush_list()
            if not list_type:
                result.append(f"<{requested}>")
                list_type = requested
            item = line[2:] if is_bullet else ordered.group(1)
            result.append(f"<li>{inline(item)}</li>")
        else:
            flush_list()
            paragraph.append(line)
    flush_paragraph()
    flush_list()
    return "\n".join(result)


def build() -> None:
    body = markdown_html(SOURCE.read_text(encoding="utf-8"))
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>FastLearn Exam Prep Methodology</title>
<style>
@page {{ size: A4; margin: 16mm 15mm 18mm; @bottom-center {{ content: "FastLearn Exam Prep Methodology · " counter(page); color: #64748b; font: 8pt sans-serif; }} }}
* {{ box-sizing: border-box; }} body {{ color: #172033; font: 10pt/1.52 Arial, sans-serif; max-width: 178mm; margin: auto; }}
h1 {{ color: #0f766e; font-size: 26pt; line-height: 1.1; margin: 0 0 9mm; }} h2 {{ color: #0f4c5c; font-size: 17pt; line-height: 1.2; border-bottom: 1px solid #cbd5e1; margin: 11mm 0 4mm; padding-bottom: 2mm; break-after: avoid; }} h3 {{ color: #155e75; font-size: 12pt; margin: 6mm 0 2mm; break-after: avoid; }}
p {{ margin: 0 0 3.3mm; }} ul, ol {{ margin: 0 0 3.3mm 5mm; padding-left: 5mm; }} li {{ margin: 1.3mm 0; }} a {{ color: #0369a1; text-decoration: none; }} h2:first-of-type {{ break-before: page; }}
</style></head><body>{body}</body></html>"""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", prefix="exam-prep-methodology-", encoding="utf-8", delete=False) as handle:
            handle.write(document)
            temporary = Path(handle.name)
        subprocess.run([
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
            "--no-pdf-header-footer", f"--print-to-pdf={OUTPUT}", temporary.as_uri(),
        ], check=True)
        shutil.copyfile(OUTPUT, STATIC_OUTPUT)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    print(f"Wrote {OUTPUT} and {STATIC_OUTPUT}")


if __name__ == "__main__":
    build()
