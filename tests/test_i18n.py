"""Multilingual catalogue and host-branding regressions."""

from types import SimpleNamespace

from components.i18n import (
    SUPPORTED_LANGS,
    course_catalog,
    get_lang,
    is_fastlearn_host,
    localize_record,
    safe_return_path,
    t,
)


def _request(*, host="lms.fastsme.com", language="", cookie=None, session=None):
    return SimpleNamespace(
        headers={"host": host, "accept-language": language},
        cookies={"language": cookie} if cookie else {},
        session=session or {},
    )


def test_supported_languages_and_negotiation():
    assert SUPPORTED_LANGS == ("en", "et", "lt", "es")
    assert get_lang(_request(language="lt-LT,et;q=0.8,en;q=0.5")) == "lt"
    assert get_lang(_request(language="es-ES,en;q=0.5")) == "es"
    assert get_lang(_request(language="en", cookie="et")) == "et"
    assert get_lang(_request(language="en", session={"lang": "lt"})) == "lt"


def test_fastlearn_host_dispatch_is_exact():
    assert is_fastlearn_host(_request(host="fastlearn.fun"))
    assert is_fastlearn_host(_request(host="www.fastlearn.fun"))
    assert not is_fastlearn_host(_request(host="lms.fastsme.com"))


def test_return_path_rejects_external_redirects():
    assert safe_return_path("/app/courses?x=1") == "/app/courses?x=1"
    for unsafe in ("https://example.com", "//example.com", "/\\example.com"):
        assert safe_return_path(unsafe) == "/"


def test_every_catalogue_record_has_all_demo_languages():
    expected = {"courses": 14, "modules": 21, "lessons": 32, "quizzes": 13, "quiz_questions": 29}
    catalog = course_catalog()
    assert {entity: len(rows) for entity, rows in catalog.items()} == expected
    for rows in catalog.values():
        assert all(entry.get("et") and entry.get("lt") and entry.get("es") for entry in rows.values())


def test_localization_requires_matching_source_record():
    english = {"id": 1, "title": "Python Fundamentals", "slug": "python-fundamentals"}
    assert localize_record(english, "courses", "et")["title"] == "Pythoni põhialused"
    assert localize_record(english, "courses", "lt")["title"] == "Python pagrindai"
    assert localize_record(english, "courses", "es")["title"] == "Fundamentos de Python"
    unrelated = {"id": 1, "title": "A newly created course"}
    assert localize_record(unrelated, "courses", "et")["title"] == unrelated["title"]


def test_translated_quiz_answers_are_present_in_options():
    for entry in course_catalog()["quiz_questions"].values():
        for lang in ("et", "lt", "es"):
            assert entry[lang]["correct_answer"] in entry[lang]["options"]


def test_primary_landing_copy_is_translated():
    for key in ("oss_headline", "learn_headline", "learn_description", "start_learning"):
        assert t(key, "en") != t(key, "et")
        assert t(key, "en") != t(key, "lt")
        assert t(key, "en") != t(key, "es")


def test_every_interface_string_has_spanish_copy():
    from components.i18n import TEXT

    assert all(values.get("es") for values in TEXT.values())
