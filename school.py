"""FastLMS school-administration layer.

Adds the ``frappe/education`` half on top of FastLMS's course-delivery core:
academic calendar, students & guardians, programs & enrolment, a gradebook
(assessments + grading scale), attendance, and fees. Postgres, in the same
``fastlms`` schema, following db.py's SQLAlchemy patterns.

Bootstrap from ``db.bootstrap_schema()`` (already wired) and seed with
``school.seed_school(conn)`` (called by seed.py).
"""
from __future__ import annotations

import random
from datetime import date, timedelta

import sqlalchemy as sa

from db import SCHEMA

S = SCHEMA

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS {S}.academic_years (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    start_date  DATE,
    end_date    DATE,
    is_current  BOOLEAN NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS {S}.academic_terms (
    id          SERIAL PRIMARY KEY,
    year_id     INTEGER REFERENCES {S}.academic_years(id),
    name        TEXT NOT NULL,
    start_date  DATE,
    end_date    DATE,
    is_current  BOOLEAN NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS {S}.programs (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT
);
CREATE TABLE IF NOT EXISTS {S}.program_courses (
    program_id  INTEGER REFERENCES {S}.programs(id),
    course_id   INTEGER REFERENCES {S}.courses(id),
    position    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (program_id, course_id)
);
CREATE TABLE IF NOT EXISTS {S}.student_groups (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    term_id     INTEGER REFERENCES {S}.academic_terms(id),
    program_id  INTEGER REFERENCES {S}.programs(id)
);
CREATE TABLE IF NOT EXISTS {S}.students (
    id          SERIAL PRIMARY KEY,
    code        TEXT UNIQUE,
    first_name  TEXT,
    last_name   TEXT,
    email       TEXT,
    dob         DATE,
    gender      TEXT,
    group_id    INTEGER REFERENCES {S}.student_groups(id),
    user_id     INTEGER REFERENCES {S}.users(id),
    enrolled_on DATE NOT NULL DEFAULT current_date
);
CREATE TABLE IF NOT EXISTS {S}.guardians (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT,
    phone       TEXT
);
CREATE TABLE IF NOT EXISTS {S}.guardian_student (
    guardian_id INTEGER REFERENCES {S}.guardians(id),
    student_id  INTEGER REFERENCES {S}.students(id),
    relation    TEXT,
    PRIMARY KEY (guardian_id, student_id)
);
CREATE TABLE IF NOT EXISTS {S}.program_enrolments (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER REFERENCES {S}.students(id),
    program_id  INTEGER REFERENCES {S}.programs(id),
    term_id     INTEGER REFERENCES {S}.academic_terms(id),
    status      TEXT NOT NULL DEFAULT 'Active',
    enrolled_on DATE NOT NULL DEFAULT current_date
);
CREATE TABLE IF NOT EXISTS {S}.grading_scales (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS {S}.grading_intervals (
    id          SERIAL PRIMARY KEY,
    scale_id    INTEGER REFERENCES {S}.grading_scales(id),
    grade       TEXT NOT NULL,
    threshold   NUMERIC NOT NULL          -- min % for this grade
);
CREATE TABLE IF NOT EXISTS {S}.assessments (
    id          SERIAL PRIMARY KEY,
    course_id   INTEGER REFERENCES {S}.courses(id),
    term_id     INTEGER REFERENCES {S}.academic_terms(id),
    name        TEXT NOT NULL,
    max_score   NUMERIC NOT NULL DEFAULT 100,
    weight      NUMERIC NOT NULL DEFAULT 1,
    scale_id    INTEGER REFERENCES {S}.grading_scales(id),
    assessed_on DATE
);
CREATE TABLE IF NOT EXISTS {S}.assessment_results (
    id            SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES {S}.assessments(id),
    student_id    INTEGER REFERENCES {S}.students(id),
    score         NUMERIC,
    grade         TEXT
);
CREATE TABLE IF NOT EXISTS {S}.attendance (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER REFERENCES {S}.students(id),
    group_id    INTEGER REFERENCES {S}.student_groups(id),
    att_date    DATE NOT NULL,
    status      TEXT NOT NULL            -- Present | Absent | Late | Excused
);
CREATE TABLE IF NOT EXISTS {S}.fee_structures (
    id          SERIAL PRIMARY KEY,
    program_id  INTEGER REFERENCES {S}.programs(id),
    term_id     INTEGER REFERENCES {S}.academic_terms(id),
    category    TEXT,
    amount      NUMERIC NOT NULL
);
CREATE TABLE IF NOT EXISTS {S}.fees (
    id            SERIAL PRIMARY KEY,
    student_id    INTEGER REFERENCES {S}.students(id),
    fee_structure_id INTEGER REFERENCES {S}.fee_structures(id),
    due_date      DATE,
    amount        NUMERIC NOT NULL,
    paid          NUMERIC NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'Unpaid'   -- Unpaid | Partly Paid | Paid | Overdue
);
CREATE TABLE IF NOT EXISTS {S}.fee_payments (
    id          SERIAL PRIMARY KEY,
    fee_id      INTEGER REFERENCES {S}.fees(id),
    paid_on     DATE NOT NULL DEFAULT current_date,
    amount      NUMERIC NOT NULL,
    method      TEXT
);
CREATE INDEX IF NOT EXISTS idx_sch_students_group ON {S}.students(group_id);
CREATE INDEX IF NOT EXISTS idx_sch_results_student ON {S}.assessment_results(student_id);
CREATE INDEX IF NOT EXISTS idx_sch_att_student ON {S}.attendance(student_id, att_date);
CREATE INDEX IF NOT EXISTS idx_sch_fees_student ON {S}.fees(student_id);
"""


def bootstrap(conn):
    for stmt in SCHEMA_SQL.split(";"):
        if stmt.strip():
            conn.execute(sa.text(stmt))


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _all(conn, sql, **p):
    return [dict(r) for r in conn.execute(sa.text(sql), p).mappings().all()]


def _one(conn, sql, **p):
    r = conn.execute(sa.text(sql), p).mappings().first()
    return dict(r) if r else None


def current_term(conn):
    return _one(conn, f"SELECT * FROM {S}.academic_terms WHERE is_current = true LIMIT 1") or \
        _one(conn, f"SELECT * FROM {S}.academic_terms ORDER BY id DESC LIMIT 1")


def school_kpis(conn):
    students = conn.execute(sa.text(f"SELECT COUNT(*) FROM {S}.students")).scalar() or 0
    programs = conn.execute(sa.text(f"SELECT COUNT(*) FROM {S}.programs")).scalar() or 0
    att = _one(conn, f"""SELECT
        COUNT(*) FILTER (WHERE status='Present') AS present, COUNT(*) AS total
        FROM {S}.attendance""")
    att_rate = round(100 * att["present"] / att["total"]) if att and att["total"] else 0
    fees = _one(conn, f"SELECT COALESCE(SUM(amount-paid),0) AS due FROM {S}.fees WHERE status != 'Paid'")
    return {"students": students, "programs": programs, "attendance_rate": att_rate,
            "fees_outstanding": float(fees["due"]) if fees else 0}


def list_programs(conn):
    return _all(conn, f"""
        SELECT p.*,
          (SELECT COUNT(*) FROM {S}.program_enrolments e WHERE e.program_id=p.id) AS students,
          (SELECT COUNT(*) FROM {S}.program_courses pc WHERE pc.program_id=p.id) AS courses
        FROM {S}.programs p ORDER BY p.name""")


def list_students(conn, group_id=None, q=None):
    where, params = [], {}
    if group_id:
        where.append("s.group_id = :g"); params["g"] = group_id
    if q:
        where.append("(s.first_name ILIKE :q OR s.last_name ILIKE :q OR s.code ILIKE :q)"); params["q"] = f"%{q}%"
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    return _all(conn, f"""
        SELECT s.*, g.name AS group_name FROM {S}.students s
        LEFT JOIN {S}.student_groups g ON g.id = s.group_id
        {clause} ORDER BY s.last_name, s.first_name LIMIT 300""", **params)


def student_detail(conn, sid):
    return _one(conn, f"""
        SELECT s.*, g.name AS group_name, pr.name AS program_name FROM {S}.students s
        LEFT JOIN {S}.student_groups g ON g.id = s.group_id
        LEFT JOIN {S}.programs pr ON pr.id = g.program_id
        WHERE s.id = :id""", id=sid)


def student_guardians(conn, sid):
    return _all(conn, f"""
        SELECT gd.*, gs.relation FROM {S}.guardian_student gs
        JOIN {S}.guardians gd ON gd.id = gs.guardian_id WHERE gs.student_id = :id""", id=sid)


def student_grades(conn, sid):
    return _all(conn, f"""
        SELECT a.name, c.title AS course, r.score, a.max_score, r.grade FROM {S}.assessment_results r
        JOIN {S}.assessments a ON a.id = r.assessment_id
        LEFT JOIN {S}.courses c ON c.id = a.course_id
        WHERE r.student_id = :id ORDER BY a.assessed_on DESC NULLS LAST""", id=sid)


def student_attendance(conn, sid, limit=20):
    return _all(conn, f"""
        SELECT att_date, status FROM {S}.attendance WHERE student_id = :id
        ORDER BY att_date DESC LIMIT {int(limit)}""", id=sid)


def student_fees(conn, sid):
    return _all(conn, f"""
        SELECT f.*, fs.category FROM {S}.fees f
        LEFT JOIN {S}.fee_structures fs ON fs.id = f.fee_structure_id
        WHERE f.student_id = :id ORDER BY f.due_date""", id=sid)


def gradebook(conn, group_id):
    """Average % per student for a group, plus per-assessment columns."""
    return _all(conn, f"""
        SELECT s.id, s.first_name, s.last_name,
          ROUND(AVG(100.0 * r.score / NULLIF(a.max_score,0))) AS avg_pct,
          COUNT(r.id) AS n
        FROM {S}.students s
        LEFT JOIN {S}.assessment_results r ON r.student_id = s.id
        LEFT JOIN {S}.assessments a ON a.id = r.assessment_id
        WHERE s.group_id = :g
        GROUP BY s.id, s.first_name, s.last_name
        ORDER BY avg_pct DESC NULLS LAST""", g=group_id)


def attendance_register(conn, group_id, on_date=None):
    where = "s.group_id = :g"
    params = {"g": group_id}
    if on_date:
        where += " AND att.att_date = :d"; params["d"] = on_date
    return _all(conn, f"""
        SELECT s.id, s.first_name, s.last_name,
          COUNT(*) FILTER (WHERE att.status='Present') AS present,
          COUNT(*) FILTER (WHERE att.status='Absent') AS absent,
          COUNT(att.id) AS total
        FROM {S}.students s
        LEFT JOIN {S}.attendance att ON att.student_id = s.id
        WHERE {where}
        GROUP BY s.id, s.first_name, s.last_name ORDER BY s.last_name""", **params)


def list_groups(conn):
    return _all(conn, f"""
        SELECT g.*, pr.name AS program_name, t.name AS term_name,
          (SELECT COUNT(*) FROM {S}.students s WHERE s.group_id=g.id) AS students
        FROM {S}.student_groups g
        LEFT JOIN {S}.programs pr ON pr.id = g.program_id
        LEFT JOIN {S}.academic_terms t ON t.id = g.term_id ORDER BY g.name""")


def fees_summary(conn):
    return _all(conn, f"""
        SELECT status, COUNT(*) AS n, COALESCE(SUM(amount-paid),0) AS outstanding
        FROM {S}.fees GROUP BY status ORDER BY status""")


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

FIRST = ["Aisha", "Liam", "Sofia", "Noah", "Mia", "Ethan", "Priya", "Lucas", "Chloe", "Mateo",
         "Hana", "Omar", "Isla", "Diego", "Yuki", "Nora", "Kai", "Zara", "Leo", "Amara",
         "Felix", "Ravi", "Elena", "Tariq", "Maya", "Sven", "Ingrid", "Marco", "Lena", "Pablo"]
LAST = ["Okafor", "Nguyen", "Rossi", "Andersen", "Kim", "Haddad", "Silva", "Muller", "Costa",
        "Tanaka", "Khan", "Lindqvist", "Moreau", "Ito", "Petrov", "Schmidt", "Dubois", "Reyes"]
GRADES_SCALE = [("A", 80), ("B", 70), ("C", 60), ("D", 50), ("E", 40), ("U", 0)]


def _grade_for(pct, intervals):
    for g, thr in intervals:
        if pct >= thr:
            return g
    return "U"


def seed_school(conn, rng=None):
    """Idempotent-ish seed: clears school tables then repopulates. Call after the
    course/users seed so courses exist."""
    rng = rng or random.Random(20260612)
    today = date(2026, 6, 12)

    for t in ("fee_payments", "fees", "fee_structures", "attendance", "assessment_results",
              "assessments", "grading_intervals", "grading_scales", "program_enrolments",
              "guardian_student", "guardians", "students", "student_groups",
              "program_courses", "programs", "academic_terms", "academic_years"):
        conn.execute(sa.text(f"DELETE FROM {S}.{t}"))

    # academic calendar
    conn.execute(sa.text(f"INSERT INTO {S}.academic_years(name,start_date,end_date,is_current) "
                         "VALUES ('2025/26', '2025-09-01', '2026-07-20', true)"))
    year_id = conn.execute(sa.text(f"SELECT id FROM {S}.academic_years ORDER BY id DESC LIMIT 1")).scalar()
    terms = [("Autumn", "2025-09-01", "2025-12-19", False),
             ("Spring", "2026-01-06", "2026-04-03", False),
             ("Summer", "2026-04-20", "2026-07-20", True)]
    term_ids = {}
    for nm, sd, ed, cur in terms:
        conn.execute(sa.text(f"INSERT INTO {S}.academic_terms(year_id,name,start_date,end_date,is_current) "
                             "VALUES (:y,:n,:s,:e,:c)"), {"y": year_id, "n": nm, "s": sd, "e": ed, "c": cur})
    for r in conn.execute(sa.text(f"SELECT id,name FROM {S}.academic_terms")).mappings().all():
        term_ids[r["name"]] = r["id"]
    cur_term = term_ids["Summer"]

    # grading scale
    conn.execute(sa.text(f"INSERT INTO {S}.grading_scales(name) VALUES ('Standard A–U')"))
    scale_id = conn.execute(sa.text(f"SELECT id FROM {S}.grading_scales ORDER BY id DESC LIMIT 1")).scalar()
    for g, thr in GRADES_SCALE:
        conn.execute(sa.text(f"INSERT INTO {S}.grading_intervals(scale_id,grade,threshold) VALUES (:s,:g,:t)"),
                     {"s": scale_id, "g": g, "t": thr})

    # programs from existing course categories (fallback to generic)
    courses = conn.execute(sa.text(f"SELECT id,title,category FROM {S}.courses")).mappings().all()
    courses = [dict(c) for c in courses]
    cats = sorted({(c["category"] or "General") for c in courses}) or ["General"]
    prog_ids = {}
    for cat in cats:
        conn.execute(sa.text(f"INSERT INTO {S}.programs(name,description) VALUES (:n,:d)"),
                     {"n": f"{cat} Programme", "d": f"A term programme covering {cat.lower()} courses."})
        pid = conn.execute(sa.text(f"SELECT id FROM {S}.programs ORDER BY id DESC LIMIT 1")).scalar()
        prog_ids[cat] = pid
    for pos, c in enumerate(courses):
        pid = prog_ids.get(c["category"] or "General")
        if pid:
            conn.execute(sa.text(f"INSERT INTO {S}.program_courses(program_id,course_id,position) "
                                 "VALUES (:p,:c,:o) ON CONFLICT DO NOTHING"),
                         {"p": pid, "c": c["id"], "o": pos})

    # student groups (one per program, current term)
    group_ids = []
    for cat, pid in prog_ids.items():
        conn.execute(sa.text(f"INSERT INTO {S}.student_groups(name,term_id,program_id) VALUES (:n,:t,:p)"),
                     {"n": f"{cat[:6]} Group", "t": cur_term, "p": pid})
        gid = conn.execute(sa.text(f"SELECT id FROM {S}.student_groups ORDER BY id DESC LIMIT 1")).scalar()
        group_ids.append((gid, pid))

    # students + guardians + enrolment
    student_ids = []
    n = 0
    for gid, pid in group_ids:
        for _ in range(rng.randint(8, 14)):
            n += 1
            fn, ln = rng.choice(FIRST), rng.choice(LAST)
            dob = date(2026 - rng.randint(15, 19), rng.randint(1, 12), rng.randint(1, 28))
            conn.execute(sa.text(f"""INSERT INTO {S}.students(code,first_name,last_name,email,dob,gender,group_id,enrolled_on)
                VALUES (:code,:fn,:ln,:em,:dob,:gen,:g,:en)"""),
                {"code": f"STU-{1000+n}", "fn": fn, "ln": ln,
                 "em": f"{fn.lower()}.{ln.lower()}{n}@school.example", "dob": dob.isoformat(),
                 "gen": rng.choice(["F", "M", "X"]), "g": gid, "en": "2025-09-01"})
            sid = conn.execute(sa.text(f"SELECT id FROM {S}.students ORDER BY id DESC LIMIT 1")).scalar()
            student_ids.append((sid, gid, pid))
            # guardian
            gn = f"{rng.choice(FIRST)} {ln}"
            conn.execute(sa.text(f"INSERT INTO {S}.guardians(name,email,phone) VALUES (:n,:e,:p)"),
                         {"n": gn, "e": f"{gn.lower().replace(' ', '.')}@home.example",
                          "p": f"+44 7{rng.randint(100,999)} {rng.randint(100000,999999)}"})
            guid = conn.execute(sa.text(f"SELECT id FROM {S}.guardians ORDER BY id DESC LIMIT 1")).scalar()
            conn.execute(sa.text(f"INSERT INTO {S}.guardian_student(guardian_id,student_id,relation) "
                                 "VALUES (:g,:s,:r)"),
                         {"g": guid, "s": sid, "r": rng.choice(["Mother", "Father", "Guardian"])})
            conn.execute(sa.text(f"INSERT INTO {S}.program_enrolments(student_id,program_id,term_id,status,enrolled_on) "
                                 "VALUES (:s,:p,:t,'Active','2025-09-01')"),
                         {"s": sid, "p": pid, "t": cur_term})

    # assessments per course (current term) + results
    intervals = GRADES_SCALE
    for c in courses:
        for an in ("Mid-term Test", "Coursework", "End-of-term Exam"):
            conn.execute(sa.text(f"""INSERT INTO {S}.assessments(course_id,term_id,name,max_score,weight,scale_id,assessed_on)
                VALUES (:c,:t,:n,100,:w,:sc,:d)"""),
                {"c": c["id"], "t": cur_term, "n": an, "w": rng.choice([1, 1, 2]),
                 "sc": scale_id, "d": (today - timedelta(days=rng.randint(5, 60))).isoformat()})
    assessments = conn.execute(sa.text(
        f"SELECT a.id, a.course_id FROM {S}.assessments a")).mappings().all()
    # map course -> program -> group, so only students in matching group get results
    course_prog = {c["id"]: prog_ids.get(c["category"] or "General") for c in courses}
    prog_students = {}
    for sid, gid, pid in student_ids:
        prog_students.setdefault(pid, []).append(sid)
    for a in assessments:
        pid = course_prog.get(a["course_id"])
        for sid in prog_students.get(pid, []):
            pct = max(15, min(100, int(rng.gauss(68, 16))))
            grade = _grade_for(pct, intervals)
            conn.execute(sa.text(f"INSERT INTO {S}.assessment_results(assessment_id,student_id,score,grade) "
                                 "VALUES (:a,:s,:sc,:g)"),
                         {"a": a["id"], "s": sid, "sc": pct, "g": grade})

    # attendance — last 20 weekdays
    sdays = []
    d = today
    while len(sdays) < 20:
        if d.weekday() < 5:
            sdays.append(d)
        d -= timedelta(days=1)
    for sid, gid, pid in student_ids:
        for dd in sdays:
            st = rng.choices(["Present", "Absent", "Late", "Excused"], weights=[86, 7, 4, 3])[0]
            conn.execute(sa.text(f"INSERT INTO {S}.attendance(student_id,group_id,att_date,status) "
                                 "VALUES (:s,:g,:d,:st)"),
                         {"s": sid, "g": gid, "d": dd.isoformat(), "st": st})

    # fees — one tuition structure per program/term + per-student fee + some payments
    for cat, pid in prog_ids.items():
        amt = rng.choice([1200, 1500, 1800, 2400])
        conn.execute(sa.text(f"INSERT INTO {S}.fee_structures(program_id,term_id,category,amount) "
                             "VALUES (:p,:t,'Tuition',:a)"),
                     {"p": pid, "t": cur_term, "a": amt})
        fsid = conn.execute(sa.text(f"SELECT id FROM {S}.fee_structures ORDER BY id DESC LIMIT 1")).scalar()
        for sid in prog_students.get(pid, []):
            roll = rng.random()
            if roll < 0.5:
                paid, status = amt, "Paid"
            elif roll < 0.7:
                paid, status = round(amt * rng.uniform(0.3, 0.6)), "Partly Paid"
            else:
                paid, status = 0, rng.choice(["Unpaid", "Overdue"])
            due = "2026-05-01"
            conn.execute(sa.text(f"""INSERT INTO {S}.fees(student_id,fee_structure_id,due_date,amount,paid,status)
                VALUES (:s,:f,:d,:a,:p,:st)"""),
                {"s": sid, "f": fsid, "d": due, "a": amt, "p": paid, "st": status})
            if paid > 0:
                fid = conn.execute(sa.text(f"SELECT id FROM {S}.fees ORDER BY id DESC LIMIT 1")).scalar()
                conn.execute(sa.text(f"INSERT INTO {S}.fee_payments(fee_id,paid_on,amount,method) "
                                     "VALUES (:f,:d,:a,:m)"),
                             {"f": fid, "d": "2026-04-15", "a": paid, "m": rng.choice(["Card", "Transfer"])})

    return {"students": len(student_ids), "programs": len(prog_ids), "groups": len(group_ids)}
