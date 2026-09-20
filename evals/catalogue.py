"""Read-only catalogue adapters used by the evaluation corpus and runner."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import arts_catalog
import chess_course
import estonian_chemistry_catalog
import science_catalog


ROOT = Path(__file__).resolve().parents[1]


def _demo_courses() -> list[dict[str, Any]]:
    """Read the literal demo catalogue without executing seed.py side effects."""
    tree = ast.parse((ROOT / "seed.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "COURSES" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("seed.py does not define a literal COURSES catalogue")


def localized(value: Any, language: str = "en") -> Any:
    if not isinstance(value, dict):
        return value
    return value.get(language) or value.get("en") or next(iter(value.values()), "")


def _languages(*values: Any) -> list[str]:
    available: set[str] = set()
    for value in values:
        if isinstance(value, dict):
            available.update(value)
    ordered = [language for language in ("en", "et", "lt", "es") if language in available]
    return ordered or ["en"]


def catalogue_courses() -> list[dict[str, Any]]:
    """Return every authored course and lesson in a stable, localized shape."""
    courses: list[dict[str, Any]] = []
    sources = (
        ("demo", _demo_courses()),
        ("science", science_catalog.CATALOG),
        ("arts", arts_catalog.CATALOG),
        ("chess", chess_course.CATALOG),
    )
    for source, records in sources:
        for course in records:
            lessons: list[dict[str, Any]] = []
            lesson_number = 0
            for module in course.get("modules", []):
                for lesson in module.get("lessons", []):
                    lesson_number += 1
                    languages = _languages(lesson.get("title"), lesson.get("content_md"))
                    lessons.append({
                        "key": f"{course['slug']}:{lesson_number:03d}",
                        "index": lesson_number,
                        "module": {
                            language: str(localized(module.get("title", ""), language))
                            for language in languages
                        },
                        "title": {
                            language: str(localized(lesson.get("title", ""), language))
                            for language in languages
                        },
                        "content": {
                            language: str(localized(lesson.get("content_md", ""), language))
                            for language in languages
                        },
                        "languages": languages,
                        "outcome_codes": [],
                        "misconceptions": {},
                    })
            courses.append({
                "slug": course["slug"],
                "source": source,
                "title": str(localized(course.get("title", course["slug"]), "en")),
                "languages": _languages(course.get("title"), course.get("description")),
                "lessons": lessons,
            })

    topic_names = {code: {"et": et, "en": en} for code, et, en, *_ in estonian_chemistry_catalog.TOPICS}
    estonian_lessons = []
    for index, unit in enumerate(estonian_chemistry_catalog.ALL_UNITS, start=1):
        estonian_lessons.append({
            "key": f"{estonian_chemistry_catalog.COURSE_SLUG}:{unit.code}",
            "index": index,
            "module": topic_names[unit.topic],
            "title": {"en": unit.title_en, "et": unit.title_et},
            "content": {
                "en": estonian_chemistry_catalog._content(unit, "en"),
                "et": estonian_chemistry_catalog._content(unit, "et"),
            },
            "languages": ["en", "et"],
            "outcome_codes": [unit.outcome, *estonian_chemistry_catalog.EXTRA_UNIT_OUTCOMES.get(unit.code, ())],
            "key_ideas": {"en": unit.key_en, "et": unit.key_et},
            "misconceptions": {"en": unit.misconception_en, "et": unit.misconception_et},
        })
    courses.append({
        "slug": estonian_chemistry_catalog.COURSE_SLUG,
        "source": "estonian-curriculum",
        "title": "Estonian Grade 8 Chemistry",
        "languages": ["et", "en"],
        "lessons": estonian_lessons,
    })
    return courses


def course_index() -> dict[str, dict[str, Any]]:
    return {course["slug"]: course for course in catalogue_courses()}


def lesson_index() -> dict[str, dict[str, Any]]:
    return {
        lesson["key"]: {**lesson, "course_slug": course["slug"]}
        for course in catalogue_courses()
        for lesson in course["lessons"]
    }


def exercise_index() -> dict[str, dict[str, Any]]:
    """Return authored deterministic exercises in the same shape as production."""
    exercises = {exercise["source_key"]: exercise for exercise in science_catalog.EXERCISES}
    for unit in estonian_chemistry_catalog.ALL_UNITS:
        public, answer = estonian_chemistry_catalog._exercise_payload(unit, "et")
        exercises[f"ee-g8-{unit.code.lower()}"] = {
            "source_key": f"ee-g8-{unit.code.lower()}",
            "exercise_type": unit.kind,
            "answer": answer,
            "public": public,
        }
    return exercises
