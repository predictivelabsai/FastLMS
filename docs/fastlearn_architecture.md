# FastLearn technical architecture

## Contents

1. [Scope](#scope)
2. [System map](#system-map)
3. [Two learning modes](#two-learning-modes)
4. [Science and chemistry catalogue](#science-and-chemistry-catalogue)
5. [Country, grade and curriculum profiles](#country-grade-and-curriculum-profiles)
6. [Estonia Grade 8 chemistry reference course](#estonia-grade-8-chemistry-reference-course)
7. [Fixed question pipeline](#fixed-question-pipeline)
8. [AI-assisted question pipeline](#ai-assisted-question-pipeline)
9. [Question selection and fallback](#question-selection-and-fallback)
10. [Answer feedback](#answer-feedback)
11. [Database model](#database-model)
12. [Web routes and public API](#web-routes-and-public-api)
13. [Mobile architecture](#mobile-architecture)
14. [Security and answer privacy](#security-and-answer-privacy)
15. [Model and runtime configuration](#model-and-runtime-configuration)
16. [Verification and evaluation](#verification-and-evaluation)
17. [Known gaps](#known-gaps)

## Scope

This document describes the implementation of FastLearn's student learning
system. It covers the Chat and Classic lesson modes, science curriculum
seeding, deterministic and AI-assisted questions, teacher approval, answer
feedback, persistence, public APIs and the Flutter client.

The educational rationale and exam-specific methodology remain in
[`exam_prep_methodology.md`](exam_prep_methodology.md). Content coverage and
remaining work are tracked in [`quiz_roadmap.md`](quiz_roadmap.md).

## System map

```text
                         ┌───────────────────────────┐
                         │ PostgreSQL / fastlms      │
                         │ curriculum, questions,    │
                         │ drafts, attempts, threads │
                         └─────────────┬─────────────┘
                                       │
              ┌────────────────────────┴──────────────────────┐
              │                                               │
    ┌─────────▼──────────┐                          ┌─────────▼──────────┐
    │ FastHTML web app   │                          │ FastAPI /api/v1    │
    │ Chat + Classic UI  │                          │ answer-safe reads  │
    │ teacher approvals  │                          │ grading endpoints  │
    └─────────┬──────────┘                          └─────────┬──────────┘
              │                                               │
    ┌─────────▼──────────┐                          ┌─────────▼──────────┐
    │ LangChain + BYOK   │                          │ Flutter mobile     │
    │ streamed tutor and │                          │ native Classic and │
    │ question drafts    │                          │ web Chat handoff   │
    └────────────────────┘                          └────────────────────┘
```

The main implementation files are:

- `main.py`: web routes, Chat streaming, teacher settings and draft approval;
- `learning_chat.py`: guided Chat state machine, deterministic grading feedback
  and global free-form feedback rule;
- `question_generation.py`: LangChain question-generation schema and prompt;
- `db.py`: schema, selection policy, adaptive state and persistence;
- `science_catalog.py`: Primary Science and chemistry curriculum and seeding;
- `estonian_chemistry_catalog.py`: versioned Estonia Grade 8 outcomes, course,
  zero-knowledge prelude, exercises and deterministic item bank;
- `components/api.py`: public curriculum and guided-content API;
- `visualizations.py`: portable lesson visualization specifications; and
- `../fastlearn-mobile/lib/screens/learning/course_screen.dart` in the sister
  repository: native lesson reader, activities and mode controls.

## Two learning modes

Every science lesson is represented by one database lesson ID and can be
opened in either mode.

### Chat mode

Chat is the default student entry path. Course cards, course lesson lists and
mobile lesson taps open a lesson-grounded conversation.

The conversation supports:

- streamed free-form tutor responses;
- persistent threads in `chat_sessions` and `chat_messages`;
- structured course, lesson and quiz choices;
- answer-safe guided exercises;
- lesson visualizations;
- free-form follow-up questions; and
- quiz attempts, feedback and adaptive state updates.

The initial route is `/app/chat/new`. A course uses `?course=<slug>` and a
lesson uses `?lesson_id=<id>`. The resulting thread is displayed at
`/app/chat?chat=<session-id>` and streamed through `/app/chat/stream`.

### Classic mode

Classic mode is explicit rather than the default. It renders authored lesson
Markdown, video where configured, lesson visualizations, completion controls
and the conventional multiple-choice quiz.

The lesson route is `/app/lesson/<lesson-id>?mode=classic`; its assessment is
`/app/quiz/<quiz-id>?mode=classic`. Both pages contain a mode switch back to
the same lesson's Chat thread.

### Shared invariants

- Both modes use the same course, module and lesson records.
- Public clients never receive protected answer payloads.
- Structured attempts are graded on the server.
- Chat is the default; Classic remains directly selectable.
- A missing AI-generated pool never removes the deterministic baseline.

## Science and chemistry catalogue

`science_catalog.py` is the canonical authored source for three England-first
courses:

| Course | Level | Canonical lessons | Rich guided activities |
|---|---|---:|---:|
| Primary Science | beginner / primary | 9 | 2 |
| Chemistry Fundamentals | secondary through high school | 10 | 4 |
| Advanced Chemistry | first-year college/university | 9 | 3 |

The 28 canonical lessons each receive one baseline review in both Chat and
Classic mode. Two older Chemistry Fundamentals lesson titles are also mapped
for upgraded databases, allowing a legacy 12-lesson deployment to retain
12/12 coverage without deleting progress.

English and Estonian are authored first. Other student interface languages
fall back to English for science content that has not yet been reviewed in the
target language.

`db.bootstrap_schema()` calls `seed_science_courses()`. Seeding is idempotent:
it updates known reference content and uses conflict handling rather than
deleting teacher work or learner history.

## Country, grade and curriculum profiles

Curriculum identity is data, not a label inferred from a course title. A
framework identifies the country, jurisdiction, authority, effective version,
canonical language and official source URLs. A programme identifies the
subject, stage, grade and expected teaching time. Courses attach to programmes
through `course_curriculum_profiles`.

The teacher course wizard asks for country, grade/phase and a matching
curriculum programme. A course copies the selected profile's country,
jurisdiction, programme code, version, grade, canonical language and supported
languages for efficient API filtering. England is stored as `GB`/`GB-ENG`;
Estonia is stored separately as `EE`/`EE`. Existing Primary Science and
chemistry catalogues are explicitly attached to England profiles.

A profile becomes immutable when its first quiz or guided-exercise attempt is
recorded. Changing country, grade or curriculum after that point requires a
course clone. This protects the meaning of historic progress and assessment
records. `school_overlay` is reserved for a future school-specific ainekava;
the national programme remains the baseline.

Curriculum outcomes are atomic records. Lessons, quiz questions and guided
exercises each have many-to-many outcome mappings. Prompt context is assembled
from these mappings and contains allowed and excluded scope. This makes both
authored and generated questions traceable to a curriculum version.

Language follows the curriculum unless the learner explicitly overrides it.
For the Estonia course, an unqualified web or public API request uses Estonian;
`?lang=en` requests the reviewed English support translation. The mobile
lesson reader deliberately omits a language override, so it receives the
course canonical language. Catalogue browsing may still follow the app UI
language.

## Estonia Grade 8 chemistry reference course

`ee-grade-8-chemistry` is the deep reference implementation. Its canonical
source is the consolidated Estonian national basic-school curriculum,
Natural Sciences Appendix 4. The 2023 official English translation and the
teacher-facing `Keemia v1` breakdown support terminology and grade-level
sequencing. All source URLs are persisted with the framework record.

The course contains two layers:

| Layer | Units | Periods | Purpose |
|---|---:|---:|---|
| Zero-knowledge prelude | 12 | additional | Safety, lab equipment, observations, particles, symbols, formulae, subscripts, coefficients, units, ratios and percentages |
| Formal Grade 8 programme | 35 | 70 | Five national topic groups: chemistry, atomic structure, oxygen/hydrogen/oxides, acids/bases and common metals |

The prelude assumes the learner knows no element symbols and no chemistry
calculation method. It is mastery-gated: completing a lesson alone is not
enough; the learner must also pass its check before the next prelude lesson
opens. Passing the readiness lesson unlocks the first formal unit.

Every one of the 47 lessons has both modes, an authored guided exercise and a
quiz. The fixed bank contains 515 Estonian-first questions: five per prelude
unit and thirteen per formal unit. It mixes recall, classification, data
interpretation, safe-action scenarios and reasoned choices across three
within-grade difficulty bands. The course uses text/formula inputs, stepwise
numeric calculations, atom construction, equation balancing, a 3Dmol water
model and accessible Plotly visuals for mass percentage, periodic structure,
pH and metal activity. English variants use the same protected answers.

Grade 9 mole calculations, the extended system of inorganic substance classes
and carbon compounds are stored as excluded scope and included in generation
prompts. Safety-sensitive outcomes are tagged. This is a curriculum boundary,
not merely a prompt suggestion.

## Fixed question pipeline

`REVIEW_QUESTIONS` in `science_catalog.py` holds the deterministic baseline.
Each record contains:

- a stable source key;
- course slug and lesson title;
- difficulty and concepts;
- English and Estonian question text;
- localized options and explanation; and
- the correct option index.

The seeder materializes one authored record in two forms:

1. an `interactive_exercises` record linked through `lesson_exercises`, used
   by Chat and native mobile Classic; and
2. a `quiz_questions` record under the lesson quiz, used by web Classic and
   the structured Chat quiz.

The interactive exercise's public payload contains the prompt and options.
Its protected `answer_payload` contains the correct index and localized
feedback. The web quiz stores its answer key in `quiz_questions`, which is
never returned by the public curriculum endpoints.

## AI-assisted question pipeline

AI-assisted approved questions are the default question source. This does not
mean an unreviewed model response is presented directly to a learner.

```text
Teacher/admin selects lesson, difficulty and optional guidance
                              │
                              ▼
             LangChain structured generation
             question_generation.py
                              │
                              ▼
       Pydantic validates languages, option count, uniqueness,
       exact answer membership and explanation length
                              │
                              ▼
       content_drafts(status='pending', generation_source='llm')
                              │
                    approve ──┴── reject
                       │              │
                       ▼              ▼
       quiz_questions(source_type='llm')   retained as rejected audit record
```

### Prompt and validation

`question_generation.GENERATOR_SYSTEM_PROMPT` requires one equivalent
question for exactly the languages required by the selected curriculum. It
includes country, jurisdiction, programme version, stage, grade, target
outcome IDs and explicit exclusions. It requires one defensible answer, a
worked solution, misconception target, cognitive process, safety
classification and scope confirmation. It also requires symbols to be defined
and calculations to show steps, units and a reasonableness check. Lesson text
and teacher guidance are delimited as source material rather than system
instructions.

`GeneratedQuestionSet` and `QuestionVariant` enforce the response structure.
The correct answer must exactly match one unique option. The same schema is
validated again at approval time before database publication.

### Teacher and administrator controls

The management page `/app/course/<course-id>/strategy` exposes:

- **AI-assisted approved questions** (`llm_reviewed`); and
- **Fixed approved questions** (`fixed`).

Administrators can configure catalogue courses. Teachers configure courses
they own, including editable clones of protected catalogue courses. Generating
a question creates a draft; approving it publishes the question. Generation,
approval and rejection are written to the audit log.

### Provider routing

Generation uses the shared LangChain BYOK gate:

1. use the workspace's encrypted BYOK provider and key when present;
2. otherwise use the configured deployment provider within the free-query
   allowance; or
3. refuse generation with a configuration message when neither is available.

The provider factory supports OpenAI, xAI, Anthropic and optional Google
Gemini integrations. The successful query is counted only after the validated
draft is stored.

## Question selection and fallback

`db.get_quiz_questions()` applies the effective course setting before
difficulty filtering.

```text
question_source = fixed
    └─ select source_type != 'llm'

question_source = llm_reviewed
    ├─ approved source_type = 'llm' exists → use reviewed LLM pool
    └─ no reviewed LLM question exists    → use authored fixed pool
```

The fallback makes generative mode safe to enable by default on a new course:
all 28 science lessons work immediately, while approved generated questions
replace the fixed selection as their pools become available.

Adaptive difficulty is a separate concern. After source selection, question
difficulty is filtered to the closest available `difficulty_level`. The
Linear/Adaptive learning strategy does not bypass approval or answer privacy.

## Answer feedback

Chat mode has one global feedback contract:

- a correct answer receives an explicit correct verdict and an explanation;
- an incorrect answer receives an explicit incorrect verdict, the correct
  answer and an explanation; and
- a learner asking a question does not receive an invented verdict.

Structured guided activities use `learning_chat.exercise_feedback()`. It reads
the protected server-side answer payload after grading. Science activities
contain authored bilingual explanations; other exercise engines receive a
deterministic answer summary and concept-grounded fallback explanation.

Structured Chat quizzes use the localized `quiz_questions.explanation`. If an
older question lacks one, the server supplies a bounded fallback reason.

Free-form text and voice tutors cannot be graded deterministically because the
learner may answer in unrestricted language. Both receive
`CHAT_FEEDBACK_RULE` as a global system instruction: when the message is an
attempted answer, the model must give the verdict, correction and reasoning;
when it is a question, it answers normally. Correct answers are not disclosed
before an attempt.

## Database model

The default schema name is `fastlms` and can be changed with `DB_SCHEMA`.

| Table | Relevant fields | Responsibility |
|---|---|---|
| `courses` | `slug`, country/jurisdiction, curriculum/version, grade, language | Course identity, cached curriculum selection and protected catalogue status |
| `curriculum_frameworks` | country, jurisdiction, authority, version, languages, sources | Versioned official curriculum identity |
| `curriculum_programs`, `curriculum_topics`, `curriculum_outcomes` | subject, stage, grade, time, scope | Atomic national programme model |
| `course_curriculum_profiles` | programme, lock, school overlay | Immutable-after-attempt course selection |
| `lesson_curriculum_outcomes`, `quiz_question_curriculum_outcomes`, `exercise_curriculum_outcomes` | foreign keys | Outcome traceability |
| `modules`, `lessons` | content and order | Shared curriculum for both modes |
| `quizzes` | lesson, threshold, XP | Conventional lesson assessment |
| `quiz_questions` | options, correct answer, explanation, difficulty, `source_type` | Approved authored or LLM question bank |
| `interactive_exercises` | public payload, protected answer payload | Guided Chat/mobile activity |
| `lesson_exercises` | lesson, exercise, order | Activity-to-lesson mapping |
| `exercise_translations` | localized prompt and public payload | Answer-safe activity translation |
| `course_learning_settings` | strategy, thresholds, `question_source` | Teacher/admin course controls |
| `content_drafts` | JSON content, status, `generation_source` | Approval queue and provenance |
| `content_translations` | localized titles, content, questions and explanations | Shared localization overlay |
| `chat_sessions`, `chat_messages` | context and messages | Persistent Chat state |
| `quiz_attempts`, `exercise_attempts` | answers and verdicts | Learner assessment records |
| `lesson_visualizations` | localized portable specifications | Web and mobile visual content |
| `audit_log` | actor, action, details | Settings and approval accountability |

`source_type` is `authored` or `llm`. `generation_source` is `template` or
`llm`. The provenance values are copied when a teacher clones a course.

## Web routes and public API

### Student web routes

| Route | Purpose |
|---|---|
| `/app/courses` | Catalogue; student cards default to Chat |
| `/app/course/<slug>` | Mode selector and course overview |
| `/app/chat/new?course=<slug>` | Start course-grounded Chat |
| `/app/chat/new?lesson_id=<id>` | Start lesson-grounded Chat |
| `/app/chat/stream` | Stream free-form or guided responses |
| `/app/chat/exercise/stream` | Grade a rich guided exercise |
| `/app/lesson/<id>?mode=classic` | Classic lesson |
| `/app/quiz/<id>?mode=classic` | Classic quiz |

### Teacher/admin routes

| Route | Purpose |
|---|---|
| `/app/course/<id>/strategy` | Question source and adaptive settings |
| `/app/course/<id>/draft/generate` | Generate validated content draft |
| `/app/course/<id>/draft` | Approve or reject a draft |

### Public mobile-facing API

The FastAPI application is mounted under `/api`, with versioned paths under
`/api/v1`:

- `GET /courses` and `GET /courses/<id>/curriculum`;
- `GET /lessons/<id>/guided-content`;
- `GET /lessons/<id>/exercises` and `/visualizations`; and
- `POST /exercises/<id>/check`.

Curriculum and guided-content reads are public and answer-safe. Learner data
and persistence operations use protected endpoints. The stateless exercise check endpoint
loads the answer key only on the server and returns a verdict, not the key.

## Mobile architecture

The Flutter application uses `API_BASE_URL`, defaulting to
`https://fastlearn.school/api/v1`.

Native Classic mode renders:

- lesson Markdown;
- a portable subset of lesson visualizations using `fl_chart`;
- accessible data-table fallbacks;
- multiple-choice and richer chemistry activities; and
- server-graded exercise verdicts.

Course records carry country, grade, curriculum code and canonical language;
the catalogue shows a country/grade badge. Curriculum and guided-content calls
omit a language parameter by default so the server applies the national
course's canonical language. Flutter renders numeric calculations, formula and
short-text answers, atoms and equations, including localized operators.

Chat is the default lesson tap. It uses a lesson-specific secure browser
handoff to `/app/chat/new?lesson_id=<id>`. A separate Classic icon opens the
native reader, and the reader retains a Chat action. A fully native
authenticated SSE Chat renderer is not yet implemented.

## Security and answer privacy

- `db.get_interactive_exercise()` removes `answer_payload` unless an internal
  caller explicitly requests it.
- Public exercise and guided-content APIs use the answer-safe form.
- Answer payloads, tolerances and correct quiz options are never embedded in
  visualization or public exercise JSON.
- Guided answers are graded against the protected payload on the server.
- Generated output is schema-validated, stored as pending and reviewed before
  publication.
- Course management routes enforce teacher/admin ownership rules.
- BYOK credentials are encrypted at rest by the shared BYOK component.
- Generation failures do not publish partial drafts or consume the fixed bank.

## Model and runtime configuration

Relevant environment variables include:

| Variable | Purpose |
|---|---|
| `DB_URL` | PostgreSQL connection URL |
| `DB_SCHEMA` | Schema name; defaults to `fastlms` |
| `MODEL_PROVIDER` / `LLM_PROVIDER` | Deployment LLM provider |
| `MODEL_NAME` | Deployment model override |
| `OPENAI_API_KEY` | OpenAI deployment key |
| `XAI_API_KEY` | xAI text and voice key |
| `ANTHROPIC_API_KEY` | Anthropic deployment key |
| `GOOGLE_API_KEY` | Optional Gemini key |
| `BYOK_DB` | Persistent BYOK credential/quota store |
| `BYOK_ENCRYPTION_KEY` | Encryption key for stored BYOK credentials |
| `BYOK_FREE_QUERY_LIMIT` | Deployment-funded query allowance |
| `FASTSME_API_TOKEN` | Protected learner-data and persistence API authentication |
| `JUDGE_LLM` | Model used by the separate evaluation runner |

Question generation uses the provider/model selected by BYOK or the shared
deployment model. `JUDGE_LLM` affects evaluation, not learner-facing question
generation.

## Verification and evaluation

The automated suite checks:

- exact 28-lesson canonical science coverage and two legacy mappings;
- the Estonia course's 12 prelude + 35 formal units, exact 70-period formal
  pacing, all 50 atomic outcomes and 515 fixed questions;
- Estonian default/English override behavior, prelude mastery gates and
  idempotent PostgreSQL seeding;
- one bilingual baseline review per canonical lesson;
- answer-safe exercise payloads;
- chemistry and chess typed-answer formats;
- explicit Chat/Classic web route controls;
- Chat-first course and lesson entry;
- reasoned correct and incorrect Chat feedback;
- generator schema validation and source fallback;
- Flutter Classic/Chat controls and native lesson rendering; and
- public API and visualization behavior.

`tests/test_science_postgres_integration.py` can run against a disposable
PostgreSQL instance by setting `RUN_POSTGRES_INTEGRATION=1` and `DB_URL`. It
boots the real schema twice to prove idempotence, confirms all England science
and all 47 Estonia lessons have Chat exercises and Classic questions, validates
source switching, curriculum profiles, language defaults, mastery gating and
answer privacy, and renders the applicable routes.

Student-learning LLM evaluations live under `evals/`. They use stored ground
truth and a configurable `JUDGE_LLM`; this evaluation path is separate from
the production grading keys.

## Known gaps

The authoritative gap list is maintained in
[`quiz_roadmap.md`](quiz_roadmap.md). The main architectural gaps are:

- native mobile Chat currently uses a secure web handoff;
- mobile completion state is still device-local;
- prose-only choices from free-form LLM output are not converted into typed
  action events;
- country programmes beyond England and Estonia need modelling and review;
- the mobile UI needs an explicit per-course English support-language override
  while preserving the national-language default;
- AI-assisted pools require teacher/admin generation and approval; and
- item-bank depth, calibration and automated ambiguity/alignment evaluations
  need expansion before any approval gate is relaxed.
