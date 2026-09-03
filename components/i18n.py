"""English, Estonian, and Lithuanian localisation helpers for FastLearn."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "et", "lt")
LANG_META = {
    "en": {"flag": "🇬🇧", "name": "English"},
    "et": {"flag": "🇪🇪", "name": "Eesti"},
    "lt": {"flag": "🇱🇹", "name": "Lietuvių"},
}
FASTLEARN_HOSTS = {"fastlearn.fun", "www.fastlearn.fun"}


TEXT = {
    # Shared navigation and authentication.
    "overview": {"en": "Overview", "et": "Ülevaade", "lt": "Apžvalga"},
    "open_source": {"en": "Open source", "et": "Avatud lähtekood", "lt": "Atvirasis kodas"},
    "demo": {"en": "Demo", "et": "Demo", "lt": "Demo"},
    "developers": {"en": "Developers", "et": "Arendajatele", "lt": "Kūrėjams"},
    "partners": {"en": "Partners", "et": "Partnerid", "lt": "Partneriai"},
    "sign_in": {"en": "Sign in", "et": "Logi sisse", "lt": "Prisijungti"},
    "sign_out": {"en": "Sign out", "et": "Logi välja", "lt": "Atsijungti"},
    "register": {"en": "Register", "et": "Registreeru", "lt": "Registruotis"},
    "language": {"en": "Language", "et": "Keel", "lt": "Kalba"},
    "view_github": {"en": "View on GitHub", "et": "Vaata GitHubis", "lt": "Peržiūrėti GitHub"},
    "email": {"en": "Email", "et": "E-post", "lt": "El. paštas"},
    "password": {"en": "Password", "et": "Parool", "lt": "Slaptažodis"},
    "forgot_password": {"en": "Forgot password?", "et": "Unustasid parooli?", "lt": "Pamiršote slaptažodį?"},
    "continue_google": {"en": "Continue with Google", "et": "Jätka Google'iga", "lt": "Tęsti su Google"},
    "create_account": {"en": "Create your account", "et": "Loo konto", "lt": "Sukurti paskyrą"},
    "reset_password": {"en": "Reset your password", "et": "Lähtesta parool", "lt": "Atkurti slaptažodį"},

    # Open-source FastLMS landing.
    "oss_eyebrow": {"en": "Open learning infrastructure", "et": "Avatud õppeplatvorm", "lt": "Atvira mokymosi infrastruktūra"},
    "oss_headline": {"en": "Build a learning platform learners actually want to use.", "et": "Loo õppeplatvorm, mida õppijad päriselt kasutada tahavad.", "lt": "Kurkite mokymosi platformą, kuria besimokantieji iš tiesų nori naudotis."},
    "oss_description": {"en": "FastLMS is an open-source foundation for courses, lessons, quizzes, AI tutoring, progress, and school operations.", "et": "FastLMS on avatud lähtekoodiga alus kursuste, tundide, testide, tehisintellekti juhendamise, edenemise ja koolitöö jaoks.", "lt": "FastLMS yra atvirojo kodo pagrindas kursams, pamokoms, testams, DI mokymui, pažangai ir mokyklos veiklai."},
    "explore_demo": {"en": "Explore the FastLearn demo →", "et": "Ava FastLearni demo →", "lt": "Išbandyti FastLearn demo →"},
    "read_source": {"en": "Read the source →", "et": "Vaata lähtekoodi →", "lt": "Peržiūrėti kodą →"},
    "oss_courses_title": {"en": "Courses and assessments", "et": "Kursused ja hindamine", "lt": "Kursai ir vertinimas"},
    "oss_courses_body": {"en": "Structure rich lessons, quizzes, enrolment, progress, and achievements in one focused workspace.", "et": "Koonda sisukad tunnid, testid, registreerumine, edenemine ja saavutused ühte selgesse tööruumi.", "lt": "Valdykite turiningas pamokas, testus, registraciją, pažangą ir pasiekimus vienoje aiškioje erdvėje."},
    "oss_ai_title": {"en": "AI tutoring", "et": "Tehisintellekti juhendaja", "lt": "DI mokytojas"},
    "oss_ai_body": {"en": "Give every learner contextual help grounded in the lesson they are studying.", "et": "Paku igale õppijale abi, mis tugineb parasjagu õpitava tunni sisule.", "lt": "Suteikite kiekvienam besimokančiajam pagalbą, paremtą jo studijuojamos pamokos turiniu."},
    "oss_control_title": {"en": "Deployment control", "et": "Juurutuse kontroll", "lt": "Diegimo kontrolė"},
    "oss_control_body": {"en": "Self-host the FastHTML application, connect PostgreSQL, and adapt the curriculum to your organisation.", "et": "Majuta FastHTMLi rakendus ise, ühenda PostgreSQL ja kohanda õppekava oma organisatsioonile.", "lt": "Savarankiškai talpinkite FastHTML programą, prijunkite PostgreSQL ir pritaikykite mokymo turinį savo organizacijai."},
    "reference_eyebrow": {"en": "Reference implementation", "et": "Näidisrakendus", "lt": "Etaloninis sprendimas"},
    "reference_title": {"en": "See FastLMS running as FastLearn.", "et": "Vaata FastLMS-i FastLearni rakendusena.", "lt": "Pamatykite FastLMS veikiantį kaip FastLearn."},
    "reference_body": {"en": "FastLearn is the production-shaped learning experience built from this repository, with a multilingual catalogue and AI tutor.", "et": "FastLearn on selle hoidla põhjal loodud tootmisvalmis õpikeskkond mitmekeelse kataloogi ja tehisintellekti juhendajaga.", "lt": "FastLearn yra šios saugyklos pagrindu sukurta produkcinė mokymosi aplinka su daugiakalbiu katalogu ir DI mokytoju."},

    # FastLearn product landing.
    "learn_eyebrow": {"en": "Learning that keeps moving", "et": "Õppimine, mis liigub edasi", "lt": "Mokymasis, kuris juda pirmyn"},
    "learn_headline": {"en": "Learn useful skills, one clear step at a time.", "et": "Õpi kasulikke oskusi üks selge samm korraga.", "lt": "Mokykitės naudingų įgūdžių po vieną aiškų žingsnį."},
    "learn_description": {"en": "Explore practical courses across technology, science, language, and creativity—with quizzes, visible progress, and an AI tutor beside you.", "et": "Avasta praktilisi kursusi tehnoloogia, loodusteaduste, keele ja loovuse vallas koos testide, nähtava edenemise ja tehisintellekti juhendajaga.", "lt": "Atraskite praktinius technologijų, gamtos mokslų, kalbų ir kūrybos kursus su testais, matoma pažanga ir DI mokytoju."},
    "start_learning": {"en": "Start learning →", "et": "Alusta õppimist →", "lt": "Pradėti mokytis →"},
    "browse_courses": {"en": "Browse courses →", "et": "Sirvi kursusi →", "lt": "Naršyti kursus →"},
    "metric_courses": {"en": "published courses", "et": "avaldatud kursust", "lt": "paskelbtų kursų"},
    "metric_languages": {"en": "learning languages", "et": "õppekeelt", "lt": "mokymosi kalbos"},
    "metric_subjects": {"en": "subject areas", "et": "ainevaldkonda", "lt": "dalykų sritys"},
    "metric_tutor": {"en": "AI tutor, always ready", "et": "AI-juhendaja on alati valmis", "lt": "DI mokytojas visada pasirengęs"},
    "inside_eyebrow": {"en": "A look inside", "et": "Pilk sisse", "lt": "Žvilgsnis į vidų"},
    "inside_title": {"en": "One place for lessons, practice, and progress.", "et": "Üks koht tundideks, harjutamiseks ja edenemiseks.", "lt": "Viena vieta pamokoms, praktikai ir pažangai."},
    "inside_body": {"en": "Choose a course, learn in focused lessons, check your understanding, and ask for help without losing context.", "et": "Vali kursus, õpi keskendunud tundides, kontrolli teadmisi ja küsi abi ilma konteksti kaotamata.", "lt": "Pasirinkite kursą, mokykitės aiškiose pamokose, pasitikrinkite žinias ir prašykite pagalbos neprarasdami konteksto."},
    "how_eyebrow": {"en": "How it works", "et": "Kuidas see töötab", "lt": "Kaip tai veikia"},
    "how_title": {"en": "From curiosity to confidence in four steps.", "et": "Uudishimust enesekindluseni nelja sammuga.", "lt": "Nuo smalsumo iki pasitikėjimo keturiais žingsniais."},
    "step_1_title": {"en": "Choose your course", "et": "Vali kursus", "lt": "Pasirinkite kursą"},
    "step_1_body": {"en": "Start with programming, science, mathematics, language, geography, or creative writing.", "et": "Alusta programmeerimisest, loodusteadustest, matemaatikast, keelest, geograafiast või loovkirjutamisest.", "lt": "Pradėkite nuo programavimo, gamtos mokslų, matematikos, kalbų, geografijos ar kūrybinio rašymo."},
    "step_2_title": {"en": "Learn in focused lessons", "et": "Õpi keskendunud tundides", "lt": "Mokykitės aiškiose pamokose"},
    "step_2_body": {"en": "Move through concise explanations, examples, and practical material at your own pace.", "et": "Läbi lühikesed selgitused, näited ja praktiline materjal omas tempos.", "lt": "Savo tempu pereikite glaustus paaiškinimus, pavyzdžius ir praktinę medžiagą."},
    "step_3_title": {"en": "Check your understanding", "et": "Kontrolli arusaamist", "lt": "Pasitikrinkite supratimą"},
    "step_3_body": {"en": "Use translated quizzes and immediate feedback to turn reading into durable knowledge.", "et": "Kasuta tõlgitud teste ja kohest tagasisidet, et muuta loetu püsivaks teadmiseks.", "lt": "Naudokite išverstus testus ir greitą grįžtamąjį ryšį, kad skaitymas taptų tvirtomis žiniomis."},
    "step_4_title": {"en": "Ask your AI tutor", "et": "Küsi AI-juhendajalt", "lt": "Klauskite DI mokytojo"},
    "step_4_body": {"en": "Get explanations grounded in the current lesson, in the language you selected.", "et": "Saa valitud keeles selgitusi, mis tuginevad parasjagu õpitavale tunnile.", "lt": "Gaukite pasirinkta kalba paaiškinimus, paremtus dabartine pamoka."},
    "subjects_eyebrow": {"en": "Explore subjects", "et": "Avasta aineid", "lt": "Atraskite dalykus"},
    "subjects_title": {"en": "Build skills across disciplines.", "et": "Arenda oskusi eri valdkondades.", "lt": "Ugdykite įgūdžius įvairiose srityse."},
    "subject_technology": {"en": "Technology", "et": "Tehnoloogia", "lt": "Technologijos"},
    "subject_science": {"en": "Science", "et": "Loodusteadused", "lt": "Gamtos mokslai"},
    "subject_language": {"en": "Language", "et": "Keel", "lt": "Kalbos"},
    "subject_creativity": {"en": "Creativity", "et": "Loovus", "lt": "Kūryba"},
    "subject_technology_body": {"en": "Python, machine learning, and building web applications.", "et": "Python, masinõpe ja veebirakenduste loomine.", "lt": "Python, mašininis mokymasis ir interneto programų kūrimas."},
    "subject_science_body": {"en": "Mathematics, physics, biology, chemistry, and geography.", "et": "Matemaatika, füüsika, bioloogia, keemia ja geograafia.", "lt": "Matematika, fizika, biologija, chemija ir geografija."},
    "subject_language_body": {"en": "English language and literature through practical examples.", "et": "Inglise keel ja kirjandus praktiliste näidete kaudu.", "lt": "Anglų kalba ir literatūra per praktinius pavyzdžius."},
    "subject_creativity_body": {"en": "Creative writing, storytelling, revision, and voice.", "et": "Loovkirjutamine, jutustamine, toimetamine ja isikupärane hääl.", "lt": "Kūrybinis rašymas, pasakojimas, redagavimas ir savitas balsas."},
    "cta_eyebrow": {"en": "Ready when you are", "et": "Alusta, kui oled valmis", "lt": "Pradėkite, kai būsite pasirengę"},
    "cta_title": {"en": "Make your next lesson the one that clicks.", "et": "Tee järgmisest tunnist see, kus kõik paika loksub.", "lt": "Tegul kita pamoka tampa ta, kurioje viskas tampa aišku."},
    "cta_body": {"en": "Create your account, choose a subject, and keep every step of your progress visible.", "et": "Loo konto, vali aine ja hoia iga edusamm nähtaval.", "lt": "Susikurkite paskyrą, pasirinkite dalyką ir matykite kiekvieną savo pažangos žingsnį."},

    # Learning application.
    "dashboard": {"en": "Dashboard", "et": "Töölaud", "lt": "Pagrindinis skydelis"},
    "courses": {"en": "Courses", "et": "Kursused", "lt": "Kursai"},
    "leaderboard": {"en": "Leaderboard", "et": "Edetabel", "lt": "Lyderių lentelė"},
    "manage_courses": {"en": "Manage courses", "et": "Halda kursusi", "lt": "Valdyti kursus"},
    "course_config": {"en": "Course setup", "et": "Kursuse seadistus", "lt": "Kurso nustatymai"},
    "ai_tutor": {"en": "AI Tutor", "et": "AI-juhendaja", "lt": "DI mokytojas"},
    "canvas": {"en": "Canvas", "et": "Tööala", "lt": "Darbo sritis"},
    "welcome_back": {"en": "Welcome back, {name}", "et": "Tere tulemast tagasi, {name}", "lt": "Sveiki sugrįžę, {name}"},
    "learning_dashboard": {"en": "Your learning dashboard", "et": "Sinu õppimise töölaud", "lt": "Jūsų mokymosi skydelis"},
    "total_xp": {"en": "Total XP", "et": "XP kokku", "lt": "Iš viso XP"},
    "level": {"en": "Level", "et": "Tase", "lt": "Lygis"},
    "streak": {"en": "Streak", "et": "Järjestikused päevad", "lt": "Dienų serija"},
    "lessons_done": {"en": "Lessons done", "et": "Tunde tehtud", "lt": "Baigtos pamokos"},
    "my_courses": {"en": "My courses", "et": "Minu kursused", "lt": "Mano kursai"},
    "my_badges": {"en": "My badges", "et": "Minu märgid", "lt": "Mano ženkleliai"},
    "browse_all_courses": {"en": "Browse all available courses", "et": "Sirvi kõiki saadaolevaid kursusi", "lt": "Naršykite visus galimus kursus"},
    "no_courses": {"en": "No courses yet", "et": "Kursusi veel pole", "lt": "Kursų dar nėra"},
    "difficulty": {"en": "Difficulty", "et": "Raskusaste", "lt": "Sudėtingumas"},
    "progress": {"en": "Progress", "et": "Edenemine", "lt": "Pažanga"},
    "beginner": {"en": "Beginner", "et": "Algaja", "lt": "Pradedantiesiems"},
    "intermediate": {"en": "Intermediate", "et": "Kesktase", "lt": "Vidutinis"},
    "advanced": {"en": "Advanced", "et": "Edasijõudnud", "lt": "Pažengusiems"},
    "enrol": {"en": "Enrol", "et": "Registreeru", "lt": "Registruotis"},
    "lessons": {"en": "lessons", "et": "tundi", "lt": "pamokos"},
    "select_lesson": {"en": "Select a lesson from the sidebar to begin.", "et": "Alustamiseks vali külgribalt tund.", "lt": "Norėdami pradėti, pasirinkite pamoką šoninėje juostoje."},
    "mark_complete": {"en": "Mark complete", "et": "Märgi lõpetatuks", "lt": "Pažymėti baigta"},
    "completed": {"en": "Completed", "et": "Lõpetatud", "lt": "Baigta"},
    "take_quiz": {"en": "Take quiz", "et": "Tee test", "lt": "Atlikti testą"},
    "next_lesson": {"en": "Next lesson", "et": "Järgmine tund", "lt": "Kita pamoka"},
    "question": {"en": "Question {number}", "et": "Küsimus {number}", "lt": "Klausimas {number}"},
    "back_to_lesson": {"en": "← Back to lesson", "et": "← Tagasi tundi", "lt": "← Grįžti į pamoką"},
    "pass_threshold": {"en": "Pass threshold: {threshold}% • +{xp} XP on pass", "et": "Lävend: {threshold}% • edukal sooritusel +{xp} XP", "lt": "Išlaikymo riba: {threshold}% • išlaikius +{xp} XP"},
    "submit_quiz": {"en": "Submit quiz", "et": "Esita test", "lt": "Pateikti testą"},
    "your_answer": {"en": "Your answer: {answer}", "et": "Sinu vastus: {answer}", "lt": "Jūsų atsakymas: {answer}"},
    "correct_answer": {"en": "Correct answer: {answer}", "et": "Õige vastus: {answer}", "lt": "Teisingas atsakymas: {answer}"},
    "passed": {"en": "Passed!", "et": "Sooritatud!", "lt": "Išlaikyta!"},
    "not_passed": {"en": "Not passed", "et": "Ei sooritanud", "lt": "Neišlaikyta"},
    "retry": {"en": "Retry", "et": "Proovi uuesti", "lt": "Bandyti dar kartą"},
    "ask_placeholder": {"en": "Ask anything about the lesson…", "et": "Küsi tunni kohta…", "lt": "Klauskite apie pamoką…"},
    "send": {"en": "Send", "et": "Saada", "lt": "Siųsti"},
    "thinking": {"en": "Thinking…", "et": "Mõtlen…", "lt": "Galvoju…"},
    "connection_error": {"en": "Connection error. Please try again.", "et": "Ühenduse viga. Proovi uuesti.", "lt": "Ryšio klaida. Bandykite dar kartą."},
    "prompt_explain": {"en": "Explain the key idea in simpler terms", "et": "Selgita põhiideed lihtsamalt", "lt": "Paaiškink pagrindinę mintį paprasčiau"},
    "prompt_example": {"en": "Give me a practical example", "et": "Too praktiline näide", "lt": "Pateik praktinį pavyzdį"},
    "prompt_quiz": {"en": "Quiz me on this lesson", "et": "Küsi minult selle tunni kohta", "lt": "Patikrink mane iš šios pamokos"},
    "top_learners": {"en": "Top learners ranked by XP", "et": "Parimad õppijad XP järgi", "lt": "Geriausi besimokantieji pagal XP"},
    "assigned": {"en": "Assigned", "et": "Määratud", "lt": "Priskirta"},
    "team": {"en": "Team", "et": "Meeskond", "lt": "Komanda"},
    "reports": {"en": "Reports", "et": "Aruanded", "lt": "Ataskaitos"},
    "team_title": {"en": "Team and learners", "et": "Meeskond ja õppijad", "lt": "Komanda ir besimokantieji"},
    "team_subtitle": {"en": "Invite people, manage roles, and assign courses.", "et": "Kutsu inimesi, halda rolle ja määra kursusi.", "lt": "Kvieskite žmones, valdykite vaidmenis ir priskirkite kursus."},
    "invite_person": {"en": "Invite a person", "et": "Kutsu inimene", "lt": "Pakviesti asmenį"},
    "invite": {"en": "Send invitation", "et": "Saada kutse", "lt": "Siųsti kvietimą"},
    "role": {"en": "Role", "et": "Roll", "lt": "Vaidmuo"},
    "student": {"en": "Student", "et": "Õppija", "lt": "Studentas"},
    "teacher": {"en": "Teacher", "et": "Õpetaja", "lt": "Mokytojas"},
    "admin": {"en": "Administrator", "et": "Administraator", "lt": "Administratorius"},
    "people": {"en": "People", "et": "Inimesed", "lt": "Žmonės"},
    "course_assignments": {"en": "Course assignments", "et": "Kursuste määramised", "lt": "Kursų priskyrimai"},
    "assign_course": {"en": "Assign course", "et": "Määra kursus", "lt": "Priskirti kursą"},
    "remove": {"en": "Remove", "et": "Eemalda", "lt": "Pašalinti"},
    "pending_invitations": {"en": "Pending invitations", "et": "Ootel kutsed", "lt": "Laukiantys kvietimai"},
    "revoke": {"en": "Revoke", "et": "Tühista", "lt": "Atšaukti"},
    "learning_reports": {"en": "Learning reports", "et": "Õppimise aruanded", "lt": "Mokymosi ataskaitos"},
    "time_spent": {"en": "Active time", "et": "Aktiivne aeg", "lt": "Aktyvus laikas"},
    "lesson_time": {"en": "Lessons", "et": "Tunnid", "lt": "Pamokos"},
    "quiz_time": {"en": "Quizzes", "et": "Testid", "lt": "Testai"},
    "tutor_time": {"en": "AI Tutor", "et": "AI-juhendaja", "lt": "DI mokytojas"},
    "learning_strategy": {"en": "Learning strategy", "et": "Õppimisstrateegia", "lt": "Mokymosi strategija"},
    "linear": {"en": "Linear", "et": "Lineaarne", "lt": "Linijinė"},
    "adaptive": {"en": "Adaptive", "et": "Kohanduv", "lt": "Adaptyvi"},
    "strategy_help": {"en": "Linear keeps the authored order. Adaptive can reorder support and extension material after assessments.", "et": "Lineaarne säilitab autori järjekorra. Kohanduv võib pärast hindamist tugi- ja süvamaterjali ümber järjestada.", "lt": "Linijinė išlaiko autoriaus tvarką. Adaptyvi po vertinimų gali pertvarkyti pagalbinę ir išplėstinę medžiagą."},
    "save_settings": {"en": "Save settings", "et": "Salvesta seaded", "lt": "Išsaugoti nustatymus"},
    "content_drafts": {"en": "Generated drafts for approval", "et": "Loodud mustandid kinnitamiseks", "lt": "Sugeneruoti juodraščiai patvirtinimui"},
    "approve": {"en": "Approve and publish", "et": "Kinnita ja avalda", "lt": "Patvirtinti ir paskelbti"},
    "reject": {"en": "Reject", "et": "Lükka tagasi", "lt": "Atmesti"},
    "recommended_review": {"en": "Recommended review", "et": "Soovitatud kordamine", "lt": "Rekomenduojamas kartojimas"},
    "ready_extension": {"en": "You are ready for an extension", "et": "Oled valmis süvaülesandeks", "lt": "Esate pasirengę išplėstinei užduočiai"},
    "optional": {"en": "Optional", "et": "Valikuline", "lt": "Pasirenkama"},
    "remedial": {"en": "Support", "et": "Tugi", "lt": "Pagalba"},
    "core": {"en": "Core", "et": "Põhiosa", "lt": "Pagrindinė"},
    "question_variant": {"en": "Question variant", "et": "Küsimuse variant", "lt": "Klausimo variantas"},
}


def t(key: str, lang: str = DEFAULT_LANG, **values) -> str:
    choices = TEXT.get(key)
    value = choices.get(lang, choices[DEFAULT_LANG]) if choices else key
    return value.format(**values) if values else value


def request_host(request) -> str:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    return host.split(",", 1)[0].split(":", 1)[0].lower()


def is_fastlearn_host(request) -> bool:
    return request_host(request) in FASTLEARN_HOSTS


def site_name(request) -> str:
    return "FastLearn" if is_fastlearn_host(request) else "FastLMS"


def _accepted_languages(header: str):
    ranked = []
    for item in (header or "").split(","):
        token, _, quality = item.strip().partition(";q=")
        code = token.split("-", 1)[0].lower()
        try:
            weight = float(quality) if quality else 1.0
        except ValueError:
            weight = 0.0
        ranked.append((weight, code))
    return [code for _, code in sorted(ranked, reverse=True)]


def get_lang(request) -> str:
    try:
        saved = request.session.get("lang")
    except Exception:
        saved = None
    saved = saved or request.cookies.get("language")
    if saved in SUPPORTED_LANGS:
        return saved
    return next((code for code in _accepted_languages(request.headers.get("accept-language", "")) if code in SUPPORTED_LANGS), DEFAULT_LANG)


def safe_return_path(value: str | None) -> str:
    value = value or "/"
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return "/"
    return value


@lru_cache(maxsize=1)
def course_catalog() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "course_translations.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def localize_record(record: dict | None, entity: str, lang: str) -> dict | None:
    """Overlay checked-in catalogue translations while retaining stable IDs."""
    if not record or lang == DEFAULT_LANG:
        return record
    row = dict(record)
    entry = course_catalog().get(entity, {}).get(str(row.get("id")), {})
    source = entry.get("source")
    source_field = "question_text" if entity == "quiz_questions" else "title"
    if source and row.get(source_field) != source:
        return row
    row.update(entry.get(lang, {}))
    return row


def prompt_language_directive(lang: str) -> str:
    return {
        "en": "Respond in English unless the learner explicitly asks for another language.",
        "et": "Vasta eesti keeles, kui õppija ei palu selgelt kasutada teist keelt.",
        "lt": "Atsakyk lietuvių kalba, nebent besimokantysis aiškiai paprašo kitos kalbos.",
    }.get(lang, "Respond in English.")
