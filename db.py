"""FastLMS database layer — PostgreSQL via SQLAlchemy.

Schema lives in ``fastlms`` on the database pointed to by ``DB_URL``.
Tables cover courses, lessons, quizzes, progress, interactivity, and chat.
"""

from __future__ import annotations

import atexit
import json
import os
import re
import threading
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.engine import Engine

load_dotenv()

SCHEMA = os.getenv("DB_SCHEMA", "fastlms")
if not re.fullmatch(r"[a-z_][a-z0-9_]*", SCHEMA):
    raise RuntimeError("DB_SCHEMA must be a lowercase PostgreSQL identifier")
_engines: dict[str, Engine] = {}
_engine_lock = threading.Lock()


def get_engine() -> Engine:
    url = os.environ.get("DB_URL")
    if not url:
        raise RuntimeError("DB_URL not set in .env")
    engine = _engines.get(url)
    if engine is not None:
        return engine
    with _engine_lock:
        engine = _engines.get(url)
        if engine is None:
            engine = sa.create_engine(
                url,
                pool_pre_ping=True,
                pool_size=int(os.getenv("DB_POOL_SIZE", "3")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "2")),
                pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "10")),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
                connect_args={
                    "application_name": os.getenv(
                        "DB_APPLICATION_NAME", "fastlms"
                    )
                },
            )
            _engines[url] = engine
    return engine


def dispose_database_pools() -> None:
    """Dispose every process-wide engine during shutdown or tests."""
    with _engine_lock:
        engines = list(_engines.values())
        _engines.clear()
    for engine in engines:
        engine.dispose()


atexit.register(dispose_database_pools)


@contextmanager
def connect():
    with get_engine().connect() as conn:
        yield conn


@contextmanager
def begin():
    with get_engine().begin() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

SCHEMA_SQL = f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA};

-- Users
CREATE TABLE IF NOT EXISTS {SCHEMA}.users (
    id              SERIAL PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'student',  -- student | instructor | admin
    avatar_url      TEXT,
    xp              INTEGER NOT NULL DEFAULT 0,
    level           TEXT NOT NULL DEFAULT 'Novice',
    streak_days     INTEGER NOT NULL DEFAULT 0,
    streak_last     DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Courses
CREATE TABLE IF NOT EXISTS {SCHEMA}.courses (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    description     TEXT,
    category        TEXT,
    difficulty      TEXT NOT NULL DEFAULT 'beginner',  -- beginner | intermediate | advanced
    thumbnail_url   TEXT,
    instructor_id   INTEGER REFERENCES {SCHEMA}.users(id),
    is_published    BOOLEAN NOT NULL DEFAULT false,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Modules (sections within a course)
CREATE TABLE IF NOT EXISTS {SCHEMA}.modules (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    order_idx       INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Lessons
CREATE TABLE IF NOT EXISTS {SCHEMA}.lessons (
    id              SERIAL PRIMARY KEY,
    module_id       INTEGER NOT NULL REFERENCES {SCHEMA}.modules(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    content_md      TEXT,
    content_type    TEXT NOT NULL DEFAULT 'text',  -- text | video | interactive
    video_url       TEXT,
    duration_min    INTEGER,
    xp_reward       INTEGER NOT NULL DEFAULT 25,
    order_idx       INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Quizzes (one per lesson, optional)
CREATE TABLE IF NOT EXISTS {SCHEMA}.quizzes (
    id              SERIAL PRIMARY KEY,
    lesson_id       INTEGER NOT NULL REFERENCES {SCHEMA}.lessons(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    pass_threshold  INTEGER NOT NULL DEFAULT 70,  -- percent
    xp_reward       INTEGER NOT NULL DEFAULT 50,
    time_limit_min  INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Quiz questions
CREATE TABLE IF NOT EXISTS {SCHEMA}.quiz_questions (
    id              SERIAL PRIMARY KEY,
    quiz_id         INTEGER NOT NULL REFERENCES {SCHEMA}.quizzes(id) ON DELETE CASCADE,
    question_text   TEXT NOT NULL,
    question_type   TEXT NOT NULL DEFAULT 'multiple_choice',
    options         JSONB NOT NULL DEFAULT '[]',
    correct_answer  TEXT NOT NULL,
    explanation     TEXT,
    order_idx       INTEGER NOT NULL DEFAULT 0
);

-- Lesson progress
CREATE TABLE IF NOT EXISTS {SCHEMA}.lesson_progress (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    lesson_id       INTEGER NOT NULL REFERENCES {SCHEMA}.lessons(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'not_started',  -- not_started | in_progress | completed
    completed_at    TIMESTAMPTZ,
    UNIQUE(user_id, lesson_id)
);

-- Quiz attempts
CREATE TABLE IF NOT EXISTS {SCHEMA}.quiz_attempts (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    quiz_id         INTEGER NOT NULL REFERENCES {SCHEMA}.quizzes(id) ON DELETE CASCADE,
    score           INTEGER NOT NULL,
    passed          BOOLEAN NOT NULL,
    answers         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);

-- Badges
CREATE TABLE IF NOT EXISTS {SCHEMA}.badges (
    id              SERIAL PRIMARY KEY,
    slug            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    icon            TEXT NOT NULL DEFAULT '🏅',
    criteria_type   TEXT NOT NULL,  -- lessons_completed | streak | quiz_score | xp_total | course_completed
    criteria_value  INTEGER NOT NULL DEFAULT 1
);

-- User badges
CREATE TABLE IF NOT EXISTS {SCHEMA}.user_badges (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    badge_id        INTEGER NOT NULL REFERENCES {SCHEMA}.badges(id) ON DELETE CASCADE,
    earned_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, badge_id)
);

-- Course enrolments
CREATE TABLE IF NOT EXISTS {SCHEMA}.enrolments (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    enrolled_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, course_id)
);

-- Explicit teacher-to-course access. Course owners and administrators also have access.
CREATE TABLE IF NOT EXISTS {SCHEMA}.teacher_course_access (
    teacher_id      INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    granted_by      INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE SET NULL,
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (teacher_id, course_id)
);

-- Assignments are distinct from self-enrolment so learners can see an Assigned tag.
CREATE TABLE IF NOT EXISTS {SCHEMA}.course_assignments (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    assigned_by     INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE SET NULL,
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, course_id)
);

-- Invitations never expire, but are single-use and revocable.
CREATE TABLE IF NOT EXISTS {SCHEMA}.invitations (
    id              SERIAL PRIMARY KEY,
    email           TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'student',
    token_hash      TEXT UNIQUE NOT NULL,
    invited_by      INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    consumed_at     TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-course learning behaviour. Linear is deliberately the default.
CREATE TABLE IF NOT EXISTS {SCHEMA}.course_learning_settings (
    course_id       INTEGER PRIMARY KEY REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    strategy        TEXT NOT NULL DEFAULT 'linear',
    low_threshold   INTEGER NOT NULL DEFAULT 60,
    high_threshold  INTEGER NOT NULL DEFAULT 85,
    high_streak     INTEGER NOT NULL DEFAULT 2,
    allow_reorder   BOOLEAN NOT NULL DEFAULT true,
    allow_remedial  BOOLEAN NOT NULL DEFAULT true,
    updated_by      INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE SET NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.learner_course_state (
    user_id             INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id           INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    difficulty_level    INTEGER NOT NULL DEFAULT 2,
    consecutive_high    INTEGER NOT NULL DEFAULT 0,
    consecutive_low     INTEGER NOT NULL DEFAULT 0,
    last_score          INTEGER,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, course_id)
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.adaptive_recommendations (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id           INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    source_quiz_id      INTEGER REFERENCES {SCHEMA}.quizzes(id) ON DELETE SET NULL,
    target_lesson_id    INTEGER REFERENCES {SCHEMA}.lessons(id) ON DELETE SET NULL,
    recommendation_type TEXT NOT NULL,
    title               TEXT NOT NULL,
    reason              TEXT,
    status              TEXT NOT NULL DEFAULT 'pending',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Aggregated active time. context_key makes general tutor sessions safely upsertable.
CREATE TABLE IF NOT EXISTS {SCHEMA}.learning_time (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id       INTEGER REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    resource_type   TEXT NOT NULL,
    resource_id     INTEGER,
    context_key     TEXT NOT NULL,
    activity_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    seconds_active  INTEGER NOT NULL DEFAULT 0,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, context_key, activity_date)
);

-- Teacher-reviewed AI/remedial content in all supported languages.
CREATE TABLE IF NOT EXISTS {SCHEMA}.content_drafts (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    module_id       INTEGER REFERENCES {SCHEMA}.modules(id) ON DELETE CASCADE,
    source_lesson_id INTEGER REFERENCES {SCHEMA}.lessons(id) ON DELETE SET NULL,
    draft_type      TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL DEFAULT 2,
    content         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'pending',
    created_by      INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE SET NULL,
    approved_by     INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.content_translations (
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER NOT NULL,
    language        TEXT NOT NULL,
    title           TEXT,
    description     TEXT,
    content_md      TEXT,
    question_text   TEXT,
    options         JSONB,
    correct_answer  TEXT,
    explanation     TEXT,
    PRIMARY KEY (entity_type, entity_id, language)
);

-- Course-neutral interactive exercise library. The browser receives only
-- public_payload while answer_payload remains server-side for grading.
CREATE TABLE IF NOT EXISTS {SCHEMA}.interactive_exercises (
    id                  BIGSERIAL PRIMARY KEY,
    source_key          TEXT UNIQUE NOT NULL,
    engine              TEXT NOT NULL,
    exercise_type       TEXT NOT NULL,
    fen                 TEXT,
    prompt              TEXT NOT NULL,
    concepts            JSONB NOT NULL DEFAULT '[]'::jsonb,
    difficulty_band     INTEGER NOT NULL DEFAULT 1 CHECK (difficulty_band BETWEEN 1 AND 5),
    cognitive_layer     TEXT NOT NULL DEFAULT 'skill' CHECK (cognitive_layer IN ('skill','knowledge','wisdom')),
    public_payload      JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    answer_payload      JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.exercise_translations (
    exercise_id         BIGINT NOT NULL REFERENCES {SCHEMA}.interactive_exercises(id) ON DELETE CASCADE,
    language            TEXT NOT NULL,
    prompt              TEXT NOT NULL,
    public_payload      JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    PRIMARY KEY (exercise_id, language)
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.lesson_exercises (
    lesson_id           INTEGER NOT NULL REFERENCES {SCHEMA}.lessons(id) ON DELETE CASCADE,
    exercise_id         BIGINT NOT NULL REFERENCES {SCHEMA}.interactive_exercises(id) ON DELETE CASCADE,
    order_idx           INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (lesson_id, exercise_id)
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.exercise_attempts (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    course_id           INTEGER NOT NULL REFERENCES {SCHEMA}.courses(id) ON DELETE CASCADE,
    lesson_id           INTEGER NOT NULL REFERENCES {SCHEMA}.lessons(id) ON DELETE CASCADE,
    exercise_id         BIGINT NOT NULL REFERENCES {SCHEMA}.interactive_exercises(id) ON DELETE CASCADE,
    chat_session_id     VARCHAR(36),
    answer              JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    correct             BOOLEAN NOT NULL,
    completed           BOOLEAN,
    optimal             BOOLEAN,
    duration_seconds    INTEGER NOT NULL DEFAULT 0 CHECK (duration_seconds BETWEEN 0 AND 5400),
    difficulty_band     INTEGER NOT NULL,
    attempted_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Native-to-target language practice preferences and graduated recall state.
CREATE TABLE IF NOT EXISTS {SCHEMA}.language_profiles (
    user_id          INTEGER PRIMARY KEY REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    native_language  TEXT NOT NULL DEFAULT 'en',
    target_language  TEXT NOT NULL DEFAULT 'es',
    daily_goal       INTEGER NOT NULL DEFAULT 10,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (native_language IN ('en','es','fr','de','it','pt','zh','ar','ja','hi','et','lt')),
    CHECK (target_language IN ('en','es','fr','de','it','pt','zh','ar','ja','hi')),
    CHECK (native_language <> target_language),
    CHECK (daily_goal BETWEEN 5 AND 50)
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.language_reviews (
    user_id          INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    target_language  TEXT NOT NULL,
    concept_id       TEXT NOT NULL,
    interval_step    INTEGER NOT NULL DEFAULT 0,
    repetitions      INTEGER NOT NULL DEFAULT 0,
    correct_streak   INTEGER NOT NULL DEFAULT 0,
    last_rating      TEXT,
    last_reviewed_at TIMESTAMPTZ,
    next_due_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (target_language IN ('en','es','fr','de','it','pt','zh','ar','ja','hi')),
    CHECK (last_rating IS NULL OR last_rating IN ('again','hard','good')),
    PRIMARY KEY (user_id, target_language, concept_id)
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.language_attempts (
    id               BIGSERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    native_language  TEXT NOT NULL,
    target_language  TEXT NOT NULL,
    concept_id       TEXT NOT NULL,
    rating           TEXT NOT NULL,
    interval_seconds INTEGER NOT NULL,
    attempted_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (native_language IN ('en','es','fr','de','it','pt','zh','ar','ja','hi','et','lt')),
    CHECK (target_language IN ('en','es','fr','de','it','pt','zh','ar','ja','hi')),
    CHECK (rating IN ('again','hard','good'))
);

CREATE TABLE IF NOT EXISTS {SCHEMA}.audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor_id        INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE SET NULL,
    action          TEXT NOT NULL,
    target_type     TEXT NOT NULL,
    target_id       TEXT,
    details         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE {SCHEMA}.lessons ADD COLUMN IF NOT EXISTS lesson_kind TEXT NOT NULL DEFAULT 'core';
ALTER TABLE {SCHEMA}.lessons ADD COLUMN IF NOT EXISTS difficulty_level INTEGER NOT NULL DEFAULT 2;
ALTER TABLE {SCHEMA}.lessons ADD COLUMN IF NOT EXISTS prerequisite_lesson_id INTEGER REFERENCES {SCHEMA}.lessons(id) ON DELETE SET NULL;
ALTER TABLE {SCHEMA}.quiz_questions ADD COLUMN IF NOT EXISTS difficulty_level INTEGER NOT NULL DEFAULT 2;
ALTER TABLE {SCHEMA}.courses ADD COLUMN IF NOT EXISTS is_default BOOLEAN NOT NULL DEFAULT false;

-- The checked-in demonstration catalogue is administrator-owned reference
-- material. Teachers may assign or clone it, but never edit it in place.
UPDATE {SCHEMA}.courses SET is_default = true WHERE slug IN (
    'python-fundamentals', 'ml-sklearn', 'fasthtml-web-apps',
    'mathematics-foundations', 'physics-essentials', 'biology-life-sciences',
    'chemistry-fundamentals', 'english-language-literature',
    'geography-physical-human', 'creative-writing', 'art-history',
    'music-history', 'art-principles', 'music-principles',
    'chess-foundations'
);
UPDATE {SCHEMA}.courses SET instructor_id = (
    SELECT id FROM {SCHEMA}.users WHERE lower(email) = 'kaljuvee@gmail.com' LIMIT 1
) WHERE is_default = true AND EXISTS (
    SELECT 1 FROM {SCHEMA}.users WHERE lower(email) = 'kaljuvee@gmail.com'
);

-- Discussions (per-lesson threaded comments)
CREATE TABLE IF NOT EXISTS {SCHEMA}.discussions (
    id              SERIAL PRIMARY KEY,
    lesson_id       INTEGER NOT NULL REFERENCES {SCHEMA}.lessons(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    parent_id       INTEGER REFERENCES {SCHEMA}.discussions(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Persistent conversations. Context stores the current course, lesson, quiz,
-- and the choices shown to the learner so chat can safely resume after reload.
CREATE TABLE IF NOT EXISTS {SCHEMA}.chat_sessions (
    id              VARCHAR(36) PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL DEFAULT 'New Chat',
    context         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Chat messages within a persistent conversation.
CREATE TABLE IF NOT EXISTS {SCHEMA}.chat_messages (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
    lesson_id       INTEGER REFERENCES {SCHEMA}.lessons(id) ON DELETE SET NULL,
    session_id      VARCHAR(36),
    role            TEXT NOT NULL,  -- user | assistant | system
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE {SCHEMA}.chat_messages ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_lessons_module ON {SCHEMA}.lessons(module_id, order_idx);
CREATE INDEX IF NOT EXISTS idx_modules_course ON {SCHEMA}.modules(course_id, order_idx);
CREATE INDEX IF NOT EXISTS idx_progress_user ON {SCHEMA}.lesson_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user_lesson ON {SCHEMA}.chat_messages(user_id, lesson_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated ON {SCHEMA}.chat_sessions(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON {SCHEMA}.chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_enrolments_user ON {SCHEMA}.enrolments(user_id);
CREATE INDEX IF NOT EXISTS idx_discussions_lesson ON {SCHEMA}.discussions(lesson_id);
CREATE INDEX IF NOT EXISTS idx_assignments_user ON {SCHEMA}.course_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_time_course ON {SCHEMA}.learning_time(course_id, user_id);
CREATE INDEX IF NOT EXISTS idx_adaptive_user_course ON {SCHEMA}.adaptive_recommendations(user_id, course_id, status);
CREATE INDEX IF NOT EXISTS idx_drafts_course_status ON {SCHEMA}.content_drafts(course_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_created ON {SCHEMA}.audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_language_reviews_due ON {SCHEMA}.language_reviews(user_id, target_language, next_due_at);
CREATE INDEX IF NOT EXISTS idx_language_attempts_user ON {SCHEMA}.language_attempts(user_id, attempted_at DESC);
CREATE INDEX IF NOT EXISTS idx_lesson_exercises_order ON {SCHEMA}.lesson_exercises(lesson_id, order_idx);
CREATE INDEX IF NOT EXISTS idx_exercise_attempts_user ON {SCHEMA}.exercise_attempts(user_id, attempted_at DESC);
CREATE INDEX IF NOT EXISTS idx_exercise_attempts_lesson ON {SCHEMA}.exercise_attempts(lesson_id, user_id);

-- Normalise the legacy role name and keep one deliberately scoped administrator.
UPDATE {SCHEMA}.users SET role = 'teacher' WHERE role = 'instructor';
UPDATE {SCHEMA}.users SET role = 'teacher' WHERE role = 'admin' AND lower(email) <> 'kaljuvee@gmail.com';
UPDATE {SCHEMA}.users SET role = 'admin' WHERE lower(email) = 'kaljuvee@gmail.com';
"""


def bootstrap_schema():
    with begin() as conn:
        for stmt in SCHEMA_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(sa.text(stmt))
        # school-administration layer (students/programs/gradebook/attendance/fees)
        import school
        school.bootstrap(conn)
        # Protected reference courses are installed with the schema so existing
        # deployments receive them without a destructive catalogue reset.
        from arts_catalog import seed_art_courses
        from chess_course import seed_chess_course
        seed_art_courses(conn, SCHEMA)
        seed_chess_course(conn, SCHEMA)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

S = SCHEMA  # shorthand for queries


def get_user(conn, user_id: int) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.users WHERE id = :id"), {"id": user_id}).mappings().first()
    return dict(row) if row else None


def get_user_by_email(conn, email: str) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.users WHERE email = :e"), {"e": email}).mappings().first()
    return dict(row) if row else None


def _localized(rows, entity: str, lang: str, conn=None):
    from components.i18n import localize_record
    localized = [localize_record(dict(row), entity, lang) for row in rows]
    if lang == "en" or conn is None or not localized:
        return localized
    ids = [row["id"] for row in localized]
    translations = conn.execute(
        sa.text(f"""
            SELECT * FROM {S}.content_translations
            WHERE entity_type = :entity AND language = :lang AND entity_id = ANY(:ids)
        """),
        {"entity": entity, "lang": lang, "ids": ids},
    ).mappings().all()
    overlays = {row["entity_id"]: dict(row) for row in translations}
    for row in localized:
        overlay = overlays.get(row["id"], {})
        for field in ("title", "description", "content_md", "question_text", "options", "correct_answer", "explanation"):
            if overlay.get(field) is not None:
                row[field] = overlay[field]
    return localized


def get_courses(conn, published_only=True, lang="en") -> list[dict]:
    where = f"WHERE is_published = true" if published_only else ""
    rows = conn.execute(sa.text(f"SELECT * FROM {S}.courses {where} ORDER BY created_at DESC")).mappings().all()
    return _localized(rows, "courses", lang, conn)


def get_course(conn, slug: str, lang="en") -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.courses WHERE slug = :s"), {"s": slug}).mappings().first()
    return _localized([row], "courses", lang, conn)[0] if row else None


def get_modules(conn, course_id: int, lang="en") -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {S}.modules WHERE course_id = :c ORDER BY order_idx"),
        {"c": course_id},
    ).mappings().all()
    return _localized(rows, "modules", lang, conn)


def get_lessons(conn, module_id: int, lang="en") -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {S}.lessons WHERE module_id = :m ORDER BY order_idx"),
        {"m": module_id},
    ).mappings().all()
    return _localized(rows, "lessons", lang, conn)


def get_lesson(conn, lesson_id: int, lang="en") -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.lessons WHERE id = :id"), {"id": lesson_id}).mappings().first()
    return _localized([row], "lessons", lang, conn)[0] if row else None


def _json_object(value) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def get_interactive_exercise(conn, exercise_id: int, lang: str = "en", *, include_answer: bool = False) -> dict | None:
    """Return one localized exercise; private answers are opt-in for graders."""
    row = conn.execute(sa.text(f"""
        SELECT e.*, et.prompt AS translated_prompt,
               et.public_payload AS translated_public_payload
        FROM {S}.interactive_exercises e
        LEFT JOIN {S}.exercise_translations et
          ON et.exercise_id=e.id AND et.language=:language
        WHERE e.id=:exercise
    """), {"exercise": exercise_id, "language": lang}).mappings().first()
    if not row:
        return None
    item = dict(row)
    public = _json_object(item.pop("public_payload", {}))
    translated = _json_object(item.pop("translated_public_payload", {}))
    public.update(translated)
    item["prompt"] = item.pop("translated_prompt") or item["prompt"]
    if not include_answer:
        item.pop("answer_payload", None)
    else:
        item["answer_payload"] = _json_object(item.get("answer_payload"))
    item.update(public)
    return item


def get_lesson_exercises(conn, lesson_id: int, lang: str = "en", *, user_id: int | None = None) -> list[dict]:
    rows = conn.execute(sa.text(f"""
        SELECT le.exercise_id, le.order_idx,
               CASE WHEN CAST(:user_id AS INTEGER) IS NULL THEN false ELSE EXISTS (
                   SELECT 1 FROM {S}.exercise_attempts ea
                   WHERE ea.user_id=:user_id AND ea.exercise_id=le.exercise_id AND ea.correct=true
               ) END AS solved
        FROM {S}.lesson_exercises le
        WHERE le.lesson_id=:lesson ORDER BY le.order_idx, le.exercise_id
    """), {"lesson": lesson_id, "user_id": user_id}).mappings().all()
    result = []
    for row in rows:
        exercise = get_interactive_exercise(conn, row["exercise_id"], lang)
        if exercise:
            exercise["order_idx"] = row["order_idx"]
            exercise["solved"] = bool(row["solved"])
            result.append(exercise)
    return result


def get_next_lesson_exercise(conn, lesson_id: int, user_id: int, lang: str = "en") -> dict | None:
    exercises = get_lesson_exercises(conn, lesson_id, lang, user_id=user_id)
    return next((exercise for exercise in exercises if not exercise["solved"]), None)


def exercise_context(conn, exercise_id: int) -> dict | None:
    row = conn.execute(sa.text(f"""
        SELECT e.id AS exercise_id, le.lesson_id, m.course_id
        FROM {S}.interactive_exercises e
        JOIN {S}.lesson_exercises le ON le.exercise_id=e.id
        JOIN {S}.lessons l ON l.id=le.lesson_id
        JOIN {S}.modules m ON m.id=l.module_id
        WHERE e.id=:exercise ORDER BY le.lesson_id LIMIT 1
    """), {"exercise": exercise_id}).mappings().first()
    return dict(row) if row else None


def update_exercise_adaptive_state(conn, *, user_id: int, course_id: int, correct: bool) -> dict:
    """Adjust practice difficulty while leaving lesson order linear."""
    settings = get_course_learning_settings(conn, course_id)
    state = conn.execute(sa.text(f"""
        SELECT * FROM {S}.learner_course_state WHERE user_id=:user AND course_id=:course
    """), {"user": user_id, "course": course_id}).mappings().first()
    decision = adaptive_transition(
        state["difficulty_level"] if state else 2,
        state["consecutive_high"] if state else 0,
        100 if correct else 0,
        low_threshold=settings["low_threshold"], high_threshold=settings["high_threshold"],
        high_streak=settings["high_streak"],
    )
    conn.execute(sa.text(f"""
        INSERT INTO {S}.learner_course_state
            (user_id, course_id, difficulty_level, consecutive_high, consecutive_low, last_score)
        VALUES (:user, :course, :level, :high, :low, :score)
        ON CONFLICT (user_id, course_id) DO UPDATE SET
            difficulty_level=EXCLUDED.difficulty_level,
            consecutive_high=EXCLUDED.consecutive_high,
            consecutive_low=CASE
                WHEN EXCLUDED.last_score < :low_threshold THEN {S}.learner_course_state.consecutive_low + 1
                ELSE 0 END,
            last_score=EXCLUDED.last_score, updated_at=now()
    """), {
        "user": user_id, "course": course_id, "level": decision["difficulty_level"],
        "high": decision["consecutive_high"], "low": decision["consecutive_low"],
        "score": 100 if correct else 0, "low_threshold": settings["low_threshold"],
    })
    return decision


def record_exercise_attempt(
    conn, *, user_id: int, exercise_id: int, lesson_id: int, chat_session_id: str | None,
    answer: dict, verdict: dict, duration_seconds: int = 0,
) -> dict:
    exercise = get_interactive_exercise(conn, exercise_id, include_answer=True)
    context = exercise_context(conn, exercise_id)
    if not exercise or not context or int(context["lesson_id"]) != int(lesson_id):
        raise ValueError("Exercise does not belong to this lesson")
    row = conn.execute(sa.text(f"""
        INSERT INTO {S}.exercise_attempts
            (user_id, course_id, lesson_id, exercise_id, chat_session_id, answer,
             correct, completed, optimal, duration_seconds, difficulty_band)
        VALUES (:user, :course, :lesson, :exercise, :chat, CAST(:answer AS jsonb),
                :correct, :completed, :optimal, :duration, :band)
        RETURNING *
    """), {
        "user": user_id, "course": context["course_id"], "lesson": lesson_id,
        "exercise": exercise_id, "chat": chat_session_id, "answer": json.dumps(answer),
        "correct": bool(verdict.get("correct")), "completed": verdict.get("completed"),
        "optimal": verdict.get("optimal"), "duration": max(0, min(int(duration_seconds or 0), 5400)),
        "band": exercise["difficulty_band"],
    }).mappings().one()
    update_exercise_adaptive_state(conn, user_id=user_id, course_id=context["course_id"], correct=bool(verdict.get("correct")))
    return dict(row)


def exercise_mastery(conn, *, user_id: int, course_id: int) -> list[dict]:
    """Summarise concept/SKW coverage without conflating it with difficulty."""
    rows = conn.execute(sa.text(f"""
        WITH available AS (
            SELECT DISTINCT e.id, concept.value #>> '{{}}' AS concept, e.cognitive_layer
            FROM {S}.interactive_exercises e
            JOIN {S}.lesson_exercises le ON le.exercise_id=e.id
            JOIN {S}.lessons l ON l.id=le.lesson_id
            JOIN {S}.modules m ON m.id=l.module_id
            CROSS JOIN LATERAL jsonb_array_elements(e.concepts) concept(value)
            WHERE m.course_id=:course
        ), attempts AS (
            SELECT exercise_id, count(*) AS attempts,
                   count(*) FILTER (WHERE correct) AS correct_attempts,
                   bool_or(correct) AS solved
            FROM {S}.exercise_attempts WHERE user_id=:user AND course_id=:course
            GROUP BY exercise_id
        )
        SELECT a.concept, a.cognitive_layer,
               count(*) AS available,
               count(*) FILTER (WHERE COALESCE(t.solved, false)) AS solved,
               COALESCE(sum(t.attempts), 0) AS attempts,
               COALESCE(sum(t.correct_attempts), 0) AS correct_attempts
        FROM available a LEFT JOIN attempts t ON t.exercise_id=a.id
        GROUP BY a.concept, a.cognitive_layer ORDER BY a.concept, a.cognitive_layer
    """), {"user": user_id, "course": course_id}).mappings().all()
    result = []
    for row in rows:
        item = dict(row)
        required = max(1, round(int(item["available"]) * 0.6))
        rate = int(item["correct_attempts"]) / int(item["attempts"]) if item["attempts"] else 0
        if int(item["solved"]) >= required:
            status = "mastered"
        elif int(item["attempts"]) >= 4 and rate < 0.34:
            status = "stuck"
        elif item["attempts"]:
            status = "in_progress"
        else:
            status = "not_started"
        item["status"] = status
        result.append(item)
    return result


def get_quiz_for_lesson(conn, lesson_id: int, lang="en") -> dict | None:
    row = conn.execute(
        sa.text(f"SELECT * FROM {S}.quizzes WHERE lesson_id = :l"), {"l": lesson_id}
    ).mappings().first()
    return _localized([row], "quizzes", lang, conn)[0] if row else None


def get_quiz_questions(conn, quiz_id: int, lang="en", learner_level: int | None = None) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {S}.quiz_questions WHERE quiz_id = :q ORDER BY order_idx"),
        {"q": quiz_id},
    ).mappings().all()
    questions = _localized(rows, "quiz_questions", lang, conn)
    if learner_level is None or not questions:
        return questions
    level = max(1, min(3, int(learner_level)))
    nearest_distance = min(abs((row.get("difficulty_level") or 2) - level) for row in questions)
    return [row for row in questions if abs((row.get("difficulty_level") or 2) - level) == nearest_distance]


def get_lesson_progress(conn, user_id: int, lesson_id: int) -> dict | None:
    row = conn.execute(
        sa.text(f"SELECT * FROM {S}.lesson_progress WHERE user_id = :u AND lesson_id = :l"),
        {"u": user_id, "l": lesson_id},
    ).mappings().first()
    return dict(row) if row else None


def get_user_course_progress(conn, user_id: int, course_id: int) -> dict:
    """Return {total, completed, percent} for a user's progress in a course."""
    row = conn.execute(
        sa.text(f"""
            SELECT count(l.id) AS total,
                   count(lp.id) FILTER (WHERE lp.status = 'completed') AS completed
            FROM {S}.lessons l
            JOIN {S}.modules m ON m.id = l.module_id
            LEFT JOIN {S}.lesson_progress lp ON lp.lesson_id = l.id AND lp.user_id = :u
            WHERE m.course_id = :c AND COALESCE(l.lesson_kind, 'core') = 'core'
        """),
        {"u": user_id, "c": course_id},
    ).mappings().first()
    total = row["total"] or 0
    completed = row["completed"] or 0
    return {"total": total, "completed": completed, "percent": round(completed / total * 100) if total else 0}


def mark_lesson_complete(conn, user_id: int, lesson_id: int) -> int:
    """Mark lesson complete, award XP, update streak. Returns XP earned."""
    lesson = get_lesson(conn, lesson_id)
    xp = lesson["xp_reward"] if lesson else 25

    conn.execute(
        sa.text(f"""
            INSERT INTO {S}.lesson_progress (user_id, lesson_id, status, completed_at)
            VALUES (:u, :l, 'completed', now())
            ON CONFLICT (user_id, lesson_id) DO UPDATE SET status = 'completed', completed_at = now()
        """),
        {"u": user_id, "l": lesson_id},
    )

    conn.execute(sa.text(f"UPDATE {S}.users SET xp = xp + :xp WHERE id = :u"), {"xp": xp, "u": user_id})
    _update_streak(conn, user_id)
    _update_level(conn, user_id)
    return xp


def _update_streak(conn, user_id: int):
    today = date.today()
    user = get_user(conn, user_id)
    if not user:
        return
    last = user["streak_last"]
    if last == today:
        return
    if last and (today - last).days == 1:
        conn.execute(
            sa.text(f"UPDATE {S}.users SET streak_days = streak_days + 1, streak_last = :d WHERE id = :u"),
            {"d": today, "u": user_id},
        )
    else:
        conn.execute(
            sa.text(f"UPDATE {S}.users SET streak_days = 1, streak_last = :d WHERE id = :u"),
            {"d": today, "u": user_id},
        )


LEVELS = [
    (0, "Novice"),
    (500, "Apprentice"),
    (2000, "Scholar"),
    (5000, "Expert"),
    (10000, "Master"),
    (25000, "Grandmaster"),
]


def _update_level(conn, user_id: int):
    user = get_user(conn, user_id)
    if not user:
        return
    xp = user["xp"]
    level = "Novice"
    for threshold, name in LEVELS:
        if xp >= threshold:
            level = name
    if level != user["level"]:
        conn.execute(sa.text(f"UPDATE {S}.users SET level = :l WHERE id = :u"), {"l": level, "u": user_id})


def get_leaderboard(conn, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT id, display_name, xp, level, streak_days FROM {S}.users ORDER BY xp DESC LIMIT :l"),
        {"l": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_user_badges(conn, user_id: int, lang="en") -> list[dict]:
    rows = conn.execute(
        sa.text(f"""
            SELECT b.*, ub.earned_at FROM {S}.user_badges ub
            JOIN {S}.badges b ON b.id = ub.badge_id
            WHERE ub.user_id = :u ORDER BY ub.earned_at DESC
        """),
        {"u": user_id},
    ).mappings().all()
    return _localized(rows, "badges", lang)


def check_and_award_badges(conn, user_id: int) -> list[dict]:
    """Check badge criteria and award any newly earned badges. Returns newly awarded list."""
    user = get_user(conn, user_id)
    if not user:
        return []

    existing = {r["badge_id"] for r in conn.execute(
        sa.text(f"SELECT badge_id FROM {S}.user_badges WHERE user_id = :u"), {"u": user_id}
    ).mappings().all()}

    all_badges = conn.execute(sa.text(f"SELECT * FROM {S}.badges")).mappings().all()
    awarded = []

    for badge in all_badges:
        if badge["id"] in existing:
            continue

        earned = False
        ct, cv = badge["criteria_type"], badge["criteria_value"]

        if ct == "xp_total":
            earned = user["xp"] >= cv
        elif ct == "streak":
            earned = user["streak_days"] >= cv
        elif ct == "lessons_completed":
            cnt = conn.execute(
                sa.text(f"SELECT count(*) FROM {S}.lesson_progress WHERE user_id = :u AND status = 'completed'"),
                {"u": user_id},
            ).scalar()
            earned = cnt >= cv
        elif ct == "quiz_score":
            cnt = conn.execute(
                sa.text(f"SELECT count(*) FROM {S}.quiz_attempts WHERE user_id = :u AND score >= :v"),
                {"u": user_id, "v": cv},
            ).scalar()
            earned = cnt > 0
        elif ct == "course_completed":
            # check if any course is 100% complete
            enrolments = conn.execute(
                sa.text(f"SELECT course_id FROM {S}.enrolments WHERE user_id = :u"), {"u": user_id}
            ).mappings().all()
            for e in enrolments:
                prog = get_user_course_progress(conn, user_id, e["course_id"])
                if prog["percent"] == 100:
                    earned = True
                    break

        if earned:
            conn.execute(
                sa.text(f"INSERT INTO {S}.user_badges (user_id, badge_id) VALUES (:u, :b) ON CONFLICT DO NOTHING"),
                {"u": user_id, "b": badge["id"]},
            )
            awarded.append(dict(badge))

    return awarded


def get_discussions(conn, lesson_id: int) -> list[dict]:
    rows = conn.execute(
        sa.text(f"""
            SELECT d.*, u.display_name, u.avatar_url FROM {S}.discussions d
            JOIN {S}.users u ON u.id = d.user_id
            WHERE d.lesson_id = :l AND d.parent_id IS NULL
            ORDER BY d.created_at DESC
        """),
        {"l": lesson_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def create_chat_session(
    conn, user_id: int, *, title: str = "New Chat", context: dict | None = None,
    session_id: str | None = None,
) -> dict:
    session_id = session_id or str(uuid.uuid4())
    row = conn.execute(sa.text(f"""
        INSERT INTO {S}.chat_sessions (id, user_id, title, context)
        VALUES (:id, :user, :title, CAST(:context AS jsonb))
        RETURNING *
    """), {
        "id": session_id, "user": user_id, "title": (title or "New Chat")[:100],
        "context": json.dumps(context or {}),
    }).mappings().one()
    return dict(row)


def get_chat_session(conn, user_id: int, session_id: str) -> dict | None:
    row = conn.execute(sa.text(f"""
        SELECT * FROM {S}.chat_sessions WHERE id = :id AND user_id = :user
    """), {"id": session_id, "user": user_id}).mappings().first()
    return dict(row) if row else None


def list_chat_sessions(conn, user_id: int, limit: int = 20) -> list[dict]:
    rows = conn.execute(sa.text(f"""
        SELECT * FROM {S}.chat_sessions WHERE user_id = :user
        ORDER BY updated_at DESC LIMIT :limit
    """), {"user": user_id, "limit": max(1, min(int(limit), 100))}).mappings().all()
    return [dict(row) for row in rows]


def update_chat_session(
    conn, user_id: int, session_id: str, *, title: str | None = None,
    context: dict | None = None,
) -> dict | None:
    row = conn.execute(sa.text(f"""
        UPDATE {S}.chat_sessions SET
            title = COALESCE(:title, title),
            context = COALESCE(CAST(:context AS jsonb), context),
            updated_at = now()
        WHERE id = :id AND user_id = :user
        RETURNING *
    """), {
        "id": session_id, "user": user_id,
        "title": title[:100] if title else None,
        "context": json.dumps(context) if context is not None else None,
    }).mappings().first()
    return dict(row) if row else None


def add_chat_message(
    conn, *, user_id: int, session_id: str, role: str, content: str,
    lesson_id: int | None = None,
) -> None:
    if role not in {"user", "assistant", "system"}:
        raise ValueError("unsupported chat role")
    conn.execute(sa.text(f"""
        INSERT INTO {S}.chat_messages (user_id, lesson_id, session_id, role, content)
        VALUES (:user, :lesson, :session, :role, :content)
    """), {
        "user": user_id, "lesson": lesson_id, "session": session_id,
        "role": role, "content": content,
    })
    conn.execute(sa.text(f"""
        UPDATE {S}.chat_sessions SET updated_at = now()
        WHERE id = :session AND user_id = :user
    """), {"session": session_id, "user": user_id})


def get_chat_history(
    conn, user_id: int, lesson_id: int | None = None, limit: int = 50,
    *, session_id: str | None = None,
) -> list[dict]:
    if session_id:
        rows = conn.execute(
            sa.text(f"""
                SELECT * FROM {S}.chat_messages
                WHERE user_id = :u AND session_id = :session
                ORDER BY created_at ASC LIMIT :lim
            """),
            {"u": user_id, "session": session_id, "lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]
    if lesson_id:
        rows = conn.execute(
            sa.text(f"""
                SELECT * FROM {S}.chat_messages
                WHERE user_id = :u AND lesson_id = :l
                ORDER BY created_at ASC LIMIT :lim
            """),
            {"u": user_id, "l": lesson_id, "lim": limit},
        ).mappings().all()
    else:
        rows = conn.execute(
            sa.text(f"""
                SELECT * FROM {S}.chat_messages
                WHERE user_id = :u AND lesson_id IS NULL
                ORDER BY created_at ASC LIMIT :lim
            """),
            {"u": user_id, "lim": limit},
        ).mappings().all()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Roles, assignments, activity and adaptive learning
# ---------------------------------------------------------------------------

ADMIN_EMAIL = "kaljuvee@gmail.com"
VALID_ROLES = {"admin", "teacher", "student"}


def role_for_email(email: str, requested: str = "student") -> str:
    """Return the only role this account may receive during account creation."""
    if (email or "").strip().lower() == ADMIN_EMAIL:
        return "admin"
    return requested if requested in {"teacher", "student"} else "student"


def audit(conn, *, actor_id: int | None, action: str, target_type: str,
          target_id: int | str | None = None, details: dict | None = None) -> None:
    conn.execute(sa.text(f"""
        INSERT INTO {S}.audit_log (actor_id, action, target_type, target_id, details)
        VALUES (:actor, :action, :target_type, :target_id, :details)
    """), {"actor": actor_id, "action": action, "target_type": target_type,
             "target_id": str(target_id) if target_id is not None else None,
             "details": json.dumps(details or {})})


def course_is_editable_by(user: dict, course: dict | None) -> bool:
    if not course:
        return False
    if user.get("role") == "admin":
        return True
    return user.get("role") in {"teacher", "instructor"} and (
        course.get("instructor_id") == user.get("id") and not course.get("is_default", False)
    )


def can_manage_course(conn, user: dict, course_id: int) -> bool:
    row = conn.execute(sa.text(f"""
        SELECT id, instructor_id, is_default FROM {S}.courses WHERE id = :course
    """), {"course": course_id}).mappings().first()
    return course_is_editable_by(user, dict(row) if row else None)


def get_managed_courses(conn, user: dict, lang: str = "en") -> list[dict]:
    if user.get("role") == "admin":
        return get_courses(conn, published_only=False, lang=lang)
    rows = conn.execute(sa.text(f"""
        SELECT c.* FROM {S}.courses c
        WHERE c.instructor_id = :teacher AND COALESCE(c.is_default, false) = false
        ORDER BY c.created_at DESC
    """), {"teacher": user["id"]}).mappings().all()
    return _localized(rows, "courses", lang, conn)


def get_assignable_courses(conn, user: dict, lang: str = "en") -> list[dict]:
    """Return the catalogue a staff member may assign without granting edit rights."""
    if user.get("role") == "admin":
        return get_courses(conn, published_only=False, lang=lang)
    rows = conn.execute(sa.text(f"""
        SELECT * FROM {S}.courses
        WHERE is_published = true OR instructor_id = :teacher
        ORDER BY is_default DESC, title
    """), {"teacher": user["id"]}).mappings().all()
    return _localized(rows, "courses", lang, conn)


def can_assign_course(conn, user: dict, course_id: int) -> bool:
    if user.get("role") == "admin":
        return bool(conn.execute(sa.text(f"SELECT 1 FROM {S}.courses WHERE id = :course"), {"course": course_id}).scalar())
    if user.get("role") not in {"teacher", "instructor"}:
        return False
    return bool(conn.execute(sa.text(f"""
        SELECT 1 FROM {S}.courses
        WHERE id = :course AND (is_published = true OR instructor_id = :teacher)
    """), {"course": course_id, "teacher": user["id"]}).scalar())


def can_clone_course(conn, user: dict, course_id: int) -> bool:
    """Only staff may fork a published, administrator-curated default."""
    if user.get("role") not in {"teacher", "instructor", "admin"}:
        return False
    return bool(conn.execute(sa.text(f"""
        SELECT 1 FROM {S}.courses
        WHERE id = :course AND is_default = true AND is_published = true
    """), {"course": course_id}).scalar())


def get_role_metrics(conn, user: dict) -> dict:
    """Return meaningful sidebar/dashboard metrics for staff roles."""
    if user.get("role") == "admin":
        row = conn.execute(sa.text(f"""
            SELECT
                (SELECT count(*) FROM {S}.users) AS people,
                (SELECT count(*) FROM {S}.courses WHERE is_published = true) AS courses,
                (SELECT count(*) FROM {S}.content_drafts WHERE status = 'pending') AS approvals
        """)).mappings().one()
    else:
        row = conn.execute(sa.text(f"""
            SELECT
                (SELECT count(DISTINCT u.id) FROM {S}.users u
                 WHERE u.role = 'student' AND (
                    EXISTS (SELECT 1 FROM {S}.course_assignments ca
                            WHERE ca.user_id = u.id AND ca.assigned_by = :teacher)
                    OR EXISTS (SELECT 1 FROM {S}.invitations i
                               WHERE i.invited_by = :teacher AND i.revoked_at IS NULL
                                 AND lower(i.email) = lower(u.email))
                 )) AS people,
                (SELECT count(DISTINCT c.id) FROM {S}.courses c
                 LEFT JOIN {S}.course_assignments ca
                    ON ca.course_id = c.id AND ca.assigned_by = :teacher
                 WHERE (c.instructor_id = :teacher AND c.is_published = true
                        AND COALESCE(c.is_default, false) = false)
                    OR ca.id IS NOT NULL) AS courses,
                (SELECT count(*) FROM {S}.content_drafts d
                 JOIN {S}.courses c ON c.id = d.course_id
                 WHERE c.instructor_id = :teacher AND d.status = 'pending'
                   AND COALESCE(c.is_default, false) = false) AS approvals
        """), {"teacher": user["id"]}).mappings().one()
    return {key: int(value or 0) for key, value in dict(row).items()}


def clone_course(conn, *, source_course_id: int, owner_id: int) -> dict:
    """Clone an assignable course and all authored content into an editable draft."""
    source = conn.execute(sa.text(f"""
        SELECT * FROM {S}.courses WHERE id = :course
    """), {"course": source_course_id}).mappings().first()
    if not source:
        raise ValueError("course not found")

    base_slug = f"{source['slug']}-copy"
    slug = base_slug
    suffix = 2
    while conn.execute(sa.text(f"SELECT 1 FROM {S}.courses WHERE slug = :slug"), {"slug": slug}).scalar():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    clone = conn.execute(sa.text(f"""
        INSERT INTO {S}.courses
            (title, slug, description, category, difficulty, thumbnail_url,
             instructor_id, is_published, is_default)
        VALUES (:title, :slug, :description, :category, :difficulty, :thumbnail,
                :owner, false, false)
        RETURNING *
    """), {
        "title": f"{source['title']} (Copy)", "slug": slug,
        "description": source.get("description"), "category": source.get("category"),
        "difficulty": source.get("difficulty") or "beginner",
        "thumbnail": source.get("thumbnail_url"), "owner": owner_id,
    }).mappings().one()

    def copy_translations(entity: str, old_id: int, new_id: int) -> None:
        conn.execute(sa.text(f"""
            INSERT INTO {S}.content_translations
                (entity_type, entity_id, language, title, description, content_md,
                 question_text, options, correct_answer, explanation)
            SELECT entity_type, :new_id, language, title, description, content_md,
                   question_text, options, correct_answer, explanation
            FROM {S}.content_translations
            WHERE entity_type = :entity AND entity_id = :old_id
            ON CONFLICT DO NOTHING
        """), {"entity": entity, "old_id": old_id, "new_id": new_id})

    copy_translations("courses", source_course_id, clone["id"])
    lesson_ids: dict[int, int] = {}
    for module in conn.execute(sa.text(f"""
        SELECT * FROM {S}.modules WHERE course_id = :course ORDER BY order_idx
    """), {"course": source_course_id}).mappings().all():
        new_module_id = conn.execute(sa.text(f"""
            INSERT INTO {S}.modules (course_id, title, description, order_idx)
            VALUES (:course, :title, :description, :order_idx) RETURNING id
        """), {
            "course": clone["id"], "title": module["title"],
            "description": module.get("description"), "order_idx": module["order_idx"],
        }).scalar_one()
        copy_translations("modules", module["id"], new_module_id)
        for lesson in conn.execute(sa.text(f"""
            SELECT * FROM {S}.lessons WHERE module_id = :module ORDER BY order_idx
        """), {"module": module["id"]}).mappings().all():
            new_lesson_id = conn.execute(sa.text(f"""
                INSERT INTO {S}.lessons
                    (module_id, title, content_md, content_type, video_url, duration_min,
                     xp_reward, order_idx, lesson_kind, difficulty_level)
                VALUES (:module, :title, :content, :content_type, :video, :duration,
                        :xp, :order_idx, :kind, :level) RETURNING id
            """), {
                "module": new_module_id, "title": lesson["title"],
                "content": lesson.get("content_md"), "content_type": lesson.get("content_type") or "text",
                "video": lesson.get("video_url"), "duration": lesson.get("duration_min"),
                "xp": lesson.get("xp_reward") or 25, "order_idx": lesson["order_idx"],
                "kind": lesson.get("lesson_kind") or "core",
                "level": lesson.get("difficulty_level") or 2,
            }).scalar_one()
            lesson_ids[lesson["id"]] = new_lesson_id
            copy_translations("lessons", lesson["id"], new_lesson_id)
            quiz = conn.execute(sa.text(f"""
                SELECT * FROM {S}.quizzes WHERE lesson_id = :lesson
            """), {"lesson": lesson["id"]}).mappings().first()
            if not quiz:
                continue
            new_quiz_id = conn.execute(sa.text(f"""
                INSERT INTO {S}.quizzes
                    (lesson_id, title, pass_threshold, xp_reward, time_limit_min)
                VALUES (:lesson, :title, :threshold, :xp, :time_limit) RETURNING id
            """), {
                "lesson": new_lesson_id, "title": quiz["title"],
                "threshold": quiz["pass_threshold"], "xp": quiz["xp_reward"],
                "time_limit": quiz.get("time_limit_min"),
            }).scalar_one()
            copy_translations("quizzes", quiz["id"], new_quiz_id)
            questions = conn.execute(sa.text(f"""
                SELECT * FROM {S}.quiz_questions WHERE quiz_id = :quiz ORDER BY order_idx
            """), {"quiz": quiz["id"]}).mappings().all()
            for question in questions:
                new_question_id = conn.execute(sa.text(f"""
                    INSERT INTO {S}.quiz_questions
                        (quiz_id, question_text, question_type, options, correct_answer,
                         explanation, order_idx, difficulty_level)
                    VALUES (:quiz, :question, :type, :options, :answer,
                            :explanation, :order_idx, :level) RETURNING id
                """), {
                    "quiz": new_quiz_id, "question": question["question_text"],
                    "type": question.get("question_type") or "multiple_choice",
                    "options": json.dumps(question.get("options") or []),
                    "answer": question["correct_answer"], "explanation": question.get("explanation"),
                    "order_idx": question["order_idx"], "level": question.get("difficulty_level") or 2,
                }).scalar_one()
                copy_translations("quiz_questions", question["id"], new_question_id)

    for old_id, new_id in lesson_ids.items():
        prerequisite = conn.execute(sa.text(f"""
            SELECT prerequisite_lesson_id FROM {S}.lessons WHERE id = :lesson
        """), {"lesson": old_id}).scalar()
        if prerequisite in lesson_ids:
            conn.execute(sa.text(f"""
                UPDATE {S}.lessons SET prerequisite_lesson_id = :prerequisite WHERE id = :lesson
            """), {"lesson": new_id, "prerequisite": lesson_ids[prerequisite]})
        # Reference exercises are immutable.  Clones share them until a future
        # teacher-authored exercise is created, avoiding answer-key duplication.
        conn.execute(sa.text(f"""
            INSERT INTO {S}.lesson_exercises (lesson_id, exercise_id, order_idx)
            SELECT :new_lesson, exercise_id, order_idx
            FROM {S}.lesson_exercises WHERE lesson_id=:old_lesson
            ON CONFLICT DO NOTHING
        """), {"new_lesson": new_id, "old_lesson": old_id})

    settings = conn.execute(sa.text(f"""
        SELECT * FROM {S}.course_learning_settings WHERE course_id = :course
    """), {"course": source_course_id}).mappings().first()
    if settings:
        conn.execute(sa.text(f"""
            INSERT INTO {S}.course_learning_settings
                (course_id, strategy, low_threshold, high_threshold, high_streak,
                 allow_reorder, allow_remedial, updated_by)
            VALUES (:course, :strategy, :low, :high, :streak, :reorder, :remedial, :owner)
        """), {
            "course": clone["id"], "strategy": settings["strategy"],
            "low": settings["low_threshold"], "high": settings["high_threshold"],
            "streak": settings["high_streak"], "reorder": settings["allow_reorder"],
            "remedial": settings["allow_remedial"], "owner": owner_id,
        })
    return dict(clone)


def get_assigned_course_ids(conn, user_id: int) -> set[int]:
    rows = conn.execute(
        sa.text(f"SELECT course_id FROM {S}.course_assignments WHERE user_id = :user"),
        {"user": user_id},
    ).all()
    return {row[0] for row in rows}


def assign_course(conn, *, user_id: int, course_id: int, assigned_by: int) -> None:
    conn.execute(sa.text(f"""
        INSERT INTO {S}.course_assignments (user_id, course_id, assigned_by)
        VALUES (:user, :course, :by)
        ON CONFLICT (user_id, course_id)
        DO UPDATE SET assigned_by = EXCLUDED.assigned_by, assigned_at = now()
    """), {"user": user_id, "course": course_id, "by": assigned_by})
    conn.execute(sa.text(f"""
        INSERT INTO {S}.enrolments (user_id, course_id)
        VALUES (:user, :course) ON CONFLICT DO NOTHING
    """), {"user": user_id, "course": course_id})


def unassign_course(conn, *, user_id: int, course_id: int) -> None:
    conn.execute(
        sa.text(f"DELETE FROM {S}.course_assignments WHERE user_id = :user AND course_id = :course"),
        {"user": user_id, "course": course_id},
    )


def resource_course_id(conn, resource_type: str, resource_id: int | None) -> int | None:
    if resource_type == "lesson" or resource_type == "tutor":
        if not resource_id:
            return None
        return conn.execute(sa.text(f"""
            SELECT m.course_id FROM {S}.lessons l
            JOIN {S}.modules m ON m.id = l.module_id WHERE l.id = :id
        """), {"id": resource_id}).scalar()
    if resource_type == "quiz" and resource_id:
        return conn.execute(sa.text(f"""
            SELECT m.course_id FROM {S}.quizzes q
            JOIN {S}.lessons l ON l.id = q.lesson_id
            JOIN {S}.modules m ON m.id = l.module_id WHERE q.id = :id
        """), {"id": resource_id}).scalar()
    if resource_type == "exercise" and resource_id:
        context = exercise_context(conn, resource_id)
        return context["course_id"] if context else None
    return None


def record_learning_time(
    conn, *, user_id: int, resource_type: str, resource_id: int | None, seconds: int
) -> int | None:
    """Accumulate a bounded active heartbeat and return its course id."""
    if resource_type not in {"lesson", "quiz", "tutor", "exercise"}:
        raise ValueError("unsupported resource type")
    seconds = max(1, min(int(seconds), 30))
    resource_id = int(resource_id) if resource_id else None
    course_id = resource_course_id(conn, resource_type, resource_id)
    context_key = f"{resource_type}:{resource_id or 0}"
    conn.execute(sa.text(f"""
        INSERT INTO {S}.learning_time
            (user_id, course_id, resource_type, resource_id, context_key, seconds_active)
        VALUES (:user, :course, :kind, :resource, :context, :seconds)
        ON CONFLICT (user_id, context_key, activity_date)
        DO UPDATE SET seconds_active = {S}.learning_time.seconds_active + EXCLUDED.seconds_active,
                      last_seen_at = now(), course_id = COALESCE(EXCLUDED.course_id, {S}.learning_time.course_id)
    """), {
        "user": user_id, "course": course_id, "kind": resource_type,
        "resource": resource_id, "context": context_key, "seconds": seconds,
    })
    return course_id


def get_language_profile(conn, user_id: int) -> dict | None:
    row = conn.execute(sa.text(f"""
        SELECT * FROM {S}.language_profiles WHERE user_id = :user
    """), {"user": user_id}).mappings().first()
    return dict(row) if row else None


def save_language_profile(
    conn, *, user_id: int, native_language: str, target_language: str, daily_goal: int = 10
) -> dict:
    from language_learning import validate_language_pair

    native, target = validate_language_pair(native_language, target_language)
    goal = max(5, min(50, int(daily_goal)))
    row = conn.execute(sa.text(f"""
        INSERT INTO {S}.language_profiles (user_id, native_language, target_language, daily_goal)
        VALUES (:user, :native, :target, :goal)
        ON CONFLICT (user_id) DO UPDATE SET
            native_language = EXCLUDED.native_language,
            target_language = EXCLUDED.target_language,
            daily_goal = EXCLUDED.daily_goal,
            updated_at = now()
        RETURNING *
    """), {"user": user_id, "native": native, "target": target, "goal": goal}).mappings().one()
    return dict(row)


def get_language_reviews(conn, *, user_id: int, target_language: str) -> list[dict]:
    rows = conn.execute(sa.text(f"""
        SELECT * FROM {S}.language_reviews
        WHERE user_id = :user AND target_language = :target
        ORDER BY next_due_at, concept_id
    """), {"user": user_id, "target": target_language}).mappings().all()
    return [dict(row) for row in rows]


def record_language_review(
    conn, *, user_id: int, native_language: str, target_language: str,
    concept_id: str, rating: str, now: datetime | None = None,
) -> dict:
    from language_learning import frequency_dictionary, schedule_review, validate_language_pair

    native, target = validate_language_pair(native_language, target_language)
    valid_concepts = {item["id"] for item in frequency_dictionary()["items"]}
    if concept_id not in valid_concepts:
        raise ValueError("unknown language concept")
    current = conn.execute(sa.text(f"""
        SELECT interval_step, repetitions, correct_streak FROM {S}.language_reviews
        WHERE user_id = :user AND target_language = :target AND concept_id = :concept
    """), {"user": user_id, "target": target, "concept": concept_id}).mappings().first()
    decision = schedule_review(current["interval_step"] if current else None, rating, now=now)
    repetitions = int(current["repetitions"] if current else 0) + 1
    correct_streak = int(current["correct_streak"] if current else 0) + 1 if decision["success"] else 0
    reviewed_at = now or datetime.now(timezone.utc)
    row = conn.execute(sa.text(f"""
        INSERT INTO {S}.language_reviews
            (user_id, target_language, concept_id, interval_step, repetitions,
             correct_streak, last_rating, last_reviewed_at, next_due_at)
        VALUES (:user, :target, :concept, :step, :repetitions, :streak,
                :rating, :reviewed, :due)
        ON CONFLICT (user_id, target_language, concept_id) DO UPDATE SET
            interval_step = EXCLUDED.interval_step,
            repetitions = EXCLUDED.repetitions,
            correct_streak = EXCLUDED.correct_streak,
            last_rating = EXCLUDED.last_rating,
            last_reviewed_at = EXCLUDED.last_reviewed_at,
            next_due_at = EXCLUDED.next_due_at
        RETURNING *
    """), {
        "user": user_id, "target": target, "concept": concept_id,
        "step": decision["interval_step"], "repetitions": repetitions,
        "streak": correct_streak, "rating": rating, "reviewed": reviewed_at,
        "due": decision["next_due_at"],
    }).mappings().one()
    conn.execute(sa.text(f"""
        INSERT INTO {S}.language_attempts
            (user_id, native_language, target_language, concept_id, rating, interval_seconds)
        VALUES (:user, :native, :target, :concept, :rating, :seconds)
    """), {
        "user": user_id, "native": native, "target": target,
        "concept": concept_id, "rating": rating,
        "seconds": decision["interval_seconds"],
    })
    result = dict(row)
    result["interval_seconds"] = decision["interval_seconds"]
    return result


def get_language_stats(conn, *, user_id: int, target_language: str) -> dict:
    row = conn.execute(sa.text(f"""
        SELECT count(*) AS expressions_seen,
               count(*) FILTER (WHERE interval_step >= 4) AS mastered,
               count(*) FILTER (WHERE next_due_at <= now()) AS due_now
        FROM {S}.language_reviews
        WHERE user_id = :user AND target_language = :target
    """), {"user": user_id, "target": target_language}).mappings().one()
    reviewed_today = conn.execute(sa.text(f"""
        SELECT count(*) FROM {S}.language_attempts
        WHERE user_id = :user AND target_language = :target
          AND attempted_at::date = CURRENT_DATE
    """), {"user": user_id, "target": target_language}).scalar() or 0
    return {**dict(row), "reviewed_today": int(reviewed_today)}


def get_course_learning_settings(conn, course_id: int) -> dict:
    row = conn.execute(
        sa.text(f"SELECT * FROM {S}.course_learning_settings WHERE course_id = :course"),
        {"course": course_id},
    ).mappings().first()
    if row:
        return dict(row)
    return {
        "course_id": course_id, "strategy": "linear", "low_threshold": 60,
        "high_threshold": 85, "high_streak": 2, "allow_reorder": True,
        "allow_remedial": True, "updated_by": None, "updated_at": None,
    }


def adaptive_transition(
    current_level: int, consecutive_high: int, score: int,
    *, low_threshold: int = 60, high_threshold: int = 85, high_streak: int = 2,
) -> dict:
    """Pure decision rule used by the database path and unit tests."""
    level = max(1, min(3, int(current_level or 2)))
    high = int(consecutive_high or 0)
    recommendation = "hold"
    if score < low_threshold:
        level = max(1, level - 1)
        high = 0
        recommendation = "remedial"
    elif score >= high_threshold:
        high += 1
        if high >= high_streak:
            level = min(3, level + 1)
            high = 0
            recommendation = "extension"
    else:
        high = 0
    return {
        "difficulty_level": level,
        "consecutive_high": high,
        "consecutive_low": 1 if score < low_threshold else 0,
        "recommendation": recommendation,
    }


def _draft_payload(kind: str, lesson_by_lang: dict[str, dict], score: int) -> dict:
    source = lesson_by_lang.get("en", {})
    titles = {
        "en": f"Guided practice: {source.get('title', 'Review')}" if kind == "remedial" else f"Extension: {source.get('title', 'Challenge')}",
        "et": f"Juhendatud harjutus: {lesson_by_lang.get('et', source).get('title', 'Kordamine')}" if kind == "remedial" else f"Süvaülesanne: {lesson_by_lang.get('et', source).get('title', 'Väljakutse')}",
        "lt": f"Praktika su pagalba: {lesson_by_lang.get('lt', source).get('title', 'Kartojimas')}" if kind == "remedial" else f"Išplėstinė užduotis: {lesson_by_lang.get('lt', source).get('title', 'Iššūkis')}",
        "es": f"Práctica guiada: {lesson_by_lang.get('es', source).get('title', 'Repaso')}" if kind == "remedial" else f"Ampliación: {lesson_by_lang.get('es', source).get('title', 'Desafío')}",
    }
    bodies = {
        "en": f"## Why this is recommended\n\nYour latest result was {score}%. Work through one smaller example, explain each step, then retry the assessment.",
        "et": f"## Miks see on soovitatud\n\nSinu viimane tulemus oli {score}%. Lahenda üks väiksem näide, selgita iga sammu ja proovi siis testi uuesti.",
        "lt": f"## Kodėl tai rekomenduojama\n\nNaujausias rezultatas – {score} %. Išnagrinėkite vieną paprastesnį pavyzdį, paaiškinkite kiekvieną žingsnį ir pakartokite testą.",
        "es": f"## Por qué se recomienda\n\nTu último resultado fue del {score} %. Trabaja con un ejemplo más sencillo, explica cada paso y vuelve a intentar la evaluación.",
    }
    if kind == "extension":
        bodies = {
            "en": f"## Stretch your understanding\n\nYou have shown consistent mastery ({score}%). Apply the idea to a less familiar case and justify your choices.",
            "et": f"## Arenda arusaamist\n\nOled näidanud püsivat meisterlikkust ({score}%). Rakenda ideed vähem tuttavas olukorras ja põhjenda oma valikuid.",
            "lt": f"## Pagilinkite supratimą\n\nParodėte nuoseklų meistriškumą ({score} %). Pritaikykite idėją mažiau pažįstamoje situacijoje ir pagrįskite pasirinkimus.",
            "es": f"## Amplía tu comprensión\n\nHas demostrado un dominio constante ({score} %). Aplica la idea a una situación menos familiar y justifica tus decisiones.",
        }
    return {lang: {"title": titles[lang], "content_md": bodies[lang]} for lang in ("en", "et", "lt", "es")}


def _question_draft_payload(lesson_by_lang: dict[str, dict], difficulty_level: int = 2) -> dict:
    titles = {lang: (lesson_by_lang.get(lang) or lesson_by_lang.get("en") or {}).get("title", "the lesson")
              for lang in ("en", "et", "lt", "es")}
    qualifier = {
        1: {"en": "With the key idea in view, ", "et": "Põhiideed silmas pidades, ", "lt": "Atsižvelgiant į pagrindinę mintį, "},
        2: {"en": "For this lesson, ", "et": "Selle tunni puhul, ", "lt": "Šioje pamokoje, "},
        3: {"en": "In a new and unfamiliar situation, ", "et": "Uues ja võõras olukorras, ", "lt": "Naujoje ir nepažįstamoje situacijoje, "},
    }[max(1, min(3, int(difficulty_level)))]
    qualifier["es"] = {
        1: "Con la idea principal a la vista, ",
        2: "Para esta lección, ",
        3: "En una situación nueva y desconocida, ",
    }[max(1, min(3, int(difficulty_level)))]
    return {
        "en": {
            "question_text": f"{qualifier['en']}which approach best demonstrates understanding of {titles['en']}?",
            "options": ["Apply the idea and explain each step", "Ignore the lesson context", "Choose without checking", "Skip the reasoning"],
            "correct_answer": "Apply the idea and explain each step",
            "explanation": "Applying the idea and making the reasoning visible demonstrates transferable understanding.",
        },
        "et": {
            "question_text": f"{qualifier['et']}milline lähenemine näitab kõige paremini teema „{titles['et']}“ mõistmist?",
            "options": ["Rakenda ideed ja selgita iga sammu", "Eira tunni konteksti", "Vali ilma kontrollimata", "Jäta põhjendus vahele"],
            "correct_answer": "Rakenda ideed ja selgita iga sammu",
            "explanation": "Idee rakendamine ja arutluskäigu nähtavaks tegemine näitab ülekantavat arusaamist.",
        },
        "lt": {
            "question_text": f"{qualifier['lt']}kuris būdas geriausiai parodo temos „{titles['lt']}“ supratimą?",
            "options": ["Pritaikyti idėją ir paaiškinti kiekvieną žingsnį", "Nepaisyti pamokos konteksto", "Pasirinkti nepatikrinus", "Praleisti pagrindimą"],
            "correct_answer": "Pritaikyti idėją ir paaiškinti kiekvieną žingsnį",
            "explanation": "Idėjos pritaikymas ir aiškus samprotavimas parodo perkeliamą supratimą.",
        },
        "es": {
            "question_text": f"{qualifier['es']}¿qué enfoque demuestra mejor la comprensión de «{titles['es']}»?",
            "options": ["Aplicar la idea y explicar cada paso", "Ignorar el contexto de la lección", "Elegir sin comprobar", "Omitir el razonamiento"],
            "correct_answer": "Aplicar la idea y explicar cada paso",
            "explanation": "Aplicar la idea y hacer visible el razonamiento demuestra una comprensión transferible.",
        },
    }


def update_adaptive_state(conn, *, user_id: int, quiz_id: int, score: int) -> dict | None:
    context = conn.execute(sa.text(f"""
        SELECT q.lesson_id, m.course_id FROM {S}.quizzes q
        JOIN {S}.lessons l ON l.id = q.lesson_id
        JOIN {S}.modules m ON m.id = l.module_id WHERE q.id = :quiz
    """), {"quiz": quiz_id}).mappings().first()
    if not context:
        return None
    settings = get_course_learning_settings(conn, context["course_id"])
    if settings["strategy"] != "adaptive":
        return None
    state = conn.execute(sa.text(f"""
        SELECT * FROM {S}.learner_course_state WHERE user_id = :user AND course_id = :course
    """), {"user": user_id, "course": context["course_id"]}).mappings().first()
    decision = adaptive_transition(
        state["difficulty_level"] if state else 2,
        state["consecutive_high"] if state else 0,
        score,
        low_threshold=settings["low_threshold"],
        high_threshold=settings["high_threshold"],
        high_streak=settings["high_streak"],
    )
    conn.execute(sa.text(f"""
        INSERT INTO {S}.learner_course_state
            (user_id, course_id, difficulty_level, consecutive_high, consecutive_low, last_score)
        VALUES (:user, :course, :level, :high, :low, :score)
        ON CONFLICT (user_id, course_id) DO UPDATE SET
            difficulty_level = EXCLUDED.difficulty_level,
            consecutive_high = EXCLUDED.consecutive_high,
            consecutive_low = EXCLUDED.consecutive_low,
            last_score = EXCLUDED.last_score, updated_at = now()
    """), {
        "user": user_id, "course": context["course_id"], "level": decision["difficulty_level"],
        "high": decision["consecutive_high"], "low": decision["consecutive_low"], "score": score,
    })
    kind = decision["recommendation"]
    if kind == "hold":
        return decision
    target = context["lesson_id"]
    reason = (
        f"Score {score}% was below the {settings['low_threshold']}% support threshold."
        if kind == "remedial" else
        f"Repeated scores at or above {settings['high_threshold']}% indicate readiness for a challenge."
    )
    conn.execute(sa.text(f"""
        INSERT INTO {S}.adaptive_recommendations
            (user_id, course_id, source_quiz_id, target_lesson_id, recommendation_type, title, reason)
        VALUES (:user, :course, :quiz, :lesson, :kind, :title, :reason)
    """), {
        "user": user_id, "course": context["course_id"], "quiz": quiz_id, "lesson": target,
        "kind": kind, "title": "Recommended review" if kind == "remedial" else "Ready for an extension",
        "reason": reason,
    })
    if (kind == "remedial" and settings["allow_remedial"]) or kind == "extension":
        existing = conn.execute(sa.text(f"""
            SELECT 1 FROM {S}.content_drafts
            WHERE source_lesson_id = :lesson AND draft_type = :kind AND status = 'pending'
        """), {"lesson": target, "kind": kind}).scalar()
        if not existing:
            lesson_by_lang = {lang: get_lesson(conn, target, lang=lang) or {} for lang in ("en", "et", "lt", "es")}
            payload = _draft_payload(kind, lesson_by_lang, score)
            module_id = lesson_by_lang["en"].get("module_id")
            conn.execute(sa.text(f"""
                INSERT INTO {S}.content_drafts
                    (course_id, module_id, source_lesson_id, draft_type, difficulty_level, content, created_by)
                VALUES (:course, :module, :lesson, :kind, :level, :content, :user)
            """), {
                "course": context["course_id"], "module": module_id, "lesson": target, "kind": kind,
                "level": decision["difficulty_level"], "content": json.dumps(payload), "user": user_id,
            })
        question_exists = conn.execute(sa.text(f"""
            SELECT 1 FROM {S}.content_drafts
            WHERE source_lesson_id = :lesson AND draft_type = 'quiz_variant'
              AND difficulty_level = :level AND status = 'pending'
        """), {"lesson": target, "level": decision["difficulty_level"]}).scalar()
        if not question_exists:
            lesson_by_lang = {lang: get_lesson(conn, target, lang=lang) or {} for lang in ("en", "et", "lt", "es")}
            conn.execute(sa.text(f"""
                INSERT INTO {S}.content_drafts
                    (course_id, module_id, source_lesson_id, draft_type, difficulty_level, content, created_by)
                VALUES (:course, :module, :lesson, 'quiz_variant', :level, :content, :user)
            """), {
                "course": context["course_id"], "module": lesson_by_lang["en"].get("module_id"),
                "lesson": target, "level": decision["difficulty_level"],
                "content": json.dumps(_question_draft_payload(lesson_by_lang, decision["difficulty_level"])), "user": user_id,
            })
    return decision


def get_learning_path(conn, *, user_id: int, course_id: int, lang: str = "en") -> list[dict]:
    rows = conn.execute(sa.text(f"""
        SELECT l.*, m.title AS module_title, m.order_idx AS module_order
        FROM {S}.lessons l JOIN {S}.modules m ON m.id = l.module_id
        WHERE m.course_id = :course ORDER BY m.order_idx, l.order_idx
    """), {"course": course_id}).mappings().all()
    lessons = _localized(rows, "lessons", lang, conn)
    settings = get_course_learning_settings(conn, course_id)
    if settings["strategy"] != "adaptive" or not settings["allow_reorder"]:
        return lessons
    state = conn.execute(sa.text(f"""
        SELECT difficulty_level FROM {S}.learner_course_state
        WHERE user_id = :user AND course_id = :course
    """), {"user": user_id, "course": course_id}).scalar() or 2
    targets = {row[0] for row in conn.execute(sa.text(f"""
        SELECT target_lesson_id FROM {S}.adaptive_recommendations
        WHERE user_id = :user AND course_id = :course AND status = 'pending'
          AND target_lesson_id IS NOT NULL
    """), {"user": user_id, "course": course_id}).all()}
    ordered = sorted(lessons, key=lambda row: (
        0 if row["id"] in targets else 1,
        0 if row.get("lesson_kind") == "remedial" and state == 1 else 1,
        abs((row.get("difficulty_level") or 2) - state),
        row.get("module_order") or 0,
        row.get("order_idx") or 0,
    ))
    # Adaptive priority never moves a lesson ahead of its explicit prerequisite.
    for _ in range(len(ordered)):
        positions = {row["id"]: index for index, row in enumerate(ordered)}
        changed = False
        for index, row in enumerate(list(ordered)):
            prerequisite = row.get("prerequisite_lesson_id")
            if prerequisite in positions and positions[prerequisite] > index:
                dependency = ordered.pop(positions[prerequisite])
                ordered.insert(index, dependency)
                changed = True
                break
        if not changed:
            break
    return ordered


def learning_time_report(
    conn,
    course_ids: list[int] | None = None,
    assigned_by: int | None = None,
) -> list[dict]:
    conditions = []
    params = {}
    if course_ids is not None:
        if not course_ids:
            return []
        conditions.append("lt.course_id = ANY(:courses)")
        params["courses"] = course_ids
    if assigned_by is not None:
        conditions.append(f"""EXISTS (
            SELECT 1 FROM {S}.course_assignments ca
            WHERE ca.user_id = lt.user_id AND ca.course_id = lt.course_id
              AND ca.assigned_by = :assigned_by
        )""")
        params["assigned_by"] = assigned_by
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = conn.execute(sa.text(f"""
        WITH times AS (
            SELECT lt.user_id, lt.course_id,
                   sum(lt.seconds_active) AS seconds_active,
                   sum(lt.seconds_active) FILTER (WHERE lt.resource_type='lesson') AS lesson_seconds,
                   sum(lt.seconds_active) FILTER (WHERE lt.resource_type='quiz') AS quiz_seconds,
                   sum(lt.seconds_active) FILTER (WHERE lt.resource_type='tutor') AS tutor_seconds
            FROM {S}.learning_time lt {where}
            GROUP BY lt.user_id, lt.course_id
        ), attempts AS (
            SELECT qa.user_id, m.course_id, round(avg(qa.score)) AS average_score
            FROM {S}.quiz_attempts qa JOIN {S}.quizzes q ON q.id=qa.quiz_id
            JOIN {S}.lessons l ON l.id=q.lesson_id JOIN {S}.modules m ON m.id=l.module_id
            GROUP BY qa.user_id, m.course_id
        ), progress AS (
            SELECT t.user_id, t.course_id, count(DISTINCT l.id) AS total_lessons,
                   count(DISTINCT l.id) FILTER (WHERE lp.status='completed') AS completed_lessons
            FROM times t JOIN {S}.modules m ON m.course_id=t.course_id
            JOIN {S}.lessons l ON l.module_id=m.id AND COALESCE(l.lesson_kind,'core')='core'
            LEFT JOIN {S}.lesson_progress lp ON lp.lesson_id=l.id AND lp.user_id=t.user_id
            GROUP BY t.user_id, t.course_id
        )
        SELECT u.id AS user_id, u.display_name, u.email, c.id AS course_id, c.title AS course_title,
               COALESCE(t.seconds_active, 0) AS seconds_active,
               COALESCE(t.lesson_seconds, 0) AS lesson_seconds,
               COALESCE(t.quiz_seconds, 0) AS quiz_seconds,
               COALESCE(t.tutor_seconds, 0) AS tutor_seconds,
               a.average_score, COALESCE(p.completed_lessons, 0) AS completed_lessons,
               COALESCE(p.total_lessons, 0) AS total_lessons,
               COALESCE(s.difficulty_level, 2) AS difficulty_level, s.last_score
        FROM times t JOIN {S}.users u ON u.id = t.user_id
        LEFT JOIN {S}.courses c ON c.id = t.course_id
        LEFT JOIN attempts a ON a.user_id=t.user_id AND a.course_id=t.course_id
        LEFT JOIN progress p ON p.user_id=t.user_id AND p.course_id=t.course_id
        LEFT JOIN {S}.learner_course_state s ON s.user_id=t.user_id AND s.course_id=t.course_id
        ORDER BY t.seconds_active DESC
    """), params).mappings().all()
    return [dict(row) for row in rows]
