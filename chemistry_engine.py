"""Deterministic grading for FastLearn's guided chemistry activities.

The browser only receives a scenario and never the expected answer.  This
module deliberately supports bounded, curriculum-authored tasks rather than a
free-form chemistry parser: that keeps primary learners safe and makes every
assessment replayable and explainable.
"""

from __future__ import annotations

from math import isclose
from typing import Any


def _integer_list(value: Any) -> list[int] | None:
    if not isinstance(value, list) or not value:
        return None
    result: list[int] = []
    for item in value:
        try:
            number = int(item)
        except (TypeError, ValueError):
            return None
        if number < 0 or number > 99:
            return None
        result.append(number)
    return result


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) < 1_000_000 else None


def grade(exercise_type: str, expected: dict[str, Any], answer: dict[str, Any]) -> dict[str, bool]:
    """Grade one bounded chemistry activity without trusting browser state."""
    if not isinstance(expected, dict) or not isinstance(answer, dict):
        return {"correct": False, "completed": False, "optimal": False}

    correct = False
    if exercise_type in {"multiple_choice", "material_sort", "molecule_geometry", "spectra_choice", "mechanism_choice"}:
        correct = answer.get("choice") == expected.get("choice")
    elif exercise_type == "equation_balance":
        submitted = _integer_list(answer.get("coefficients"))
        wanted = _integer_list(expected.get("coefficients"))
        correct = submitted == wanted
    elif exercise_type == "atom_builder":
        correct = all(
            isinstance(expected.get(key), int) and answer.get(key) == expected[key]
            for key in ("protons", "electrons", "neutrons")
        )
    elif exercise_type == "mole_calculation":
        submitted = _number(answer.get("value"))
        wanted = _number(expected.get("value"))
        tolerance = _number(expected.get("tolerance"))
        correct = bool(
            submitted is not None and wanted is not None and
            isclose(submitted, wanted, rel_tol=0, abs_tol=tolerance if tolerance is not None else 0.01)
        )

    return {"correct": correct, "completed": correct, "optimal": correct}
