"""Regressions for the Estonia Grade 8 chemistry reference implementation."""

import estonian_chemistry_catalog as catalog
import question_generation
import visualizations
from chemistry_engine import grade
from components.api import _grade_exercise


def test_course_has_zero_knowledge_prelude_and_exact_formal_pacing():
    assert len(catalog.PRELUDE_UNITS) == 12
    assert len(catalog.FORMAL_UNITS) == 35
    assert sum(unit.periods for unit in catalog.FORMAL_UNITS) == 70
    assert catalog.fixed_question_count() == 515
    assert sum(topic[3] for topic in catalog.TOPICS) == 70
    assert catalog.PRELUDE_UNITS[0].code == "P01"
    assert catalog.PRELUDE_UNITS[-1].code == "P12"


def test_every_atomic_outcome_is_mapped_and_grade_9_scope_is_excluded():
    mapped = {
        outcome
        for unit in catalog.ALL_UNITS
        for outcome in (unit.outcome, *catalog.EXTRA_UNIT_OUTCOMES.get(unit.code, ()))
    }
    expected = {code for _topic, code, _description in catalog.OUTCOMES}
    assert mapped == expected
    assert "moolarvutused" not in " ".join(unit.key_et.lower() for unit in catalog.FORMAL_UNITS)
    assert catalog.PROGRAM_CODE.startswith("EE-PROK")


def test_estonian_is_canonical_and_english_is_the_only_support_translation():
    assert catalog.COURSE_SLUG == "ee-grade-8-chemistry"
    assert "riigiteataja.ee" in " ".join(source["url"] for source in catalog.SOURCE_URLS)
    context = {
        "country_code": "EE",
        "jurisdiction_code": "EE",
        "program_code": catalog.PROGRAM_CODE,
        "version": catalog.CURRICULUM_VERSION,
        "grade_code": "8",
        "canonical_language": "et",
        "supported_languages": ["et", "en"],
        "outcome_codes": ["EE-PROK-CHEM-G8-PRE-06"],
        "excluded_scope": ["moolarvutused", "süsinikuühendid"],
    }
    prompt = question_generation.generation_prompt(
        {"et": {"title": "Sümbolid", "content_md": "Na on naatrium."}},
        1,
        curriculum_context=context,
        required_languages=["et", "en"],
    )
    assert "Canonical language: et" in prompt
    assert "Required languages: et, en" in prompt
    assert "moolarvutused" in prompt


def test_guided_exercises_cover_notation_calculation_atoms_and_equations():
    kinds = {unit.kind for unit in catalog.ALL_UNITS}
    assert {"multiple_choice", "short_answer", "formula_builder", "numeric_calculation",
            "atom_builder", "equation_balance"} <= kinds
    public, answer = catalog._exercise_payload(catalog.PRELUDE_UNITS[6], "et")
    assert public["molecule"] == "water"
    assert grade("formula_builder", answer, {"text": "H₂O"})["correct"]
    numeric_public, numeric_answer = catalog._exercise_payload(catalog.PRELUDE_UNITS[8], "et")
    assert grade("numeric_calculation", numeric_answer, {"value": 20})["correct"]


def test_exercise_check_returns_localized_explanatory_feedback():
    _public, answer = catalog._exercise_payload(catalog.PRELUDE_UNITS[0], "et")
    exercise = {
        "engine": "chemistry",
        "exercise_type": "multiple_choice",
        "answer_payload": answer,
    }
    verdict = _grade_exercise(exercise, {"choice": answer["choice"]}, "et")
    assert verdict["correct"] is True
    assert verdict["correct_answer"]
    assert verdict["explanation"].startswith("Õige vastus")


def test_estonian_visuals_are_localized_and_accessible():
    visual = visualizations.curated("ee-grade-8-chemistry", "pH ja indikaatorid", "et")[0]
    assert visual["renderer"] == "plotly"
    assert visual["table"]["columns"]
    assert visual["alt_text"]
    assert "happelist" in visual["title"]
