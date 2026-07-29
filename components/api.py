"""FastLMS public reads and token-gated enrolment writes."""

import sqlalchemy as sa
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db

from .api_core import Resource, require_write_token

RESOURCES = (
    Resource("courses", "courses", "Courses", "Published learning courses and catalogue metadata."),
    Resource("lessons", "lessons", "Lessons", "Course lessons, content types, duration, and XP."),
    Resource("learners", "users", "Learners", "Learner profiles and progress levels."),
    Resource("enrolments", "enrolments", "Enrolments", "Course enrolments connecting learners and courses."),
)

api = FastAPI(
    title="FastLMS API",
    version="1.0.0",
    description=(
        "Open integration access to FastLMS courses, lessons, learners, and "
        "enrolments. Reads are public. Selected writes require a bearer token "
        "and remain disabled until FASTSME_API_TOKEN is configured."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[{"url": "https://lms.fastsme.com/api", "description": "Production"}],
    license_info={"name": "MIT"},
)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "HEAD", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)


class EnrolmentCreate(BaseModel):
    user_id: int
    course_id: int


def _list(table: str, *, limit: int, offset: int):
    with db.connect() as connection:
        total = connection.execute(
            sa.text(f"SELECT count(*) FROM {db.S}.{table}")
        ).scalar_one()
        rows = connection.execute(
            sa.text(
                f"SELECT * FROM {db.S}.{table} ORDER BY id LIMIT :limit OFFSET :offset"
            ),
            {"limit": limit, "offset": offset},
        ).mappings().all()
    return {
        "data": [dict(row) for row in rows],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


def _get(table: str, item_id: int):
    with db.connect() as connection:
        row = connection.execute(
            sa.text(f"SELECT * FROM {db.S}.{table} WHERE id=:id"),
            {"id": item_id},
        ).mappings().first()
    if not row:
        raise HTTPException(
            404,
            detail={
                "code": "not_found",
                "message": f"{table.title()} record not found.",
                "details": {"id": item_id},
            },
        )
    return dict(row)


@api.get("/", tags=["System"])
def index():
    return {
        "name": "FastLMS API",
        "version": "1.0.0",
        "documentation": "https://lms.fastsme.com/developers",
        "swagger": "https://lms.fastsme.com/api/docs",
        "openapi": "https://lms.fastsme.com/api/openapi.json",
    }


@api.get("/v1/health", tags=["System"])
def health():
    return {"status": "ok", "product": "FastLMS", "version": "1.0.0"}


def register_read_routes(slug: str, table: str, tag: str):
    def list_records(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ):
        return _list(table, limit=limit, offset=offset)

    def get_record(item_id: int):
        return _get(table, item_id)

    api.get(
        f"/v1/{slug}", tags=[tag], operation_id=f"list_{slug}"
    )(list_records)
    api.get(
        f"/v1/{slug}/{{item_id}}", tags=[tag], operation_id=f"get_{slug}"
    )(get_record)


for resource in RESOURCES:
    register_read_routes(resource.slug, resource.table, resource.title)


@api.post(
    "/v1/enrolments",
    status_code=201,
    dependencies=[Depends(require_write_token)],
    tags=["Enrolments"],
)
def create_enrolment(payload: EnrolmentCreate):
    """Enrol an existing learner in an existing course."""

    with db.begin() as connection:
        item_id = connection.execute(
            sa.text(
                f"INSERT INTO {db.S}.enrolments (user_id, course_id) "
                "VALUES (:user_id, :course_id) "
                "ON CONFLICT (user_id, course_id) DO UPDATE SET user_id=excluded.user_id "
                "RETURNING id"
            ),
            payload.model_dump(),
        ).scalar_one()
    return _get("enrolments", item_id)
