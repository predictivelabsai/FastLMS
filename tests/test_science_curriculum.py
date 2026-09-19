"""Curriculum, chemistry grading, 3D, and privacy regressions."""

from pathlib import Path

from chemistry_engine import grade
from science_catalog import CATALOG, EXERCISES, public_exercise


def test_england_first_science_pathway_has_three_bilingual_courses():
    assert [course["slug"] for course in CATALOG] == [
        "primary-science", "chemistry-fundamentals", "advanced-chemistry",
    ]
    assert [course["difficulty"] for course in CATALOG] == ["beginner", "intermediate", "advanced"]
    for course in CATALOG:
        assert set(course["title"]) == {"en", "et"}
        assert course["modules"]
        for module in course["modules"]:
            assert set(module["title"]) == {"en", "et"}
            for lesson in module["lessons"]:
                assert set(lesson["title"]) == {"en", "et"}
                assert set(lesson["content_md"]) == {"en", "et"}


def test_primary_course_covers_materials_living_world_and_energy_earth():
    primary = CATALOG[0]
    module_titles = {module["title"]["en"] for module in primary["modules"]}
    assert module_titles == {
        "Working Scientifically", "Materials and Matter", "Living World", "Energy, Earth and Space",
    }


def test_chemistry_exercises_are_guided_and_answer_safe():
    assert {exercise["engine"] if "engine" in exercise else "chemistry" for exercise in EXERCISES} == {"chemistry"}
    assert {exercise["exercise_type"] for exercise in EXERCISES} >= {
        "atom_builder", "equation_balance", "molecule_geometry", "mole_calculation",
    }
    for exercise in EXERCISES:
        public = public_exercise(exercise, "et")
        assert "answer" not in public
        assert "tolerance" not in public
        assert public["engine"] == "chemistry"


def test_chemistry_grading_is_deterministic_and_server_compatible():
    assert grade("equation_balance", {"coefficients": [2, 1, 2]}, {"coefficients": [2, 1, 2]})["correct"]
    assert not grade("equation_balance", {"coefficients": [2, 1, 2]}, {"coefficients": [1, 1, 1]})["correct"]
    assert grade("atom_builder", {"protons": 11, "neutrons": 12, "electrons": 11}, {"protons": 11, "neutrons": 12, "electrons": 11})["correct"]
    assert grade("mole_calculation", {"value": 2.0, "tolerance": 0.01}, {"value": 2.005})["correct"]
    assert not grade("mole_calculation", {"value": 2.0}, {"value": "not a number"})["correct"]


def test_3d_chemistry_renderer_is_local_accessible_and_wired_to_chat():
    layout = Path("components/layout.py").read_text(encoding="utf-8")
    renderer = Path("static/chemistry.js").read_text(encoding="utf-8")
    chat = Path("static/chat.js").read_text(encoding="utf-8")
    assert 'src="/static/vendor/3Dmol-min.js"' in layout
    assert 'src="/static/chemistry.js"' in layout
    assert Path("static/vendor/3Dmol-min.js").stat().st_size > 500_000
    assert Path("static/vendor/3Dmol-LICENSE").is_file()
    assert "window.$3Dmol" in renderer
    assert "3D model unavailable" in renderer
    assert "FastLearnChemistry" in renderer
    assert "exercise.engine === 'chemistry'" in chat
    assert "submitInteractive" in chat


def test_bootstrap_and_api_dispatch_chemistry_without_exposing_answers():
    database = Path("db.py").read_text(encoding="utf-8")
    chat = Path("learning_chat.py").read_text(encoding="utf-8")
    api = Path("components/api.py").read_text(encoding="utf-8")
    assert "seed_science_courses(conn, SCHEMA)" in database
    assert "grade_chemistry" in chat
    assert "grade_chemistry" in api
    assert 'item.pop("answer_payload", None)' in database


def test_mobile_guided_content_bundle_is_public_and_answer_safe():
    api = Path("components/api.py").read_text(encoding="utf-8")
    assert '@api.get("/v1/lessons/{lesson_id}/guided-content"' in api
    assert '"exercises": exercises' in api
    assert '"visualizations": visuals' in api
    assert "include_answer=True" not in api.split("def lesson_guided_content", 1)[1].split(
        '@api.get("/v1/exercises/{exercise_id}"', 1
    )[0]
