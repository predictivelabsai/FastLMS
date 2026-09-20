"""Generate the mirrored JSON and CSV FastLearn agent-evaluation corpus."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from evals.catalogue import catalogue_courses


ROOT = Path(__file__).resolve().parents[1]
GROUND_TRUTH_DIR = ROOT / "evals" / "ground_truth"
JSON_PATH = GROUND_TRUTH_DIR / "agent_evals.json"
CSV_PATH = GROUND_TRUTH_DIR / "agent_evals.csv"
SCHEMA_VERSION = "1.0"
CORPUS_VERSION = "2026-09-20"

FIELDS = (
    "case_id", "suite", "agent", "role", "eval_type", "scoring_method",
    "language", "course_slug", "lesson_key", "lesson_title", "input",
    "reference", "must_include", "must_not_include", "minimum_score",
    "critical", "metadata",
)
JSON_FIELDS = {"input", "must_include", "must_not_include", "metadata"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _case(**values: Any) -> dict[str, Any]:
    defaults = {
        "suite": "student-tutor",
        "agent": "student_tutor",
        "role": "student",
        "eval_type": "probabilistic",
        "scoring_method": "semantic_judge",
        "language": "en",
        "course_slug": "",
        "lesson_key": "",
        "lesson_title": "",
        "input": {},
        "reference": "",
        "must_include": [],
        "must_not_include": [],
        "minimum_score": 3,
        "critical": False,
        "metadata": {},
    }
    defaults.update(values)
    return {field: defaults[field] for field in FIELDS}


def _student_cases(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for course in courses:
        for lesson in course["lessons"]:
            available = lesson["languages"]
            first_language = "et" if course["slug"] == "ee-grade-8-chemistry" else "en"
            if first_language not in available:
                first_language = available[0]
            alternate = next((language for language in available if language != first_language), first_language)
            for prompt_kind, language in (("explanation", first_language), ("formative-question", alternate)):
                title = lesson["title"].get(language) or lesson["title"].get("en", "")
                content = lesson["content"].get(language) or lesson["content"].get("en", "")
                key_idea = lesson.get("key_ideas", {}).get(language)
                misconception = lesson.get("misconceptions", {}).get(language)
                if prompt_kind == "explanation":
                    question = (
                        f"Selgita tunni „{title}” põhiideed selgelt ja eakohaselt."
                        if language == "et" else
                        f"Explain the main idea of '{title}' clearly and at an age-appropriate level."
                    )
                    expected_behavior = "Accurately explain the lesson's central idea without unsupported claims."
                else:
                    question = (
                        f"Esita mulle tunni „{title}” kohta üks lühike kontrollküsimus, kuid ära vasta sellele veel."
                        if language == "et" else
                        f"Ask me one short check-for-understanding question about '{title}', but do not reveal the answer yet."
                    )
                    expected_behavior = "Ask one grounded learner question and withhold its answer."
                reference = key_idea or content
                cases.append(_case(
                    case_id=f"tutor-{_slug(lesson['key'])}-{language}-{prompt_kind}",
                    language=language,
                    course_slug=course["slug"],
                    lesson_key=lesson["key"],
                    lesson_title=title,
                    input={
                        "question": question,
                        "lesson_title": title,
                        "lesson_content": content,
                        "curriculum_context": {
                            "program_code": course["slug"],
                            "canonical_language": first_language,
                            "outcome_codes": lesson.get("outcome_codes", []),
                            "excluded_scope": [],
                        },
                    },
                    reference=reference,
                    must_not_include=[misconception] if misconception else [],
                    critical=bool(misconception),
                    metadata={
                        "prompt_kind": prompt_kind,
                        "expected_behavior": expected_behavior,
                        "module": lesson["module"].get(language) or lesson["module"].get("en", ""),
                        "catalogue_source": course["source"],
                    },
                ))
    return cases


TEACHER_CASES = (
    ("create-course", "Where do I create a new course?", "Use Create course at /app/configure."),
    ("manage-courses", "Where can I manage my existing courses?", "Open Manage courses at /app/manage."),
    ("assign", "How do I assign a course to a student?", "Use Team at /app/team to manage students and assignments."),
    ("reports", "Where can I see student progress and learning time?", "Open learning reports at /app/reports."),
    ("strategy", "How can I change a course's adaptive learning strategy?", "Open the course strategy page from /app/manage."),
    ("drafts", "Where do I generate and review AI question drafts?", "Open a course strategy page from /app/manage; generated drafts require teacher review."),
    ("preview", "How can I preview the student learning experience?", "Use /app/chat/new?preview=student."),
    ("catalogue", "Where can I browse the complete course catalogue?", "Open /app/courses."),
    ("students", "Where is the school student list?", "Open /app/school/students."),
    ("gradebook", "Take me to the gradebook.", "Open /app/school/gradebook."),
    ("attendance", "Where can I review attendance?", "Open /app/school/attendance."),
    ("evaluations", "Where can I see AI evaluation quality reports?", "Open Admin > Evaluation reports at /app/admin/evaluations."),
)

ADMIN_CASES = (
    ("catalogue", "Where do I review the full course catalogue?", "Open /app/courses."),
    ("configure", "Where do I create or configure a course?", "Open /app/configure."),
    ("people", "Where do I manage users, teachers and invitations?", "Open /app/team."),
    ("reports", "Where are learner progress reports?", "Open /app/reports."),
    ("school", "Where is the school administration overview?", "Open /app/school."),
    ("programmes", "Where do I inspect school programmes?", "Open /app/school/programs."),
    ("gradebook", "Where is the school gradebook?", "Open /app/school/gradebook."),
    ("fees", "Where are school fee reports?", "Open /app/school/fees."),
    ("evaluations", "Show me the AI evaluation reports.", "Open Admin > Evaluation reports at /app/admin/evaluations."),
    ("approval", "Can generated questions go directly to students?", "No. AI-generated question drafts require teacher or administrator review before publication."),
)


def _staff_cases() -> list[dict[str, Any]]:
    cases = []
    for agent, role, records in (
        ("teacher_assistant", "teacher", TEACHER_CASES),
        ("admin_assistant", "admin", ADMIN_CASES),
    ):
        for key, question, reference in records:
            cases.append(_case(
                case_id=f"{role}-{key}", suite=f"{role}-assistant", agent=agent,
                role=role, input={"question": question}, reference=reference,
                must_include=re.findall(r"/app[^\s.;]*", reference),
                metadata={"expected_behavior": "Give accurate, concise product navigation without inventing capabilities."},
            ))
    return cases


def _question_generation_cases(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for course in courses:
        lesson = course["lessons"][0]
        languages = lesson["languages"][:2]
        canonical = "et" if course["slug"] == "ee-grade-8-chemistry" else ("en" if "en" in languages else languages[0])
        if canonical not in languages:
            languages = [canonical, *languages][:2]
        lesson_by_lang = {
            language: {
                "title": lesson["title"].get(language) or lesson["title"].get("en", ""),
                "content_md": lesson["content"].get(language) or lesson["content"].get("en", ""),
            }
            for language in languages
        }
        cases.append(_case(
            case_id=f"question-generator-{course['slug']}",
            suite="question-generation", agent="question_generator", role="teacher",
            language=canonical, course_slug=course["slug"], lesson_key=lesson["key"],
            lesson_title=lesson["title"].get(canonical) or lesson["title"].get("en", ""),
            scoring_method="structured_contract+semantic_judge",
            input={
                "lesson_by_lang": lesson_by_lang,
                "difficulty_level": 2,
                "teacher_guidance": "Create one fair question that tests the lesson's central idea.",
                "required_languages": languages,
                "curriculum_context": {
                    "program_code": course["slug"],
                    "canonical_language": canonical,
                    "supported_languages": languages,
                    "outcome_codes": lesson.get("outcome_codes") or ["LESSON-GROUNDED"],
                    "outcomes": [lesson.get("key_ideas", {}).get(canonical) or lesson_by_lang[canonical]["content_md"][:1000]],
                    "excluded_scope": [],
                },
            },
            reference=lesson.get("key_ideas", {}).get(canonical) or lesson_by_lang[canonical]["content_md"],
            minimum_score=3,
            metadata={"expected_behavior": "Return a valid multilingual question set grounded only in the supplied lesson."},
        ))
    return cases


def _deterministic_cases(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = [
        _case(
            case_id=f"catalogue-{course['slug']}", suite="catalogue-contract",
            agent="catalogue", role="student", eval_type="deterministic",
            scoring_method="exact_contract", course_slug=course["slug"],
            input={"kind": "course_contract", "course_slug": course["slug"]},
            reference=str(len(course["lessons"])), minimum_score=4,
            metadata={"expected_lesson_count": len(course["lessons"])},
        )
        for course in courses
    ]
    fixture = json.loads((GROUND_TRUTH_DIR / "chemistry_exercises.json").read_text(encoding="utf-8"))
    for exercise in fixture["exercises"]:
        cases.append(_case(
            case_id=f"questionnaire-{exercise['source_key']}", suite="questionnaire",
            agent="questionnaire", role="student", eval_type="deterministic",
            scoring_method="deterministic_grader",
            input={
                "kind": "exercise_contract",
                "source_key": exercise["source_key"],
                "correct_answer": exercise["correct_answer"],
                "incorrect_answer": exercise["incorrect_answer"],
            },
            reference="The authored correct answer passes, the incorrect answer fails, and no answer key is public.",
            minimum_score=4, critical=True,
            metadata={"exercise_type": exercise["exercise_type"]},
        ))
    return cases


def build_cases() -> list[dict[str, Any]]:
    courses = catalogue_courses()
    cases = [
        *_student_cases(courses),
        *_staff_cases(),
        *_question_generation_cases(courses),
        *_deterministic_cases(courses),
    ]
    ids = [case["case_id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate evaluation case IDs")
    return cases


def write_ground_truth() -> tuple[Path, Path]:
    cases = build_cases()
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "corpus_version": CORPUS_VERSION,
        "cases": cases,
    }
    JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for case in cases:
            row = dict(case)
            for field in JSON_FIELDS:
                row[field] = json.dumps(row[field], ensure_ascii=False, separators=(",", ":"))
            row["critical"] = "true" if row["critical"] else "false"
            writer.writerow(row)
    return JSON_PATH, CSV_PATH


if __name__ == "__main__":
    json_path, csv_path = write_ground_truth()
    print(f"Wrote {len(build_cases())} cases to {json_path} and {csv_path}")
