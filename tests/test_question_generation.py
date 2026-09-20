"""AI-assisted question generation and selection regressions."""

import asyncio

import pytest
from pydantic import ValidationError

import db
import question_generation


def _payload():
    variants = {}
    for language in question_generation.LANGUAGES:
        variants[language] = {
            "question_text": f"Which option correctly applies conservation? ({language})",
            "options": ["Atoms are conserved", "Atoms vanish", "Mass is optional"],
            "correct_answer": "Atoms are conserved",
            "explanation": "A balanced reaction preserves the number of atoms of each element.",
        }
    return {
        "canonical_language": "en",
        "required_languages": list(question_generation.LANGUAGES),
        "curriculum_outcome_ids": ["LESSON-GROUNDED"],
        "question_kind": "single_choice",
        "cognitive_process": "apply",
        "misconception_target": "Atoms can disappear.",
        "worked_solution": "Count each element on both sides; every atom remains present.",
        "safety_classification": "none",
        "scope_confirmation": "This stays within the supplied lesson and outcome.",
        "variants": variants,
    }


class _StructuredModel:
    def __init__(self, payload):
        self.payload = payload
        self.messages = None

    async def ainvoke(self, messages):
        self.messages = messages
        return self.payload


class _FakeModel:
    def __init__(self, payload):
        self.structured = _StructuredModel(payload)
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self.structured


def test_langchain_generator_returns_validated_multilingual_question():
    model = _FakeModel(_payload())
    lessons = {
        code: {"title": "Conservation", "content_md": "Atoms are conserved."}
        for code in question_generation.LANGUAGES
    }
    result = asyncio.run(question_generation.generate_question_set(
        model, lessons, 2, "Use a chemical equation."
    ))

    assert model.schema is question_generation.GeneratedQuestionSet
    assert set(result["variants"]) == set(question_generation.LANGUAGES)
    assert result["variants"]["en"]["correct_answer"] in result["variants"]["en"]["options"]
    assert "Use a chemical equation" in model.structured.messages[1].content


def test_generated_question_rejects_ambiguous_or_missing_answer_keys():
    invalid = _payload()
    invalid["variants"]["en"]["correct_answer"] = "A different answer"
    with pytest.raises(ValidationError):
        question_generation.GeneratedQuestionSet.model_validate(invalid)


def test_question_source_uses_reviewed_llm_pool_with_fixed_fallback():
    authored = {"id": 1, "source_type": "authored"}
    generated = {"id": 2, "source_type": "llm"}

    assert db.questions_for_source([authored, generated], "fixed") == [authored]
    assert db.questions_for_source([authored, generated], "llm_reviewed") == [generated]
    assert db.questions_for_source([authored], "llm_reviewed") == [authored]


def test_schema_tracks_toggle_and_generation_provenance():
    assert "question_source TEXT NOT NULL DEFAULT 'llm_reviewed'" in db.SCHEMA_SQL
    assert "source_type     TEXT NOT NULL DEFAULT 'authored'" in db.SCHEMA_SQL
    assert "generation_source TEXT NOT NULL DEFAULT 'template'" in db.SCHEMA_SQL
