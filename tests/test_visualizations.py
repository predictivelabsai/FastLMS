"""Visualization contract, accessibility, streaming, and approval regressions."""

import json
from pathlib import Path

import visualizations


EXPECTED_LESSONS = {
    "Variables and Expressions",
    "Solving Linear Equations",
    "Shapes, Area, and Perimeter",
    "Speed, Velocity, and Acceleration",
    "Newton's Laws of Motion",
    "Plate Tectonics and Earthquakes",
    "Urbanisation and Megacities",
    "The Elements of Art",
    "Composition and Visual Meaning",
}


def test_curated_visual_library_covers_the_agreed_subject_lessons():
    assert {lesson for _slug, lesson in visualizations.BUILDERS} == EXPECTED_LESSONS
    assert {slug for slug, _lesson in visualizations.BUILDERS} == {
        "mathematics-foundations", "physics-essentials",
        "geography-physical-human", "art-principles",
    }


def test_every_visual_is_localized_accessible_and_json_safe():
    for (slug, lesson), builder in visualizations.BUILDERS.items():
        english = builder("en")
        assert visualizations.curated(slug, lesson, "en") == [english]
        for lang in visualizations.LANGUAGES:
            spec = builder(lang)
            assert visualizations.validate(spec) == spec
            assert spec["audience"] == {"min_age": 8, "max_age": 16}
            assert spec["alt_text"]
            assert spec["ui"]["accessible_data"]
            assert spec["ui"]["load_error"]
            assert spec["table"]["columns"]
            assert spec["table"]["rows"]
            assert json.loads(json.dumps(spec)) == spec
            assert all(trace.get("type", "scatter") in visualizations.TRACE_TYPES for trace in spec["data"])


def test_visual_requests_are_explicit_and_do_not_hijack_normal_chat():
    assert visualizations.wants_visual("Show me this as a graph")
    assert visualizations.wants_visual("Can you visualise the equation?")
    assert visualizations.wants_visual("Draw it as a diagram")
    assert not visualizations.wants_visual("Explain the equation more simply")


def test_clone_titles_can_reuse_curated_templates():
    assert visualizations.curated("teacher-copy", "Newton's Laws of Motion", "en")


def test_chat_stream_uses_a_typed_visualization_event_and_safe_renderer():
    main_source = Path("main.py").read_text(encoding="utf-8")
    client_source = Path("static/chat.js").read_text(encoding="utf-8")
    renderer_source = Path("static/visualizations.js").read_text(encoding="utf-8")
    layout_source = Path("components/layout.py").read_text(encoding="utf-8")
    assert 'event: visualization' in main_source
    assert "eventType === 'visualization'" in client_source
    assert "FastLearnVisualizations" in client_source
    assert "Plotly.react" in renderer_source
    assert "textContent" in renderer_source
    assert "innerHTML" not in renderer_source
    assert "/static/vendor/plotly-3.6.0.min.js" in layout_source
    assert "cdn.plot.ly" not in layout_source


def test_saved_visuals_follow_the_existing_teacher_approval_flow():
    schema = Path("db.py").read_text(encoding="utf-8")
    routes = Path("main.py").read_text(encoding="utf-8")
    assert "lesson_visualizations" in schema
    assert 'value="visualization"' in routes
    assert 'draft["draft_type"] == "visualization"' in routes
    assert "visualizations.validate(english)" in routes


def test_chat_reload_order_is_deterministic_for_same_transaction_messages():
    source = Path("db.py").read_text(encoding="utf-8")
    assert source.count("ORDER BY created_at ASC, id ASC LIMIT :lim") == 3
