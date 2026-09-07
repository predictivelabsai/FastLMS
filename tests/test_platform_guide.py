"""Presentation invariants for the README and generated platform guide."""

import re
from pathlib import Path


def test_readme_embeds_one_canonical_walkthrough():
    readme = Path("README.md").read_text(encoding="utf-8")
    embedded_gifs = re.findall(r"!\[[^\]]*\]\(([^)]+\.gif)\)", readme)
    assert embedded_gifs == ["static/fastlearn-demo.gif"]


def test_platform_guide_source_keeps_presentation_copy_only():
    guide = Path("docs/fastlearn_platform_guide.md").read_text(encoding="utf-8")
    assert "## Contents" in guide
    assert guide.index("## Quick reference") < guide.index("## 1. Platform overview")
    assert "## Appendix: Developers" in guide
    assert "https://fastlearn.fun/auth/google/callback" in guide.split("## Appendix: Developers", 1)[1]
    assert "https://fastlearn.fun/auth/google/callback" not in guide.split("## Appendix: Developers", 1)[0]
    assert "Available editions:" not in guide
    assert "Screenshots were reviewed" not in guide


def test_platform_guide_layout_is_two_column_landscape():
    css = Path("docs/fastlearn_platform_guide.css").read_text(encoding="utf-8")
    builder = Path("scripts/build_platform_guide.py").read_text(encoding="utf-8")
    assert "size: A4 landscape" in css
    assert "grid-template-columns:" in css
    assert "border-left:" in css
    assert "@page cover" in css
    assert css.count("content: counter(page);") == 2
    assert ".cover-page { page: cover; }" in css
    assert ".divider-page h2" in css
    assert 'class="guide-page cover-page"' in builder
    assert '"guide-page divider-page"' in builder
    assert builder.count("<h1>FastLearn Platform Guide</h1>") == 1
