"""Stateful, chat-first course, quiz, and language-learning interactions."""

from __future__ import annotations

import json
from string import ascii_uppercase

import sqlalchemy as sa

import db
import language_learning as languages


COPY = {
    "en": {
        "welcome": "What would you like to learn? Choose a course below, or ask me anything.",
        "course": "Choose a lesson. Your adaptive path is ordered for you.",
        "complete": "Mark this lesson complete",
        "quiz": "Take the quiz",
        "lessons": "Choose another lesson",
        "courses": "Choose another course",
        "done": "Lesson complete — you earned **{xp} XP**.",
        "already": "This lesson is already complete.",
        "correct": "Correct.",
        "incorrect": "Not quite. The correct answer is **{answer}**.",
        "score": "Quiz complete: **{score}%** ({correct}/{total}).",
        "native": "Which language do you want FastLearn to explain from?",
        "target": "Your interface language is your starting language. Which language would you like to learn?",
        "speak": "Say the translation aloud before revealing it.",
        "reveal": "Reveal the answer",
        "change": "Choose another target language",
        "again": "Again",
        "hard": "Hard",
        "good": "Got it",
    },
    "et": {
        "welcome": "Mida soovid õppida? Vali allpool kursus või küsi minult midagi.",
        "course": "Vali tund. Sinu kohanduv õpitee on sinu jaoks järjestatud.",
        "complete": "Märgi tund lõpetatuks", "quiz": "Tee test",
        "lessons": "Vali teine tund", "courses": "Vali teine kursus",
        "done": "Tund lõpetatud — teenisid **{xp} XP**.", "already": "See tund on juba lõpetatud.",
        "correct": "Õige.", "incorrect": "Mitte päris. Õige vastus on **{answer}**.",
        "score": "Test lõpetatud: **{score}%** ({correct}/{total}).",
        "native": "Millisest keelest soovid selgitusi saada?",
        "target": "Kasutajaliidese keel on sinu lähtekeel. Millist keelt soovid õppida?",
        "speak": "Ütle tõlge valjusti enne vastuse näitamist.",
        "reveal": "Näita vastust", "change": "Vali teine sihtkeel",
        "again": "Uuesti", "hard": "Raske", "good": "Selge",
    },
    "lt": {
        "welcome": "Ko norėtum mokytis? Pasirink kursą arba klausk manęs bet ko.",
        "course": "Pasirink pamoką. Tavo adaptyvus kelias jau surikiuotas.",
        "complete": "Pažymėti pamoką baigta", "quiz": "Atlikti testą",
        "lessons": "Pasirinkti kitą pamoką", "courses": "Pasirinkti kitą kursą",
        "done": "Pamoka baigta — gavai **{xp} XP**.", "already": "Ši pamoka jau baigta.",
        "correct": "Teisingai.", "incorrect": "Ne visai. Teisingas atsakymas: **{answer}**.",
        "score": "Testas baigtas: **{score}%** ({correct}/{total}).",
        "native": "Kurčia kalba nori gauti paaiškinimus?",
        "target": "Sąsajos kalba yra tavo pradinė kalba. Kurią kalbą nori mokytis?",
        "speak": "Prieš parodydamas atsakymą pasakyk vertimą garsiai.",
        "reveal": "Rodyti atsakymą", "change": "Pasirinkti kitą kalbą",
        "again": "Dar kartą", "hard": "Sunku", "good": "Moku",
    },
    "es": {
        "welcome": "¿Qué quieres aprender? Elige un curso o pregúntame lo que quieras.",
        "course": "Elige una lección. Tu ruta adaptativa ya está ordenada para ti.",
        "complete": "Marcar la lección como terminada", "quiz": "Hacer el cuestionario",
        "lessons": "Elegir otra lección", "courses": "Elegir otro curso",
        "done": "Lección terminada — ganaste **{xp} XP**.", "already": "Esta lección ya está terminada.",
        "correct": "Correcto.", "incorrect": "No exactamente. La respuesta correcta es **{answer}**.",
        "score": "Cuestionario terminado: **{score}%** ({correct}/{total}).",
        "native": "¿Desde qué idioma quieres que FastLearn te explique?",
        "target": "El idioma de la interfaz es tu idioma inicial. ¿Qué idioma quieres aprender?",
        "speak": "Di la traducción en voz alta antes de mostrarla.",
        "reveal": "Mostrar la respuesta", "change": "Elegir otro idioma",
        "again": "Otra vez", "hard": "Difícil", "good": "Lo sé",
    },
}


def _copy(lang: str) -> dict:
    return COPY.get(lang, COPY["en"])


def _choices(items) -> list[dict]:
    return [
        {"key": ascii_uppercase[index], "label": str(label), "value": value}
        for index, (label, value) in enumerate(items)
        if index < len(ascii_uppercase)
    ]


def resolve_choice(message: str, choices: list[dict]) -> dict | None:
    """Resolve a click payload, a bare A/B reply, or an exact choice label."""
    answer = (message or "").strip().casefold()
    for choice in choices or []:
        if answer in {str(choice["key"]).casefold(), str(choice["label"]).strip().casefold()}:
            return choice
    return None


def _choice_markdown(choices: list[dict]) -> str:
    return "\n".join(f"**{choice['key']}.** {choice['label']}" for choice in choices)


def _course_by_id(conn, course_id: int, lang: str) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {db.S}.courses WHERE id = :id"), {"id": course_id}).mappings().first()
    return db._localized([row], "courses", lang, conn)[0] if row else None


def _course_for_lesson(conn, lesson_id: int, lang: str) -> dict | None:
    row = conn.execute(sa.text(f"""
        SELECT c.* FROM {db.S}.courses c
        JOIN {db.S}.modules m ON m.course_id = c.id
        JOIN {db.S}.lessons l ON l.module_id = m.id
        WHERE l.id = :lesson
    """), {"lesson": lesson_id}).mappings().first()
    return db._localized([row], "courses", lang, conn)[0] if row else None


def _course_picker(conn, lang: str) -> dict:
    choices = _choices((course["title"], course["id"]) for course in db.get_courses(conn, lang=lang))
    context = {"phase": "course_picker", "choices": choices}
    return {"title": "New Chat", "context": context,
            "content": f"{_copy(lang)['welcome']}\n\n{_choice_markdown(choices)}"}


def _show_course(conn, user_id: int, course_id: int, lang: str) -> dict:
    course = _course_by_id(conn, course_id, lang)
    if not course:
        return _course_picker(conn, lang)
    conn.execute(sa.text(f"""
        INSERT INTO {db.S}.enrolments (user_id, course_id)
        VALUES (:user, :course) ON CONFLICT DO NOTHING
    """), {"user": user_id, "course": course_id})
    path = db.get_learning_path(conn, user_id=user_id, course_id=course_id, lang=lang)
    choices = _choices((lesson["title"], lesson["id"]) for lesson in path)
    context = {"phase": "lesson_picker", "course_id": course_id, "choices": choices}
    description = course.get("description") or ""
    return {
        "title": course["title"], "context": context,
        "content": f"## {course['title']}\n\n{description}\n\n{_copy(lang)['course']}\n\n{_choice_markdown(choices)}",
    }


def _show_lesson(conn, user_id: int, lesson_id: int, lang: str) -> dict:
    lesson = db.get_lesson(conn, lesson_id, lang=lang)
    course = _course_for_lesson(conn, lesson_id, lang)
    if not lesson or not course:
        return _course_picker(conn, lang)
    quiz = db.get_quiz_for_lesson(conn, lesson_id, lang=lang)
    actions = [(_copy(lang)["complete"], "complete")]
    if quiz:
        actions.append((_copy(lang)["quiz"], "quiz"))
    actions.extend([(_copy(lang)["lessons"], "lessons"), (_copy(lang)["courses"], "courses")])
    choices = _choices(actions)
    context = {
        "phase": "lesson", "course_id": course["id"], "lesson_id": lesson_id,
        "quiz_id": quiz["id"] if quiz else None, "choices": choices,
    }
    meta = f"*{lesson.get('duration_min', 0)} min · +{lesson.get('xp_reward', 25)} XP*"
    return {
        "title": lesson["title"], "context": context, "lesson_id": lesson_id,
        "content": f"## {lesson['title']}\n\n{meta}\n\n{lesson.get('content_md') or ''}\n\n{_choice_markdown(choices)}",
    }


def _options(question: dict) -> list[str]:
    value = question.get("options") or []
    return json.loads(value) if isinstance(value, str) else list(value)


def _quiz_questions(conn, context: dict, lang: str) -> list[dict]:
    questions = db.get_quiz_questions(conn, int(context["quiz_id"]), lang=lang)
    selected = {int(value) for value in context.get("question_ids", [])}
    return [question for question in questions if question["id"] in selected] if selected else questions


def _quiz_question(conn, context: dict, lang: str, lead: str = "") -> dict:
    questions = _quiz_questions(conn, context, lang)
    index = int(context.get("quiz_index", 0))
    if index >= len(questions):
        return _finish_quiz(conn, context, lang)
    question = questions[index]
    choices = _choices((option, option) for option in _options(question))
    context.update({"phase": "quiz", "choices": choices, "question_id": question["id"]})
    prefix = f"{lead}\n\n" if lead else ""
    return {
        "title": context.get("title") or "Quiz", "context": context,
        "lesson_id": context.get("lesson_id"),
        "content": f"{prefix}### {index + 1}. {question['question_text']}\n\n{_choice_markdown(choices)}",
    }


def _start_quiz(conn, user_id: int, quiz_id: int, lang: str) -> dict:
    quiz = conn.execute(sa.text(f"SELECT * FROM {db.S}.quizzes WHERE id = :id"), {"id": quiz_id}).mappings().first()
    if not quiz:
        return _course_picker(conn, lang)
    lesson = db.get_lesson(conn, quiz["lesson_id"], lang=lang)
    course = _course_for_lesson(conn, quiz["lesson_id"], lang)
    learner_level = conn.execute(sa.text(f"""
        SELECT CASE WHEN cls.strategy = 'adaptive' THEN COALESCE(lcs.difficulty_level, 2) ELSE 2 END
        FROM {db.S}.quizzes q JOIN {db.S}.lessons l ON l.id=q.lesson_id
        JOIN {db.S}.modules m ON m.id=l.module_id
        LEFT JOIN {db.S}.course_learning_settings cls ON cls.course_id=m.course_id
        LEFT JOIN {db.S}.learner_course_state lcs ON lcs.course_id=m.course_id AND lcs.user_id=:user
        WHERE q.id=:quiz
    """), {"user": user_id, "quiz": quiz_id}).scalar() or 2
    questions = db.get_quiz_questions(conn, quiz_id, lang=lang, learner_level=learner_level)
    context = {
        "phase": "quiz", "course_id": course["id"] if course else None,
        "lesson_id": quiz["lesson_id"], "quiz_id": quiz_id, "quiz_index": 0,
        "quiz_correct": 0, "quiz_answers": {}, "title": quiz.get("title") or "Quiz",
        "question_ids": [question["id"] for question in questions],
    }
    result = _quiz_question(conn, context, lang)
    result["title"] = quiz.get("title") or (lesson["title"] if lesson else "Quiz")
    return result


def _finish_quiz(conn, context: dict, lang: str, user_id: int | None = None) -> dict:
    total = int(context.get("quiz_index", 0))
    correct = int(context.get("quiz_correct", 0))
    score = round(correct / total * 100) if total else 0
    if user_id is not None:
        quiz = conn.execute(sa.text(f"SELECT * FROM {db.S}.quizzes WHERE id = :id"), {"id": context["quiz_id"]}).mappings().first()
        passed = bool(quiz and score >= quiz["pass_threshold"])
        conn.execute(sa.text(f"""
            INSERT INTO {db.S}.quiz_attempts (user_id, quiz_id, score, passed, answers, completed_at)
            VALUES (:user, :quiz, :score, :passed, CAST(:answers AS jsonb), now())
        """), {"user": user_id, "quiz": context["quiz_id"], "score": score,
                 "passed": passed, "answers": json.dumps(context.get("quiz_answers", {}))})
        db.update_adaptive_state(conn, user_id=user_id, quiz_id=int(context["quiz_id"]), score=score)
        if passed:
            conn.execute(sa.text(f"UPDATE {db.S}.users SET xp = xp + :xp WHERE id = :user"),
                         {"xp": quiz["xp_reward"], "user": user_id})
            db._update_streak(conn, user_id)
            db._update_level(conn, user_id)
            db.check_and_award_badges(conn, user_id)
    choices = _choices([
        (_copy(lang)["lessons"], "lessons"), (_copy(lang)["courses"], "courses")
    ])
    context.update({"phase": "quiz_done", "choices": choices})
    return {
        "title": context.get("title") or "Quiz", "context": context,
        "lesson_id": context.get("lesson_id"),
        "content": f"{_copy(lang)['score'].format(score=score, correct=correct, total=total)}\n\n{_choice_markdown(choices)}",
    }


def _language_picker(lang: str) -> dict:
    choices = _choices((languages.language_label(code), code) for code in languages.NATIVE_LANGUAGE_CODES)
    return {
        "title": "Language learning",
        "context": {"phase": "language_native", "choices": choices},
        "content": f"{_copy(lang)['native']}\n\n{_choice_markdown(choices)}",
    }


def _language_target_picker(native: str, lang: str) -> dict:
    targets = [code for code in languages.TARGET_LANGUAGE_CODES if code != native]
    choices = _choices((languages.language_label(code), code) for code in targets)
    return {
        "title": "Language learning",
        "context": {"phase": "language_target", "native_language": native, "choices": choices},
        "content": f"{_copy(lang)['target']}\n\n{_choice_markdown(choices)}",
    }


def _language_card(conn, user_id: int, context: dict, lang: str, lead: str = "") -> dict:
    reviews = db.get_language_reviews(conn, user_id=user_id, target_language=context["target_language"])
    cards = languages.build_session(
        reviews, native_language=context["native_language"], target_language=context["target_language"], limit=1
    )
    if not cards:
        return _language_picker(lang)
    card = cards[0]
    choices = _choices([(_copy(lang)["reveal"], "reveal"), (_copy(lang)["change"], "change")])
    context.update({"phase": "language_reveal", "concept_id": card["id"], "choices": choices})
    prefix = f"{lead}\n\n" if lead else ""
    return {
        "title": f"Learn {languages.LANGUAGE_META[context['target_language']]['name']}",
        "context": context,
        "content": f"{prefix}## {card['native']['text']}\n\n{_copy(lang)['speak']}\n\n{_choice_markdown(choices)}",
    }


def initial_response(
    conn, user_id: int, lang: str, *, mode: str = "courses", course_slug: str = "",
    lesson_id: int | None = None, quiz_id: int | None = None,
) -> dict:
    if mode == "language":
        return _language_picker(lang)
    if quiz_id:
        return _start_quiz(conn, user_id, quiz_id, lang)
    if lesson_id:
        return _show_lesson(conn, user_id, lesson_id, lang)
    if course_slug:
        course = db.get_course(conn, course_slug, lang=lang)
        if course:
            return _show_course(conn, user_id, course["id"], lang)
    return _course_picker(conn, lang)


def handle_guided_message(conn, user_id: int, context: dict, message: str, lang: str) -> dict | None:
    choice = resolve_choice(message, context.get("choices", []))
    if not choice:
        return None
    phase = context.get("phase")
    value = choice["value"]
    if phase == "course_picker":
        return _show_course(conn, user_id, int(value), lang)
    if phase == "lesson_picker":
        return _show_lesson(conn, user_id, int(value), lang)
    if phase == "lesson":
        if value == "complete":
            progress = db.get_lesson_progress(conn, user_id, int(context["lesson_id"]))
            lead = _copy(lang)["already"] if progress and progress["status"] == "completed" else _copy(lang)["done"].format(
                xp=db.mark_lesson_complete(conn, user_id, int(context["lesson_id"]))
            )
            result = _show_lesson(conn, user_id, int(context["lesson_id"]), lang)
            result["content"] = f"{lead}\n\n{result['content']}"
            return result
        if value == "quiz" and context.get("quiz_id"):
            return _start_quiz(conn, user_id, int(context["quiz_id"]), lang)
        if value == "lessons":
            return _show_course(conn, user_id, int(context["course_id"]), lang)
        if value == "courses":
            return _course_picker(conn, lang)
    if phase == "quiz":
        questions = _quiz_questions(conn, context, lang)
        index = int(context.get("quiz_index", 0))
        if index >= len(questions):
            return _finish_quiz(conn, context, lang, user_id)
        question = questions[index]
        answer = str(value)
        correct = answer == question["correct_answer"]
        context.setdefault("quiz_answers", {})[str(question["id"])] = answer
        context["quiz_correct"] = int(context.get("quiz_correct", 0)) + int(correct)
        context["quiz_index"] = index + 1
        lead = _copy(lang)["correct"] if correct else _copy(lang)["incorrect"].format(answer=question["correct_answer"])
        if question.get("explanation"):
            lead += f" {question['explanation']}"
        if context["quiz_index"] >= len(questions):
            result = _finish_quiz(conn, context, lang, user_id)
            result["content"] = f"{lead}\n\n{result['content']}"
            return result
        return _quiz_question(conn, context, lang, lead)
    if phase == "quiz_done":
        return _show_course(conn, user_id, int(context["course_id"]), lang) if value == "lessons" else _course_picker(conn, lang)
    if phase == "language_native":
        return _language_target_picker(str(value), lang)
    if phase == "language_target":
        profile = db.save_language_profile(
            conn, user_id=user_id, native_language=context["native_language"], target_language=str(value), daily_goal=10
        )
        context.update({"native_language": profile["native_language"], "target_language": profile["target_language"]})
        return _language_card(conn, user_id, context, lang)
    if phase == "language_reveal":
        if value == "change":
            return _language_picker(lang)
        item = next(item for item in languages.frequency_dictionary()["items"] if item["id"] == context["concept_id"])
        target = item["forms"][context["target_language"]]
        choices = _choices([
            (_copy(lang)["again"], "again"), (_copy(lang)["hard"], "hard"), (_copy(lang)["good"], "good")
        ])
        context.update({"phase": "language_rate", "choices": choices})
        romanization = f"\n\n_{target.get('romanization')}_" if target.get("romanization") else ""
        return {"title": f"Learn {languages.LANGUAGE_META[context['target_language']]['name']}", "context": context,
                "content": f"## {target['text']}{romanization}\n\n{_choice_markdown(choices)}"}
    if phase == "language_rate":
        db.record_language_review(
            conn, user_id=user_id, native_language=context["native_language"],
            target_language=context["target_language"], concept_id=context["concept_id"], rating=str(value),
        )
        return _language_card(conn, user_id, context, lang)
    return None
