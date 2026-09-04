"""Safe Markdown rendering for AI tutor responses."""

import re

import bleach
import markdown


_ALLOWED_TAGS = {
    "a",
    "blockquote",
    "br",
    "code",
    "del",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}

_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "td": ["align"],
    "th": ["align"],
}

_LIST_ITEM = re.compile(r"^(?:[-+*]|\d+[.)])\s+")


def _normalise_model_markdown(source: str) -> str:
    """Accept the compact lists that chat models commonly emit."""
    lines = source.splitlines()
    normalised: list[str] = []
    fence = None
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else marker
        if (
            fence is None
            and _LIST_ITEM.match(stripped)
            and normalised
            and normalised[-1].strip()
            and not _LIST_ITEM.match(normalised[-1].lstrip())
        ):
            normalised.append("")
        normalised.append(line)
    return "\n".join(normalised)


def render_chat_markdown(source: str | None) -> str:
    """Turn model-authored Markdown into a small, safe HTML subset."""
    rendered = markdown.markdown(
        _normalise_model_markdown(source or ""),
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
        output_format="html",
    )
    return bleach.clean(
        rendered,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        strip=True,
        strip_comments=True,
    )
