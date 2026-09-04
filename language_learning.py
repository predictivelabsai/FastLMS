"""Frequency-informed, audio-first language practice for FastLearn.

The engine uses original multilingual content and general instructional ideas:
anticipation, speaking aloud, high-frequency expressions, and graduated-interval
recall. It does not contain or reproduce any proprietary language course.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping


TARGET_LANGUAGE_CODES = ("en", "es", "fr", "de", "it", "pt", "zh", "ar", "ja", "hi")
NATIVE_LANGUAGE_CODES = TARGET_LANGUAGE_CODES + ("et", "lt")

LANGUAGE_META = {
    "en": {"name": "English", "autonym": "English", "flag": "🇬🇧", "voice": "en-US", "direction": "ltr"},
    "es": {"name": "Spanish", "autonym": "Español", "flag": "🇪🇸", "voice": "es-ES", "direction": "ltr"},
    "fr": {"name": "French", "autonym": "Français", "flag": "🇫🇷", "voice": "fr-FR", "direction": "ltr"},
    "de": {"name": "German", "autonym": "Deutsch", "flag": "🇩🇪", "voice": "de-DE", "direction": "ltr"},
    "it": {"name": "Italian", "autonym": "Italiano", "flag": "🇮🇹", "voice": "it-IT", "direction": "ltr"},
    "pt": {"name": "Portuguese", "autonym": "Português", "flag": "🇵🇹", "voice": "pt-PT", "direction": "ltr"},
    "zh": {"name": "Mandarin Chinese", "autonym": "中文", "flag": "🇨🇳", "voice": "zh-CN", "direction": "ltr"},
    "ar": {"name": "Arabic", "autonym": "العربية", "flag": "🇸🇦", "voice": "ar-SA", "direction": "rtl"},
    "ja": {"name": "Japanese", "autonym": "日本語", "flag": "🇯🇵", "voice": "ja-JP", "direction": "ltr"},
    "hi": {"name": "Hindi", "autonym": "हिन्दी", "flag": "🇮🇳", "voice": "hi-IN", "direction": "ltr"},
    "et": {"name": "Estonian", "autonym": "Eesti", "flag": "🇪🇪", "voice": "et-EE", "direction": "ltr"},
    "lt": {"name": "Lithuanian", "autonym": "Lietuvių", "flag": "🇱🇹", "voice": "lt-LT", "direction": "ltr"},
}

# Deliberately short initial intervals make anticipation and recall visible in a
# live session; successful material then expands out to roughly three months.
RECALL_INTERVALS_SECONDS = (25, 120, 600, 3600, 18_000, 86_400, 432_000, 2_160_000, 7_776_000)
VALID_RATINGS = ("again", "hard", "good")


@lru_cache(maxsize=1)
def frequency_dictionary() -> dict:
    path = Path(__file__).resolve().parent / "data" / "language_frequency.json"
    return json.loads(path.read_text(encoding="utf-8"))


def language_label(code: str) -> str:
    meta = LANGUAGE_META[code]
    return f"{meta['flag']} {meta['autonym']}"


def validate_language_pair(native_language: str, target_language: str) -> tuple[str, str]:
    native = str(native_language or "").lower()
    target = str(target_language or "").lower()
    if native not in NATIVE_LANGUAGE_CODES or target not in TARGET_LANGUAGE_CODES or native == target:
        raise ValueError("choose two different supported languages")
    return native, target


def default_language_pair(interface_language: str = "en") -> tuple[str, str]:
    native = interface_language if interface_language in NATIVE_LANGUAGE_CODES else "en"
    target = "en" if native == "es" else "es"
    return native, target


def schedule_review(
    interval_step: int | None,
    rating: str,
    *,
    now: datetime | None = None,
) -> dict:
    """Return the next deterministic graduated-recall state."""
    if rating not in VALID_RATINGS:
        raise ValueError("unsupported recall rating")
    now = now or datetime.now(timezone.utc)
    current = max(0, min(int(interval_step if interval_step is not None else 0), len(RECALL_INTERVALS_SECONDS) - 1))
    if rating == "again":
        next_step = 0
        seconds = RECALL_INTERVALS_SECONDS[0]
        success = False
    elif rating == "hard":
        next_step = current
        seconds = max(60, RECALL_INTERVALS_SECONDS[next_step] // 2)
        success = True
    else:
        next_step = min(current + 1, len(RECALL_INTERVALS_SECONDS) - 1)
        seconds = RECALL_INTERVALS_SECONDS[next_step]
        success = True
    return {
        "interval_step": next_step,
        "interval_seconds": seconds,
        "next_due_at": now + timedelta(seconds=seconds),
        "success": success,
    }


def _normalise_due(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def build_session(
    reviews: Iterable[Mapping],
    *,
    native_language: str,
    target_language: str,
    now: datetime | None = None,
    limit: int = 8,
) -> list[dict]:
    """Mix due reviews with unseen high-frequency expressions."""
    native, target = validate_language_pair(native_language, target_language)
    now = now or datetime.now(timezone.utc)
    states = {str(row["concept_id"]): dict(row) for row in reviews}
    items = frequency_dictionary()["items"]
    due = []
    unseen = []
    for item in items:
        state = states.get(item["id"])
        card = {
            **item,
            "native": item["forms"][native],
            "target": item["forms"][target],
            "native_language": native,
            "target_language": target,
            "target_meta": LANGUAGE_META[target],
            "review": state,
        }
        if state is None:
            unseen.append(card)
            continue
        due_at = _normalise_due(state.get("next_due_at"))
        card["next_due_at"] = due_at
        if due_at is None or due_at <= now:
            due.append(card)
        # Future cards stay out of the active queue until their interval elapses.
    due.sort(key=lambda card: (card.get("next_due_at") or now, card["rank"]))
    unseen.sort(key=lambda card: card["rank"])
    # Reviews come first; unseen material then follows frequency rank.
    session = due + unseen[: max(0, limit - len(due))]
    return session[: max(1, int(limit))]


def dictionary_summary() -> dict:
    data = frequency_dictionary()
    return {
        "target_languages": len(data["target_languages"]),
        "native_languages": len(data["target_languages"]) + len(data.get("native_only_languages", [])),
        "expressions": len(data["items"]),
        "method": data["method"],
    }
