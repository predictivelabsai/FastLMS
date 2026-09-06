"""Versioned FastLearn integration API.

Published curriculum and answer-safe exercises are public.  Learner data,
assignments, progress, attempts, and conversations require the deployment's
FastSME bearer token.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

import db
from app_version import APP_VERSION
from chess_engine import grade as grade_chess
from .api_core import ErrorEnvelope, Resource, require_write_token


RESOURCES = (
    Resource("courses", "courses", "Courses", "Published course catalogue and metadata."),
    Resource("modules", "modules", "Modules", "Ordered sections within published courses."),
    Resource("lessons", "lessons", "Lessons", "Localized lesson content and learning metadata."),
    Resource("exercises", "interactive_exercises", "Exercises", "Answer-safe guided exercises, including chess positions."),
)

PUBLIC_FIELDS = {
    "courses": ("id", "title", "slug", "description", "category", "difficulty", "thumbnail_url", "is_published", "is_default", "created_at"),
    "modules": ("id", "course_id", "title", "description", "order_idx", "created_at"),
    "lessons": ("id", "module_id", "title", "content_md", "content_type", "video_url", "duration_min", "xp_reward", "order_idx", "lesson_kind", "difficulty_level", "created_at"),
}

api = FastAPI(
    title="FastLearn API",
    version=APP_VERSION,
    description=(
        "Build learning integrations with FastLearn courses, assignments, progress, "
        "chat sessions, and guided exercises. Published curriculum reads are public. "
        "Learner data and all state-changing operations require `Authorization: Bearer <token>`."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[
        {"url": "https://fastlearn.fun/api", "description": "FastLearn production"},
        {"url": "https://lms.fastsme.com/api", "description": "FastLMS reference"},
    ],
    contact={"name": "FastSME", "url": "https://fastsme.com"},
    license_info={"name": "MIT"},
)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS", "POST"],
    allow_headers=["Accept", "Content-Type", "Authorization"],
)


@api.exception_handler(HTTPException)
async def api_http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {
        "code": "http_error", "message": str(exc.detail), "details": {},
    }
    return JSONResponse(status_code=exc.status_code, content={"error": detail}, headers=exc.headers)


class EnrolmentCreate(BaseModel):
    user_id: int
    course_id: int


class AssignmentCreate(BaseModel):
    user_id: int
    course_id: int
    assigned_by: int


class ExerciseCheck(BaseModel):
    answer: dict[str, Any]


class ExerciseAttemptCreate(ExerciseCheck):
    user_id: int
    lesson_id: int
    exercise_id: int
    chat_session_id: str | None = None
    duration_seconds: int = Field(default=0, ge=0, le=5400)


class ChatSessionCreate(BaseModel):
    user_id: int
    title: str = Field(default="New Chat", max_length=100)
    context: dict[str, Any] = Field(default_factory=dict)


def _not_found(resource: str, item_id: int | str):
    raise HTTPException(404, detail={
        "code": "not_found", "message": f"{resource} record not found.", "details": {"id": item_id},
    })


def _published_clause(table: str) -> tuple[str, str]:
    if table == "courses":
        return "", "c.is_published=true"
    if table == "modules":
        return f"JOIN {db.S}.courses c ON c.id=r.course_id", "c.is_published=true"
    return (
        f"JOIN {db.S}.modules m ON m.id=r.module_id JOIN {db.S}.courses c ON c.id=m.course_id",
        "c.is_published=true",
    )


def _list_public(table: str, *, limit: int, offset: int, lang: str) -> dict:
    fields = PUBLIC_FIELDS[table]
    alias = "c" if table == "courses" else "r"
    joins, where = _published_clause(table)
    selected = ", ".join(f"{alias}.{field}" for field in fields)
    order = "c.id" if table == "courses" else "r.id"
    with db.connect() as connection:
        total = connection.execute(sa.text(
            f"SELECT count(*) FROM {db.S}.{table} {alias} {joins} WHERE {where}"
        )).scalar_one()
        rows = connection.execute(sa.text(
            f"SELECT {selected} FROM {db.S}.{table} {alias} {joins} WHERE {where} "
            f"ORDER BY {order} LIMIT :limit OFFSET :offset"
        ), {"limit": limit, "offset": offset}).mappings().all()
        data = db._localized(rows, table, lang, connection)
    return {"data": data, "meta": {"total": total, "limit": limit, "offset": offset}}


def _get_public(table: str, item_id: int, lang: str) -> dict:
    fields = PUBLIC_FIELDS[table]
    alias = "c" if table == "courses" else "r"
    joins, where = _published_clause(table)
    selected = ", ".join(f"{alias}.{field}" for field in fields)
    with db.connect() as connection:
        row = connection.execute(sa.text(
            f"SELECT {selected} FROM {db.S}.{table} {alias} {joins} "
            f"WHERE {where} AND {alias}.id=:id"
        ), {"id": item_id}).mappings().first()
        if not row:
            _not_found(table.title(), item_id)
        return db._localized([row], table, lang, connection)[0]


@api.get("/", tags=["System"])
def index():
    return {
        "name": "FastLearn API", "version": APP_VERSION,
        "documentation": "https://fastlearn.fun/developers",
        "swagger": "https://fastlearn.fun/api/docs",
        "openapi": "https://fastlearn.fun/api/openapi.json",
    }


@api.get("/v1/health", tags=["System"])
def health():
    import os
    return {"status": "ok", "product": "FastLearn", "version": APP_VERSION, "writes_enabled": bool(os.getenv("FASTSME_API_TOKEN"))}


def register_public_routes(slug: str, table: str, tag: str):
    def list_records(
        limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
        lang: str = Query("en", pattern="^(en|et|lt|es)$"),
    ):
        return _list_public(table, limit=limit, offset=offset, lang=lang)

    def get_record(item_id: int, lang: str = Query("en", pattern="^(en|et|lt|es)$")):
        return _get_public(table, item_id, lang)

    api.get(f"/v1/{slug}", tags=[tag], operation_id=f"list_{slug}")(list_records)
    api.get(f"/v1/{slug}/{{item_id}}", tags=[tag], operation_id=f"get_{slug}")(get_record)


for resource in RESOURCES[:3]:
    register_public_routes(resource.slug, resource.table, resource.title)


@api.get("/v1/exercises", tags=["Exercises"])
def list_exercises(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    lang: str = Query("en", pattern="^(en|et|lt|es)$"),
):
    with db.connect() as connection:
        ids = connection.execute(sa.text(f"""
            SELECT DISTINCT e.id FROM {db.S}.interactive_exercises e
            JOIN {db.S}.lesson_exercises le ON le.exercise_id=e.id
            JOIN {db.S}.lessons l ON l.id=le.lesson_id
            JOIN {db.S}.modules m ON m.id=l.module_id
            JOIN {db.S}.courses c ON c.id=m.course_id
            WHERE c.is_published=true ORDER BY e.id LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).scalars().all()
        total = connection.execute(sa.text(f"""
            SELECT count(DISTINCT e.id) FROM {db.S}.interactive_exercises e
            JOIN {db.S}.lesson_exercises le ON le.exercise_id=e.id
            JOIN {db.S}.lessons l ON l.id=le.lesson_id
            JOIN {db.S}.modules m ON m.id=l.module_id
            JOIN {db.S}.courses c ON c.id=m.course_id WHERE c.is_published=true
        """)).scalar_one()
        rows = [db.get_interactive_exercise(connection, exercise_id, lang) for exercise_id in ids]
    return {"data": [row for row in rows if row], "meta": {"total": total, "limit": limit, "offset": offset}}


@api.get("/v1/courses/{course_id}/curriculum", tags=["Courses"])
def course_curriculum(course_id: int, lang: str = Query("en", pattern="^(en|et|lt|es)$")):
    course = _get_public("courses", course_id, lang)
    with db.connect() as connection:
        modules = db.get_modules(connection, course_id, lang)
        for module in modules:
            module["lessons"] = db.get_lessons(connection, module["id"], lang)
            for lesson in module["lessons"]:
                lesson["exercise_count"] = len(db.get_lesson_exercises(connection, lesson["id"], lang))
    return {"course": course, "modules": modules}


@api.get("/v1/lessons/{lesson_id}/exercises", tags=["Exercises"])
def lesson_exercises(lesson_id: int, lang: str = Query("en", pattern="^(en|et|lt|es)$")):
    _get_public("lessons", lesson_id, lang)
    with db.connect() as connection:
        rows = db.get_lesson_exercises(connection, lesson_id, lang)
    return {"data": rows, "meta": {"total": len(rows)}}


@api.get("/v1/exercises/{exercise_id}", tags=["Exercises"])
def get_exercise(exercise_id: int, lang: str = Query("en", pattern="^(en|et|lt|es)$")):
    with db.connect() as connection:
        exercise = db.get_interactive_exercise(connection, exercise_id, lang)
    if not exercise:
        _not_found("Exercise", exercise_id)
    return exercise


@api.post("/v1/exercises/{exercise_id}/check", tags=["Exercises"], responses={404: {"model": ErrorEnvelope}})
def check_exercise(exercise_id: int, payload: ExerciseCheck):
    with db.connect() as connection:
        exercise = db.get_interactive_exercise(connection, exercise_id, include_answer=True)
    if not exercise:
        _not_found("Exercise", exercise_id)
    if exercise["engine"] != "chess":
        raise HTTPException(422, detail={"code": "unsupported_engine", "message": "Unsupported exercise engine.", "details": {}})
    return grade_chess(exercise["exercise_type"], exercise.get("fen"), exercise["answer_payload"], payload.answer)


@api.get("/v1/learners", dependencies=[Depends(require_write_token)], tags=["Learners"])
def list_learners(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with db.connect() as connection:
        total = connection.execute(sa.text(f"SELECT count(*) FROM {db.S}.users WHERE role='student'")).scalar_one()
        rows = connection.execute(sa.text(f"""
            SELECT id, email, display_name, role, avatar_url, xp, level, streak_days, created_at
            FROM {db.S}.users WHERE role='student' ORDER BY id LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).mappings().all()
    return {"data": [dict(row) for row in rows], "meta": {"total": total, "limit": limit, "offset": offset}}


@api.get("/v1/learners/{user_id}/progress", dependencies=[Depends(require_write_token)], tags=["Progress"])
def learner_progress(user_id: int):
    with db.connect() as connection:
        learner = db.get_user(connection, user_id)
        if not learner or learner.get("role") != "student":
            _not_found("Learner", user_id)
        courses = connection.execute(sa.text(f"""
            SELECT DISTINCT c.* FROM {db.S}.courses c
            LEFT JOIN {db.S}.enrolments e ON e.course_id=c.id AND e.user_id=:user
            LEFT JOIN {db.S}.course_assignments a ON a.course_id=c.id AND a.user_id=:user
            WHERE e.id IS NOT NULL OR a.id IS NOT NULL ORDER BY c.id
        """), {"user": user_id}).mappings().all()
        data = []
        for course in courses:
            progress = db.get_user_course_progress(connection, user_id, course["id"])
            progress["course"] = {"id": course["id"], "slug": course["slug"], "title": course["title"]}
            progress["exercise_mastery"] = db.exercise_mastery(connection, user_id=user_id, course_id=course["id"])
            data.append(progress)
    return {"learner": {"id": learner["id"], "email": learner["email"], "display_name": learner["display_name"]}, "courses": data}


@api.get("/v1/assignments", dependencies=[Depends(require_write_token)], tags=["Assignments"])
def list_assignments(user_id: int | None = None):
    where = "WHERE a.user_id=:user" if user_id else ""
    with db.connect() as connection:
        rows = connection.execute(sa.text(f"""
            SELECT a.id, a.user_id, a.course_id, a.assigned_by, a.assigned_at,
                   u.display_name AS learner_name, u.email AS learner_email, c.title AS course_title
            FROM {db.S}.course_assignments a JOIN {db.S}.users u ON u.id=a.user_id
            JOIN {db.S}.courses c ON c.id=a.course_id {where} ORDER BY a.assigned_at DESC
        """), {"user": user_id} if user_id else {}).mappings().all()
    return {"data": [dict(row) for row in rows], "meta": {"total": len(rows)}}


@api.post("/v1/assignments", status_code=201, dependencies=[Depends(require_write_token)], tags=["Assignments"])
def create_assignment(payload: AssignmentCreate):
    with db.begin() as connection:
        learner = db.get_user(connection, payload.user_id)
        course = connection.execute(sa.text(f"SELECT id FROM {db.S}.courses WHERE id=:id"), {"id": payload.course_id}).scalar()
        teacher = db.get_user(connection, payload.assigned_by)
        if not learner or learner.get("role") != "student" or not course or not teacher or teacher.get("role") not in {"teacher", "admin"}:
            raise HTTPException(422, detail={"code": "invalid_assignment", "message": "A student, course, and teacher/admin are required.", "details": {}})
        db.assign_course(connection, user_id=payload.user_id, course_id=payload.course_id, assigned_by=payload.assigned_by)
        db.audit(connection, actor_id=payload.assigned_by, action="course.assigned.api", target_type="course", target_id=payload.course_id, details={"user_id": payload.user_id})
    return payload.model_dump()


@api.post("/v1/enrolments", status_code=201, dependencies=[Depends(require_write_token)], tags=["Enrolments"])
def create_enrolment(payload: EnrolmentCreate):
    with db.begin() as connection:
        row = connection.execute(sa.text(f"""
            INSERT INTO {db.S}.enrolments (user_id, course_id) VALUES (:user_id, :course_id)
            ON CONFLICT (user_id, course_id) DO UPDATE SET user_id=EXCLUDED.user_id RETURNING *
        """), payload.model_dump()).mappings().one()
    return dict(row)


@api.post("/v1/exercise-attempts", status_code=201, dependencies=[Depends(require_write_token)], tags=["Progress"])
def create_exercise_attempt(payload: ExerciseAttemptCreate):
    with db.begin() as connection:
        exercise = db.get_interactive_exercise(connection, payload.exercise_id, include_answer=True)
        if not exercise:
            _not_found("Exercise", payload.exercise_id)
        verdict = grade_chess(exercise["exercise_type"], exercise.get("fen"), exercise["answer_payload"], payload.answer)
        row = db.record_exercise_attempt(
            connection, user_id=payload.user_id, exercise_id=payload.exercise_id,
            lesson_id=payload.lesson_id, chat_session_id=payload.chat_session_id,
            answer=payload.answer, verdict=verdict, duration_seconds=payload.duration_seconds,
        )
    return {"attempt_id": row["id"], **verdict}


@api.get("/v1/chat/sessions", dependencies=[Depends(require_write_token)], tags=["Chat"])
def list_chat_sessions(user_id: int, limit: int = Query(20, ge=1, le=100)):
    with db.connect() as connection:
        rows = db.list_chat_sessions(connection, user_id, limit=limit)
    return {"data": rows, "meta": {"total": len(rows), "limit": limit}}


@api.post("/v1/chat/sessions", status_code=201, dependencies=[Depends(require_write_token)], tags=["Chat"])
def create_chat_session(payload: ChatSessionCreate):
    with db.begin() as connection:
        if not db.get_user(connection, payload.user_id):
            _not_found("User", payload.user_id)
        return db.create_chat_session(connection, payload.user_id, title=payload.title, context=payload.context)


@api.get("/v1/chat/sessions/{session_id}/messages", dependencies=[Depends(require_write_token)], tags=["Chat"])
def chat_messages(session_id: str, user_id: int, limit: int = Query(100, ge=1, le=500)):
    with db.connect() as connection:
        if not db.get_chat_session(connection, user_id, session_id):
            _not_found("Chat session", session_id)
        rows = db.get_chat_history(connection, user_id, limit=limit, session_id=session_id)
    return {"data": rows, "meta": {"total": len(rows), "limit": limit}}
