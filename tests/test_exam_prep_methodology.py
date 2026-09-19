from pathlib import Path

from fasthtml.common import to_xml

from components.landing import (
    EXAM_PREP_METHODOLOGY_PDF_URL,
    EXAM_PREP_METHODOLOGY_URL,
    exam_prep_methodology_page,
    fastlearn_landing,
)


def test_exam_prep_methodology_has_the_agreed_scope_and_contents():
    methodology = Path("docs/exam_prep_methodology.md").read_text(encoding="utf-8")

    assert "## Table of contents" in methodology
    assert "UKiset 9–11" in methodology
    assert "UKiset 11–13" in methodology
    assert "UKiset 13–16" in methodology
    assert "## Mathematics: separate Foundation and Higher from launch" in methodology
    assert "fixed-difficulty mini mocks" in methodology
    assert "extrapolate the capability, never copy" in methodology
    assert "JUDGE_LLM" in methodology


def test_landing_links_the_public_html_methodology_page():
    markup = to_xml(fastlearn_landing("en"))

    assert EXAM_PREP_METHODOLOGY_URL == "/methodology"
    assert markup.count(EXAM_PREP_METHODOLOGY_URL) >= 2
    assert "Methodology" in markup


def test_methodology_html_offers_a_pdf_download():
    markup = to_xml(exam_prep_methodology_page("en"))

    assert "Table of contents" in markup
    assert EXAM_PREP_METHODOLOGY_PDF_URL in markup
    assert "Download PDF" in markup
    assert 'class="methodology-content"' in markup
    assert Path("docs/exam_prep_methodology.pdf").stat().st_size > 10_000
    assert Path("static/exam_prep_methodology.pdf").stat().st_size > 10_000
