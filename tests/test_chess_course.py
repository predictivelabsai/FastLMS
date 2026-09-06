"""Chess curriculum, grading, chat-contract, and API safety regressions."""

from pathlib import Path

from chess_course import CATALOG, CHESS_COURSES, CHESS_TRANSLATIONS, EXERCISES, public_exercise
from chess_engine import grade, shortest_route_length


def _exercise(source_key):
    return next(item for item in EXERCISES if item["source_key"] == source_key)


def test_chess_foundations_is_original_child_focused_and_complete_for_v1():
    course = CATALOG[0]
    assert course["slug"] == "chess-foundations"
    assert len(course["modules"]) == 3
    assert sum(len(module["lessons"]) for module in course["modules"]) == 10
    assert len(EXERCISES) == 20
    assert {item["exercise_type"] for item in EXERCISES} == {
        "multiple_choice", "select_squares", "place_pieces", "path", "move_sequence",
    }
    assert "ages 3–12" in CHESS_COURSES[0]["description"]
    assert all("needs-human-review" not in lesson["content_md"]["en"] for module in course["modules"] for lesson in module["lessons"])


def test_chess_curriculum_and_prompts_cover_every_demo_language():
    for module in CATALOG[0]["modules"]:
        assert set(module["title"]) == {"en", "et", "lt", "es"}
        for lesson in module["lessons"]:
            assert set(lesson["title"]) == {"en", "et", "lt", "es"}
            assert set(lesson["content_md"]) == {"en", "et", "lt", "es"}
    assert all(set(item["prompt"]) == {"en", "et", "lt", "es"} for item in EXERCISES)
    assert len(CHESS_TRANSLATIONS["courses"]) == 1
    assert len(CHESS_TRANSLATIONS["lessons"]) == 10


def test_public_exercise_never_contains_an_answer_key():
    public = public_exercise(_exercise("fl-chess-02b"), "et")
    assert public["prompt"].startswith("Vali")
    assert "answer" not in public
    assert "targets" not in public
    assert "placements" not in public
    assert "solution" not in public


def test_all_supported_exercise_types_are_graded_server_side():
    assert grade("multiple_choice", None, {"answer": 1}, {"answer": 1})["correct"]
    assert grade("select_squares", None, {"targets": ["a1", "b2"]}, {"squares": ["b2", "a1"]})["correct"]
    assert grade("place_pieces", None, {"placements": [{"square": "a1", "piece": "R"}]}, {"placements": [{"piece": "R", "square": "a1"}]})["correct"]
    path = grade("path", "8/8/8/8/8/8/8/R7 w - - 0 1", {"goal": "h8", "optimal_len": 2}, {"moves": ["a1a8", "a8h8"]})
    assert path == {"correct": True, "completed": True, "optimal": True}
    capture = grade("move_sequence", "r6n/8/8/8/3p3b/8/8/R7 w - - 0 1", {"capture_all": True}, {"moves": ["a1a8", "a8h8", "h8h4", "h4d4"]})
    assert capture["correct"]
    assert not grade("multiple_choice", None, {"answer": 1}, {"answer": 0})["correct"]
    assert shortest_route_length("8/8/8/8/8/8/8/R7 w - - 0 1", "h8") == 2


def test_chat_client_supports_rich_board_submission_and_sse_results():
    script = Path("static/chat.js").read_text(encoding="utf-8")
    assert "mountInteractive" in script
    assert "/app/chat/exercise/stream" in script
    assert "data.interactive" in script
    assert "duration_seconds" in script
    source = Path("main.py").read_text(encoding="utf-8")
    assert '@app.post("/app/chat/exercise/stream")' in source
    assert "'interactive': guided.get('interactive')" in source


def test_database_keeps_public_and_private_exercise_payloads_apart():
    source = Path("db.py").read_text(encoding="utf-8")
    assert "interactive_exercises" in source
    assert "public_payload" in source
    assert "answer_payload" in source
    assert 'item.pop("answer_payload", None)' in source
    assert "exercise_attempts" in source
    assert all(";" not in line for line in source.splitlines() if line.lstrip().startswith("--"))


def test_api_protects_learner_data_and_exposes_answer_safe_exercises():
    source = Path("components/api.py").read_text(encoding="utf-8")
    assert '@api.get("/v1/exercises"' in source
    assert '@api.post("/v1/exercises/{exercise_id}/check"' in source
    assert '@api.get("/v1/learners", dependencies=[Depends(require_write_token)]' in source
    assert "password_hash" not in source
    assert '@api.get("/v1/learners/{user_id}/progress", dependencies=[Depends(require_write_token)]' in source
