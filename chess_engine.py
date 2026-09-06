"""Server-side grading for FastLearn chess exercises.

Answers are evaluated against private database payloads.  Route drills keep the
same learner piece moving throughout; they intentionally do not alternate turns
like a complete game.
"""

from __future__ import annotations

from collections import deque
from typing import Any

import chess


_DIRECTIONS = {
    chess.ROOK: ((1, 0), (-1, 0), (0, 1), (0, -1)),
    chess.BISHOP: ((1, 1), (1, -1), (-1, 1), (-1, -1)),
    chess.QUEEN: (
        (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (1, -1), (-1, 1), (-1, -1),
    ),
}


def _route_destinations(square: int, piece_type: int, board: chess.Board, *, capture: bool) -> set[int]:
    result: set[int] = set()
    file_index, rank_index = chess.square_file(square), chess.square_rank(square)
    colour = board.color_at(square)
    for file_step, rank_step in _DIRECTIONS.get(piece_type, ()):
        file_pos, rank_pos = file_index + file_step, rank_index + rank_step
        while 0 <= file_pos < 8 and 0 <= rank_pos < 8:
            target = chess.square(file_pos, rank_pos)
            piece = board.piece_at(target)
            if piece:
                if capture and piece.color != colour:
                    result.add(target)
                break
            result.add(target)
            file_pos += file_step
            rank_pos += rank_step
    return result


def _moving_square(board: chess.Board) -> int:
    squares = [square for square, piece in board.piece_map().items() if piece.color == board.turn]
    if len(squares) != 1:
        raise ValueError("A route exercise must contain exactly one learner piece")
    return squares[0]


def _grade_path(fen: str, expected: dict, answer: dict) -> tuple[bool, bool, bool]:
    moves = answer.get("moves") or []
    if not isinstance(moves, list) or not moves:
        return False, False, False
    board = chess.Board(fen)
    current = _moving_square(board)
    piece = board.piece_at(current)
    goal = chess.parse_square(expected["goal"])
    for notation in moves:
        try:
            move = chess.Move.from_uci(str(notation))
        except ValueError:
            return False, False, False
        if move.from_square != current or move.to_square not in _route_destinations(current, piece.piece_type, board, capture=False):
            return False, False, False
        board.remove_piece_at(current)
        board.set_piece_at(move.to_square, piece)
        current = move.to_square
    completed = current == goal
    optimal = completed and len(moves) == int(expected.get("optimal_len", len(moves)))
    return completed and optimal, completed, optimal


def _grade_capture_sequence(fen: str, answer: dict) -> tuple[bool, bool, bool]:
    moves = answer.get("moves") or []
    if not isinstance(moves, list) or not moves:
        return False, False, False
    board = chess.Board(fen)
    current = _moving_square(board)
    piece = board.piece_at(current)
    opponents = {square for square, other in board.piece_map().items() if other.color != piece.color}
    for notation in moves:
        try:
            move = chess.Move.from_uci(str(notation))
        except ValueError:
            return False, False, False
        destinations = _route_destinations(current, piece.piece_type, board, capture=True)
        if move.from_square != current or move.to_square not in destinations or move.to_square not in opponents:
            return False, False, False
        opponents.remove(move.to_square)
        board.remove_piece_at(current)
        board.set_piece_at(move.to_square, piece)
        current = move.to_square
    completed = not opponents
    return completed, completed, completed


def grade(exercise_type: str, fen: str | None, expected: dict[str, Any], answer: dict[str, Any]) -> dict[str, bool | None]:
    """Return correctness signals without ever returning the expected answer."""
    if exercise_type == "multiple_choice":
        correct = answer.get("answer") == expected.get("answer")
        return {"correct": correct, "completed": correct, "optimal": None}
    if exercise_type == "select_squares":
        submitted = answer.get("squares") or []
        correct = isinstance(submitted, list) and set(submitted) == set(expected.get("targets") or [])
        return {"correct": correct, "completed": correct, "optimal": None}
    if exercise_type == "place_pieces":
        submitted = answer.get("placements") or []
        wanted = {(item["square"], item["piece"]) for item in expected.get("placements") or []}
        received = {(item.get("square"), item.get("piece")) for item in submitted if isinstance(item, dict)}
        correct = wanted == received
        return {"correct": correct, "completed": correct, "optimal": None}
    if exercise_type == "path":
        correct, completed, optimal = _grade_path(str(fen), expected, answer)
        return {"correct": correct, "completed": completed, "optimal": optimal}
    if exercise_type == "move_sequence":
        correct, completed, optimal = _grade_capture_sequence(str(fen), answer)
        return {"correct": correct, "completed": completed, "optimal": optimal}
    raise ValueError(f"Unsupported exercise type: {exercise_type}")


def shortest_route_length(fen: str, goal: str) -> int:
    """Return the shortest empty-board route for a slider exercise."""
    board = chess.Board(fen)
    start = _moving_square(board)
    piece = board.piece_at(start)
    target = chess.parse_square(goal)
    board.remove_piece_at(start)
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        square, distance = queue.popleft()
        if square == target:
            return distance
        probe = board.copy()
        probe.set_piece_at(square, piece)
        for destination in _route_destinations(square, piece.piece_type, probe, capture=False):
            if destination not in seen:
                seen.add(destination)
                queue.append((destination, distance + 1))
    return 0

