"""Language-pair, dictionary, and graduated-recall regressions."""

from datetime import datetime, timedelta, timezone

import pytest

import language_learning as learning


def test_engine_has_ten_targets_including_chinese_and_arabic():
    assert len(learning.TARGET_LANGUAGE_CODES) == 10
    assert {"zh", "ar", "es"}.issubset(learning.TARGET_LANGUAGE_CODES)
    assert {"et", "lt"}.issubset(learning.NATIVE_LANGUAGE_CODES)


def test_frequency_dictionary_is_complete_and_ranked():
    data = learning.frequency_dictionary()
    assert len(data["items"]) == 30
    assert [item["rank"] for item in data["items"]] == list(range(1, 31))
    expected = set(learning.NATIVE_LANGUAGE_CODES)
    for item in data["items"]:
        assert set(item["forms"]) == expected
        assert all(form["text"] for form in item["forms"].values())
        for code in ("zh", "ar", "ja", "hi"):
            assert item["forms"][code]["romanization"]


def test_language_pair_must_be_supported_and_distinct():
    assert learning.validate_language_pair("et", "es") == ("et", "es")
    with pytest.raises(ValueError):
        learning.validate_language_pair("es", "es")
    with pytest.raises(ValueError):
        learning.validate_language_pair("xx", "ar")


def test_graduated_recall_expands_and_resets():
    now = datetime(2026, 9, 4, tzinfo=timezone.utc)
    first = learning.schedule_review(None, "good", now=now)
    second = learning.schedule_review(first["interval_step"], "good", now=now)
    reset = learning.schedule_review(second["interval_step"], "again", now=now)
    hard = learning.schedule_review(None, "hard", now=now)
    assert reset["next_due_at"] == now + timedelta(seconds=25)
    assert hard["interval_seconds"] < first["interval_seconds"]
    assert second["interval_seconds"] > first["interval_seconds"]
    assert reset["interval_step"] == 0
    assert not reset["success"]


def test_session_prioritises_due_then_unseen_and_excludes_future():
    now = datetime(2026, 9, 4, tzinfo=timezone.utc)
    reviews = [
        {"concept_id": "thank_you", "next_due_at": now - timedelta(seconds=1)},
        {"concept_id": "hello", "next_due_at": now + timedelta(days=1)},
    ]
    session = learning.build_session(
        reviews, native_language="en", target_language="es", now=now, limit=4
    )
    assert session[0]["id"] == "thank_you"
    assert "hello" not in {card["id"] for card in session}
    assert session[1]["id"] == "yes"
