"""Host-aware FastLMS open-source and FastLearn product landing pages."""

from __future__ import annotations

from urllib.parse import quote, urlencode

from fasthtml.common import *

from app_version import APP_VERSION
from .account_auth import AUTH_CSS, AUTH_JS, auth_modal
from .i18n import LANG_META, SUPPORTED_LANGS, t
from .seo import seo_meta


FASTLEARN_URL = "https://fastlearn.fun/"
REPOSITORY_URL = "https://github.com/predictivelabsai/FastLMS"
ACCENT = "#256b62"
TINT = "#f1f8f6"
FAVICON = "data:image/svg+xml," + quote(
    """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="9" fill="#256b62"/><path fill="white" d="M8 8h16v5H14v3h8v5h-8v5H8Z"/><circle cx="24" cy="8" r="4" fill="#f2c94c"/></svg>""",
    safe="",
)

PARTNERS = (
    ("SAASPASS", "https://saaspass.com/", "https://saaspass.com/_next/static/assets/0176aeff921f6359fee88e796be31ace.png", "Identity and access management for secure learning environments."),
    ("Sixty Four", "https://sixtyfour.ee/", "https://sixtyfour.ee/favicon.ico", "Software delivery, service design, and education technology expertise."),
    ("EDI Labs", "https://edilabs.tech/", "https://edilabs.tech/static/favicon.svg", "AI and data engineering for learning and knowledge systems."),
    ("Predictive Labs", "https://predictivelabs.ai/", "https://predictivelabs.ai/static/favicon.svg", "Auditable AI systems and applied machine learning."),
    ("Consistente", "https://consistente.tech/", "https://consistente.tech/static/favicon.svg", "Enterprise AI delivery across regulated industries."),
    ("Manmouna Technologies", "https://manmouna.tech/", "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230B1E14'/%3E%3Cpath d='M32 12 52 32 32 52 12 32Z' fill='%2334D399'/%3E%3Cpath d='M32 22 42 32 32 42 22 32Z' fill='%230B1E14'/%3E%3C/svg%3E", "Auditable AI systems for public services and education."),
)


CSS = """
:root{--accent:#256b62;--accent-strong:#174f49;--tint:#f1f8f6;--sun:#f2c94c;--ink:#172321;--muted:#62716e;--line:#dce8e5;--paper:#fbfdfc}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}
a{color:inherit}.site-nav{height:70px;display:flex;align-items:center;justify-content:space-between;max-width:1200px;margin:auto;padding:0 26px;border-bottom:1px solid var(--line);background:rgba(251,253,252,.94);position:relative;z-index:20}
.site-brand{display:flex;align-items:center;gap:10px;font-weight:780;text-decoration:none;letter-spacing:-.02em}.site-mark{width:32px;height:32px;border-radius:10px;background:var(--accent);display:grid;place-items:center;color:#fff;font-weight:850;box-shadow:inset -7px -7px 0 rgba(0,0,0,.05)}
.nav-actions{display:flex;align-items:center;gap:17px}.nav-link{color:var(--muted);font-size:14px;font-weight:650;text-decoration:none}.nav-link:hover{color:var(--accent)}
.lang{position:relative}.lang summary{list-style:none;cursor:pointer;padding:7px 9px;border:1px solid transparent;border-radius:9px}.lang summary::-webkit-details-marker{display:none}.lang[open] summary,.lang summary:hover{border-color:var(--line);background:#fff}.lang-menu{position:absolute;right:0;top:40px;z-index:50;min-width:155px;padding:6px;background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 18px 48px rgba(23,35,33,.14)}.lang-menu a{display:flex;gap:9px;padding:8px 10px;color:var(--muted);font-size:12px;text-decoration:none;border-radius:8px}.lang-menu a:hover,.lang-menu a.active{background:var(--tint);color:var(--ink)}
.button{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:11px 18px;text-decoration:none;font-weight:700;font-size:14px;border:0;cursor:pointer}.button.primary{background:var(--accent);color:#fff}.button.primary:hover{background:var(--accent-strong)}.button.secondary{border:1px solid var(--line);background:#fff;color:var(--ink)}
.hero{max-width:1200px;margin:auto;padding:104px 26px 76px;position:relative}.hero:after{content:"";position:absolute;right:4%;top:46px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,var(--sun) 0 4%,transparent 5%),linear-gradient(145deg,var(--tint),transparent);opacity:.55;z-index:-1}.eyebrow{color:var(--accent);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.17em}.hero h1{font-size:clamp(45px,7.2vw,82px);line-height:1.01;letter-spacing:-.058em;max-width:980px;margin:22px 0}.lede{font-size:20px;line-height:1.68;color:var(--muted);max-width:780px}.actions{display:flex;gap:12px;margin-top:33px;flex-wrap:wrap}
.metrics{max-width:1200px;margin:0 auto 78px;padding:0 26px;display:grid;grid-template-columns:repeat(4,1fr)}.metric{padding:23px 24px;background:#fff;border:1px solid var(--line);border-right:0}.metric:first-child{border-radius:18px 0 0 18px}.metric:last-child{border-right:1px solid var(--line);border-radius:0 18px 18px 0}.metric strong{display:block;color:var(--accent);font-size:27px;letter-spacing:-.04em}.metric span{display:block;color:var(--muted);font-size:13px;margin-top:5px}
.preview{background:var(--tint);border-block:1px solid var(--line)}.section{max-width:1200px;margin:auto;padding:82px 26px}.section-head{max-width:780px}.section h2{font-size:clamp(32px,4.2vw,52px);letter-spacing:-.045em;line-height:1.08;margin:15px 0}.section-lede{color:var(--muted);font-size:17px;line-height:1.65;max-width:720px}.demo-frame{max-width:1030px;margin:38px auto 0;padding:9px;background:#fff;border:1px solid var(--line);border-radius:22px;box-shadow:0 25px 70px rgba(37,107,98,.12)}.demo-frame img{display:block;width:100%;height:auto;border-radius:15px;background:#fff}.demo-frame p{text-align:center;color:var(--muted);font-size:12px;margin:12px 4px 3px}
.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:15px;margin-top:38px}.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:25px}.card-num{font-size:12px;font-weight:800;color:var(--accent)}.card-icon{font-size:25px}.card h3{font-size:19px;margin:22px 0 9px}.card p{color:var(--muted);font-size:14px;line-height:1.6;margin:0}
.oss-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:38px}.oss-card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:28px}.oss-card h2,.oss-card h3{font-size:21px;margin:20px 0 9px}.oss-card p{color:var(--muted);line-height:1.63;margin:0}.split{display:grid;grid-template-columns:1fr 1fr;gap:65px;align-items:start}.reference{border:1px solid var(--line);border-radius:25px;background:linear-gradient(135deg,var(--tint),#fff);padding:42px}
.partner-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:32px}.partner{color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:18px;padding:20px;background:#fff}.partner-top{display:flex;justify-content:space-between;align-items:center}.partner img{width:42px;height:42px;object-fit:contain}.partner small{color:var(--accent);font-weight:750}.partner h3{font-size:17px;margin:17px 0 8px}.partner p{font-size:13px;color:var(--muted);line-height:1.55;margin:0}
.cta{max-width:1148px;margin:0 auto 78px;padding:56px;border-radius:28px;background:var(--accent);color:#fff;display:grid;grid-template-columns:1fr auto;align-items:end;gap:30px}.cta .eyebrow{color:#cce8e3}.cta h2{font-size:clamp(31px,4vw,50px);letter-spacing:-.045em;line-height:1.08;margin:13px 0}.cta p{color:#dcefeb;max-width:700px;line-height:1.6}.cta .button{background:#fff;color:var(--accent)}
.footer{max-width:1200px;margin:auto;padding:28px 26px 46px;border-top:1px solid var(--line);display:flex;justify-content:space-between;gap:20px;color:var(--muted);font-size:13px}.footer-links{display:flex;gap:18px}.footer a{color:var(--accent);text-decoration:none}.site-version{margin-left:8px;color:#9aa7a4;font-size:10px;font-weight:500}
@media(max-width:820px){.nav-actions{gap:9px}.nav-link.optional,.nav-actions>.secondary{display:none}.hero{padding-top:74px}.metrics,.card-grid,.oss-grid,.partner-grid,.split{grid-template-columns:1fr}.metric{border-right:1px solid var(--line);border-bottom:0}.metric:first-child{border-radius:18px 18px 0 0}.metric:last-child{border-bottom:1px solid var(--line);border-radius:0 0 18px 18px}.cta{margin-inline:16px;padding:34px;grid-template-columns:1fr}.footer{flex-direction:column}.footer-links{flex-wrap:wrap}}
"""


def _language_switcher(lang: str, current_path: str):
    current = LANG_META.get(lang, LANG_META["en"])
    return Details(
        Summary(current["flag"], aria_label=t("language", lang)),
        Div(*[
            A(Span(meta["flag"]), Span(meta["name"]), href=f"/set-lang?{urlencode({'lang': code, 'next': current_path})}",
              lang=code, cls="active" if code == lang else "")
            for code in SUPPORTED_LANGS for meta in (LANG_META[code],)
        ], cls="lang-menu"), cls="lang",
    )


def _head(*, lang: str, product: bool):
    if product:
        title, description = "FastLearn · Learn useful skills with an AI tutor", t("learn_description", lang)
        base_url, product_name = FASTLEARN_URL.rstrip("/"), "FastLearn"
    else:
        title, description = "FastLMS · Open-source learning platform", t("oss_description", lang)
        base_url, product_name = "https://lms.fastsme.com", "FastLMS"
    return Head(
        Title(title), Meta(charset="utf-8"), Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(name="description", content=description),
        *seo_meta(base_url=base_url, product=product_name, title=title, description=description),
        Link(rel="icon", type="image/svg+xml", href=FAVICON), Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"),
        Style(CSS + AUTH_CSS),
    )


def _nav(*, brand: str, lang: str, product: bool):
    if product:
        links = (A(t("overview", lang), href="#overview", cls="nav-link optional"), A(t("courses", lang), href="#subjects", cls="nav-link optional"),
                 _language_switcher(lang, "/"), A(t("sign_in", lang).title(), href="/auth/login", cls="button primary"))
    else:
        links = (A(t("overview", lang), href="#overview", cls="nav-link optional"), A(t("open_source", lang), href="#open-source", cls="nav-link optional"),
                 A(t("demo", lang), href=FASTLEARN_URL, cls="nav-link"), _language_switcher(lang, "/"),
                 A(t("view_github", lang), href=REPOSITORY_URL, target="_blank", rel="noopener noreferrer", cls="button secondary"),
                 Button(t("sign_in", lang).title(), type="button", onclick="authOpen('login')", cls="button primary"))
    return Nav(A(Span("F", cls="site-mark"), Span(brand), href="/", cls="site-brand"), Div(*links, cls="nav-actions"), cls="site-nav")


def fastlms_landing(lang: str = "en"):
    cards = (("01", "oss_courses_title", "oss_courses_body"), ("02", "oss_ai_title", "oss_ai_body"), ("03", "oss_control_title", "oss_control_body"))
    return Html(
        _head(lang=lang, product=False),
        Body(
            _nav(brand="FastLMS", lang=lang, product=False),
            Main(
                Section(Span(t("oss_eyebrow", lang), cls="eyebrow"), H1(t("oss_headline", lang)), P(t("oss_description", lang), cls="lede"),
                        Div(A(t("explore_demo", lang), href=FASTLEARN_URL, cls="button primary"), A(t("read_source", lang), href=REPOSITORY_URL, cls="button secondary"), cls="actions"),
                        id="overview", cls="hero"),
                Section(Div(Img(src="/static/fastlms-demo.gif", alt="FastLMS multilingual product tour", loading="eager", width="1200", height="750"),
                            P(t("inside_body", lang)), cls="demo-frame"), cls="section preview"),
                Section(Span(t("open_source", lang), cls="eyebrow"),
                        Div(*[Article(Span(number, cls="card-num"), H2(t(title, lang)), P(t(body, lang)), cls="oss-card") for number, title, body in cards], cls="oss-grid"),
                        id="open-source", cls="section"),
                Section(
                    Div(Span(t("reference_eyebrow", lang), cls="eyebrow"), H2(t("reference_title", lang)), P(t("reference_body", lang), cls="section-lede"),
                        Div(A(t("explore_demo", lang), href=FASTLEARN_URL, cls="button primary"), cls="actions"), cls="reference"),
                    Div(Span(t("partners", lang), cls="eyebrow"),
                        Div(*[A(Div(Img(src=logo, alt=f"{name} logo", loading="lazy"), Small(t("partners", lang)), cls="partner-top"), H3(name), P(description),
                                href=url, target="_blank", rel="noopener noreferrer", cls="partner") for name, url, logo, description in PARTNERS], cls="partner-grid")),
                    cls="section split"),
            ),
            Footer(Div(Span("FastLMS · FastSME"), Span(f"v{APP_VERSION}", cls="site-version")), Div(A(t("demo", lang), href=FASTLEARN_URL), A(t("developers", lang), href="/developers"), A(t("view_github", lang), href=REPOSITORY_URL), cls="footer-links"), cls="footer"),
            auth_modal("FastLMS", lang), Script(AUTH_JS),
        ), lang=lang,
    )


def fastlearn_landing(lang: str = "en"):
    steps = (("01", "step_1_title", "step_1_body"), ("02", "step_2_title", "step_2_body"), ("03", "step_3_title", "step_3_body"), ("04", "step_4_title", "step_4_body"))
    subjects = (("💻", "subject_technology", "subject_technology_body"), ("🧪", "subject_science", "subject_science_body"),
                ("📚", "subject_language", "subject_language_body"), ("✍️", "subject_creativity", "subject_creativity_body"),
                ("♞", "subject_chess", "subject_chess_body"))
    return Html(
        _head(lang=lang, product=True),
        Body(
            _nav(brand="FastLearn", lang=lang, product=True),
            Main(
                Section(Span(t("learn_eyebrow", lang), cls="eyebrow"), H1(t("learn_headline", lang)), P(t("learn_description", lang), cls="lede"),
                        Div(A(t("start_learning", lang), href="/auth/login", cls="button primary"), A(t("browse_courses", lang), href="#subjects", cls="button secondary"), cls="actions"),
                        id="overview", cls="hero"),
                Section(Div(Strong("15"), Span(t("metric_courses", lang)), cls="metric"), Div(Strong("10"), Span(t("metric_languages", lang)), cls="metric"),
                        Div(Strong("10"), Span(t("metric_subjects", lang)), cls="metric"), Div(Strong("24/7"), Span(t("metric_tutor", lang)), cls="metric"), cls="metrics"),
                Section(Div(Span(t("inside_eyebrow", lang), cls="eyebrow"), H2(t("inside_title", lang)), P(t("inside_body", lang), cls="section-lede"), cls="section-head"),
                        Div(Img(src="/static/fastlearn-demo.gif", alt="FastLearn product tour", loading="eager", width="1200", height="750"), cls="demo-frame"), cls="section preview"),
                Section(Div(Span(t("how_eyebrow", lang), cls="eyebrow"), H2(t("how_title", lang)), cls="section-head"),
                        Div(*[Article(Span(number, cls="card-num"), H3(t(title, lang)), P(t(body, lang)), cls="card") for number, title, body in steps], cls="card-grid"), cls="section"),
                Section(Div(Span(t("subjects_eyebrow", lang), cls="eyebrow"), H2(t("subjects_title", lang)), cls="section-head"),
                        Div(*[Article(Span(icon, cls="card-icon"), H3(t(title, lang)), P(t(body, lang)), cls="card") for icon, title, body in subjects], cls="card-grid"), id="subjects", cls="section preview"),
                Section(Div(Span(t("cta_eyebrow", lang), cls="eyebrow"), H2(t("cta_title", lang)), P(t("cta_body", lang))),
                        A(t("start_learning", lang), href="/auth/login", cls="button"), cls="cta"),
            ),
            Footer(Div(Span("© 2026 FastLearn"), Span(f"v{APP_VERSION}", cls="site-version")), Div(A("FastLMS", href="https://lms.fastsme.com"), A(t("language", lang), href="#overview"), cls="footer-links"), cls="footer"),
            auth_modal("FastLearn", lang), Script(AUTH_JS),
        ), lang=lang,
    )


def landing_page(lang: str = "en", *, product: bool = False):
    return fastlearn_landing(lang) if product else fastlms_landing(lang)
