# FastLMS

Current release: `v1.3.0`

Open-source learning management system built with [FastHTML](https://github.com/AnswerDotAI/fasthtml). Python-first, no JavaScript framework — HTMX handles all interactivity. Features a 3-pane layout, a New Chat workspace with SSE streaming, and Duolingo-style learner elements (XP, streaks, badges, leaderboards, levels).

FastLearn 1.3 adds Chess Foundations I for children aged 3–12, with original multilingual lessons, guided chessboards, private server-side grading, adaptive practice records, and API access. Role-specific chat keeps students, teachers, and administrators on their own paths even when older conversations exist.

![FastLMS Demo](docs/fastlms-demo.gif)

## Features

### Learning
- **Course management** — courses, modules, lessons with markdown content and embedded video
- **Quizzes** — multiple-choice with auto-grading, pass thresholds, explanations, and XP rewards
- **Progress tracking** — per-lesson completion, per-course percentage bars, dashboard overview
- **Chat-first learning** — persistent conversations for course choice, lessons, quizzes, language practice, and open tutoring, with SSE responses from Grok / OpenAI / Claude
- **Discussions** — per-lesson threaded comments
- **Role-based access** — one administrator, scoped teachers, and students
- **Team and assignments** — Postmark invitations, course grants, and visible Assigned tags
- **Active-time reporting** — lesson, quiz, and conversational tutor time with visibility and inactivity controls
- **Adaptive learning** — configurable thresholds, bounded difficulty changes, remediation, and extension drafts
- **Language learning** — native-to-target practice across 10 major languages using a ranked frequency dictionary, browser pronunciation, anticipation, and graduated recall
- **Multilingual demo** — complete catalogue and core UI in English, Estonian, Lithuanian, and Spanish
- **Guided chess** — 10 original beginner lessons and 20 interactive board exercises covering coordinates, rooks, bishops, queens, and knights
- **Integration API** — public localized curriculum and answer-safe exercises, plus bearer-protected assignments, progress, attempts, learners, and chat history

### Interactivity
- **XP system** — earn points for completing lessons and passing quizzes
- **Levels** — Novice → Apprentice → Scholar → Expert → Master → Grandmaster (XP thresholds)
- **Streaks** — consecutive-day activity tracking with badge rewards at 3, 7, and 30 days
- **Badges** — 11 achievement types (first lesson, quiz ace, XP milestones, course completion)
- **Leaderboard** — ranked by XP with level badges and streak display

### School administration (the `frappe/education` layer — `school.py`)
For schools/colleges, not just self-serve courses. Admin/teacher pages under **/app/school**:
- **Students & guardians** — a first-class Student (distinct from a learner account) with guardian contacts and class/section groups
- **Programmes & enrolment** — course bundles per academic term, with student groups
- **Gradebook** — assessments (mid-term / coursework / exam) with a grading scale (A–U) and per-student averages
- **Attendance** — per-student register with present/absent rates
- **Fees** — tuition fee structures per programme/term, per-student fees with payments and AR-style status (Unpaid / Partly Paid / Paid / Overdue)
- **Academic calendar** — years and terms

17 tables in `school.py`, seeded by `school.seed_school()`. See
[docs/EDUCATION-COMPARISON.md](docs/EDUCATION-COMPARISON.md) for how this maps to
`frappe/education`.

### Architecture
- **3-pane layout** — left navigation (280px), center content (flex), right canvas (400px slide-in)
- **Light theme** — calm violet palette, Inter font, CSS custom properties
- **Server-side rendering** — all UI generated in Python, HTMX for partial updates
- **PostgreSQL** — full schema with courses, users, progress, interactivity, chat history
- **Multi-provider AI** — pluggable LLM backend (X.AI Grok, OpenAI, Anthropic Claude)
- **Language engine** — checked-in multilingual frequency data with deterministic spaced-recall scheduling and per-learner review state

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/predictivelabsai/FastLMS.git
cd FastLMS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your database URL and LLM API key:

```
DB_URL=postgresql://user:pass@localhost:5432/mydb
MODEL_PROVIDER=xai
XAI_API_KEY=xai-...
```

### 3. Seed demo data

```bash
python seed.py
```

This creates the `fastlms` schema, 3 demo courses (Python, ML, FastHTML), the protected Chess Foundations course, 11 badges, and two accounts:
- **Teacher**: `instructor@fastlms.dev` / `admin`
- **Student**: `student@fastlms.dev` / `admin`

To add 11 academic and creative subjects (Mathematics, Physics, Biology, Chemistry, English, Geography, Creative Writing, Art History, Music History, Art, and Music):

```bash
python seed_subjects.py
```

### 4. Run

```bash
python main.py
```

Open [http://localhost:5001](http://localhost:5001).

## Project structure

```
FastLMS/
├── main.py                  # FastHTML app — all routes
├── db.py                    # PostgreSQL schema, queries, interactivity logic
├── chess_course.py          # Original four-language chess curriculum and exercise seed
├── chess_engine.py          # Private server-side chess grading
├── seed.py                  # Demo data seeder (courses, badges, users)
├── seed_subjects.py         # Academic and creative subjects seeder (11 courses with lessons + quizzes)
├── components/
│   └── layout.py            # 3-pane layout, UI fragments (cards, badges, progress bars)
├── static/
│   ├── app.css              # Light theme, 3-pane grid, all components
│   └── chat.js              # SSE streaming chat client
├── requirements.txt
├── .env.example
└── LICENSE                  # MIT
```

## Database schema

All tables live in the `fastlms` PostgreSQL schema:

| Table | Purpose |
|-------|---------|
| `users` | Auth, XP, level, streak, role (student/teacher/admin) |
| `courses` | Title, slug, category, difficulty, publish/default state and owner |
| `modules` | Ordered sections within a course |
| `lessons` | Markdown content, video URL, XP reward, duration |
| `quizzes` | Per-lesson, pass threshold, XP reward |
| `quiz_questions` | Multiple-choice with options (JSONB), correct answer, explanation |
| `lesson_progress` | Per-user lesson completion status |
| `quiz_attempts` | Score, pass/fail, answers (JSONB) |
| `enrolments` | User ↔ course many-to-many |
| `badges` | Definitions with criteria (XP, streak, lessons, quiz score) |
| `user_badges` | Awarded badges per user |
| `chat_messages` | AI tutor conversation history per user/lesson |
| `discussions` | Per-lesson threaded comments |
| `course_assignments` | Explicit assigned-course tags for students |
| `teacher_course_access` | Scoped teacher course grants |
| `invitations` | Single-use, revocable, non-expiring invitations |
| `learning_time` | Active seconds by learner, course, and learning context |
| `course_learning_settings` | Linear/adaptive strategy and thresholds |
| `learner_course_state` | Current bounded adaptive difficulty state |
| `adaptive_recommendations` | Explainable remediation and extension decisions |
| `content_drafts` | Multilingual teacher-approval queue |
| `content_translations` | Approved and catalogue translations, including Spanish |
| `interactive_exercises` | Answer-safe exercise presentation plus private grading payload |
| `exercise_translations` | Localized prompts and public interaction labels |
| `lesson_exercises` | Ordered lesson-to-exercise links |
| `exercise_attempts` | Graded attempts, active duration, difficulty, chat and learner context |
| `language_profiles` | Native language, target language, and daily practice goal |
| `language_reviews` | Per-expression graduated-recall state and next due time |
| `language_attempts` | Immutable language-practice rating history |
| `audit_log` | Role, invitation, assignment, strategy, and approval events |

## Interactivity details

### XP and levels

| Level | XP Threshold |
|-------|-------------|
| Novice | 0 |
| Apprentice | 500 |
| Scholar | 2,000 |
| Expert | 5,000 |
| Master | 10,000 |
| Grandmaster | 25,000 |

XP is awarded for lesson completion (configurable per lesson, default 25) and quiz passes (configurable per quiz, default 50).

### Badges

| Badge | Criteria |
|-------|----------|
| First Steps | Complete 1 lesson |
| Dedicated Learner | Complete 10 lessons |
| Knowledge Seeker | Complete 50 lessons |
| On Fire | 3-day streak |
| Week Warrior | 7-day streak |
| Month Master | 30-day streak |
| Quiz Ace | Score 100% on any quiz |
| Rising Star | Earn 500 XP |
| Scholar | Earn 2,000 XP |
| Expert | Earn 5,000 XP |
| Graduate | Complete an entire course |

Badges are checked automatically after every lesson completion and quiz submission.

### Streaks

Activity on consecutive days increments the streak counter. Missing a day resets it to 1. The streak updates on lesson completion and quiz submission.

## New Chat workspace

The chat supports three LLM providers via environment variables:

| Provider | `MODEL_PROVIDER` | `DEFAULT_MODEL` | API Key Var |
|----------|-----------------|-----------------|-------------|
| X.AI (Grok) | `xai` | `grok-4-1-fast-reasoning` | `XAI_API_KEY` |
| OpenAI | `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |

Students land in chat after signing in. Course, lesson, adaptive quiz, and language-learning choices appear as clickable chat responses and also accept typed answers such as `A` or `B`. Open-ended tutor responses receive the active lesson context. Conversation history and guided-learning state are persisted per user and thread.

## Routes

| Route | Description |
|-------|-------------|
| `GET /` | Landing page |
| `GET /app` | Chat-first student entry point |
| `GET /app/dashboard` | Optional progress dashboard (courses, stats, badges) |
| `GET /app/courses` | Browse all published courses |
| `GET /app/course/{slug}` | Course detail with module/lesson sidebar |
| `POST /app/course/{id}/clone` | Clone a protected admin default into a teacher-owned draft |
| `POST /app/course/{slug}/enrol` | Enrol in a course |
| `GET /app/lesson/{id}` | Lesson view (markdown, video, actions) |
| `POST /app/lesson/{id}/complete` | Mark lesson complete, award XP |
| `GET /app/quiz/{id}` | Take a quiz |
| `POST /app/quiz/{id}/submit` | Submit quiz, auto-grade, award XP |
| `GET /app/chat/new` | Create a contextual course, lesson, quiz, or language chat |
| `GET /app/chat` | Persistent chat workspace and history |
| `GET /app/chat/stream` | SSE streaming endpoint |
| `POST /app/chat/exercise/stream` | Grade a rich board answer and stream feedback into chat |
| `GET /app/leaderboard` | XP leaderboard |
| `GET /app/profile` | User profile, badges, progress to next level |
| `GET /app/manage` | Teacher course management |
| `GET /app/configure` | Course configuration wizard (5-step: course → modules → lessons → quizzes → publish) |
| `GET /app/team` | Invite users, change roles, and assign courses |
| `GET /app/reports` | Scoped progress, assessment, and active-time reporting |
| `GET /app/course/{id}/strategy` | Configure adaptive learning and review generated drafts |
| `POST /app/activity/heartbeat` | Record bounded active learning time |
| `GET /app/languages` | Start native-to-target language practice in chat |
| `POST /app/languages/preferences` | Save the learner's language pair and daily goal |
| `POST /app/languages/review` | Schedule the next graduated-recall interval |
| `GET /healthz` | Health check |

## Supported Courses

FastLMS ships with 15 ready-to-use courses:

### Programming & Technology
| Course | Category | Difficulty | Modules | Lessons |
|--------|----------|------------|---------|---------|
| Python Fundamentals | Programming | Beginner | 2 | 5 |
| Machine Learning with scikit-learn | Data Science | Intermediate | 1 | 2 |
| Building Web Apps with FastHTML | Web Development | Intermediate | 1 | 1 |

### Academic Subjects
| Course | Category | Difficulty | Modules | Lessons |
|--------|----------|------------|---------|---------|
| Mathematics Foundations | Mathematics | Beginner | 2 (Algebra, Geometry) | 3 |
| Physics Essentials | Physics | Intermediate | 1 (Mechanics) | 2 |
| Biology: Life Sciences | Biology | Beginner | 2 (Cell Biology, Genetics) | 4 |
| Chemistry Fundamentals | Chemistry | Intermediate | 2 (Atomic Structure, Reactions) | 4 |
| English Language & Literature | English | Beginner | 2 (Reading, Writing) | 4 |
| Geography: Physical & Human | Geography | Beginner | 2 (Physical, Human) | 4 |
| Creative Writing | Creative Writing | Beginner | 2 (Storytelling, Poetry) | 4 |

### Art & Music
| Course | Category | Difficulty | Modules | Lessons |
|--------|----------|------------|---------|---------|
| Art History | Art History | Beginner | 1 (Seeing Art Across Time) | 2 |
| Music History | Music History | Beginner | 1 (Listening Through Time) | 2 |
| Art | Art | Beginner | 1 (Visual Language) | 2 |
| Music | Music | Beginner | 1 (How Music Works) | 2 |

### Chess
| Course | Category | Difficulty | Modules | Lessons |
|--------|----------|------------|---------|---------|
| Chess Foundations I | Chess | Beginner | 3 | 10 |

Chess Foundations I is installed idempotently during schema bootstrap. Its 20 guided exercises cover multiple choice, square selection, piece placement, route planning, and capture sequences. Learner-facing text is original FastLearn material available in English, Estonian, Lithuanian, and Spanish; the board engine keeps expected answers on the server.

Run `python seed.py` for the 3 programming courses, then `python seed_subjects.py` for the 11 academic and creative subjects.

## Integration API

Open Swagger at `https://fastlearn.fun/api/docs`, ReDoc at `/api/redoc`, or the developer overview at `/developers`. Published courses, modules, lessons, and answer-safe exercises are public. Set `FASTSME_API_TOKEN` and send it as a bearer token for learners, assignments, enrolments, progress, recorded exercise attempts, and chat history.

## Language learning

FastLearn includes a generic native-to-target practice engine rather than one
fixed language course. Learners can start from English, Spanish, French, German,
Italian, Portuguese, Mandarin Chinese, Arabic, Japanese, Hindi, Estonian, or
Lithuanian and choose one of ten major target languages: English, Spanish,
French, German, Italian, Portuguese, Mandarin Chinese, Arabic, Japanese, or
Hindi.

The initial checked-in dictionary contains 30 frequency-informed words and
functional expressions aligned across every supported native language. Sessions
ask the learner to anticipate and say the target phrase, reveal and listen to
the answer, then rate recall. A deterministic graduated-interval scheduler
returns difficult material sooner and expands intervals after successful recall.
This uses general audio-first and spaced-repetition principles; it does not copy
proprietary course content.

## Design inspiration

The 3-pane layout, SSE streaming chat, and interactivity engine are inspired by [LiquidRound](https://github.com/plai/liquidround), an M&A research platform built on the same FastHTML + PostgreSQL + HTMX stack. FastLMS adapts that architecture for education with a lighter FastLearn product surface.

## License

MIT. See [LICENSE](LICENSE).
