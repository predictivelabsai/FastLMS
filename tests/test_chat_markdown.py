"""AI tutor Markdown rendering regressions."""

from pathlib import Path

from components.chat_markdown import render_chat_markdown


def test_tutor_markdown_is_rendered_as_structured_html():
    source = """**Great!** Let's learn.

### Addition (+)

Combining numbers.

```text
7 + 5 = 12
```
1. First
2. Second
"""
    rendered = render_chat_markdown(source)

    assert "<strong>Great!</strong>" in rendered
    assert "<h3>Addition (+)</h3>" in rendered
    assert "<pre><code" in rendered
    assert "<ol>" in rendered
    assert "**Great!**" not in rendered
    assert "### Addition" not in rendered


def test_tutor_markdown_strips_unsafe_model_html_and_links():
    source = '<script>alert("x")</script> [unsafe](javascript:alert(1))'
    rendered = render_chat_markdown(source)

    assert "<script" not in rendered
    assert "javascript:" not in rendered
    assert "href=" not in rendered


def test_chat_client_uses_server_rendered_html_without_cdn_parser():
    script = Path("static/chat.js").read_text(encoding="utf-8")
    layout = Path("components/layout.py").read_text(encoding="utf-8")

    assert "data.html" in script
    assert "marked.parse" not in script
    assert "marked.min.js" not in layout
