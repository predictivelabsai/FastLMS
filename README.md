# FastLMS

Open-source learning management system built with [FastHTML](https://github.com/AnswerDotAI/fasthtml). Python-first, no JavaScript framework — HTMX handles all interactivity. Features a 3-pane layout, AI tutor chat with SSE streaming, and Duolingo-style interactive elements (XP, streaks, badges, leaderboards, levels).

![FastLMS Demo](docs/fastlms-demo.gif)

## Features

### Learning
- **Course management** — courses, modules, lessons with markdown content and embedded video
- **Quizzes** — multiple-choice with auto-grading, pass thresholds, explanations, and XP rewards
- **Progress tracking** — per-lesson completion, per-course percentage bars, dashboard overview
- **AI Tutor** — SSE streaming chat powered by Grok / OpenAI / Claude, with lesson-aware context
- **Discussions** — per-lesson threaded comments

### Interactivity
- **XP system** — earn points for completing lessons and passing quizzes
- **Levels** — Novice → Apprentice → Scholar → Expert → Master → Grandmaster (XP thresholds)
- **Streaks** — consecutive-day activity tracking with badge rewards at 3, 7, and 30 days
- **Badges** — 11 achievement types (first lesson, quiz ace, XP milestones, course completion)
- **Leaderboard** — ranked by XP with level badges and streak display

### Architecture
- **3-pane layout** — left navigation (280px), center content (flex), right canvas (400px slide-in)
- **Dark theme** — navy + amber palette, Inter font, CSS custom properties
- **Server-side rendering** — all UI generated in Python, HTMX for partial updates
- **PostgreSQL** — full schema with courses, users, progress, interactivity, chat history
- **Multi-provider AI** — pluggable LLM backend (X.AI Grok, OpenAI, Anthropic Claude)

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/predictivelabs/FastLMS.git
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

This creates the `fastlms` schema, 3 demo courses (Python, ML, FastHTML), 11 badges, and two accounts:
- **Instructor**: `instructor@fastlms.dev` / `admin`
- **Student**: `student@fastlms.dev` / `admin`

To add 7 academic subjects (Mathematics, Physics, Biology, Chemistry, English, Geography, Creative Writing):

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
├── seed.py                  # Demo data seeder (courses, badges, users)
├── seed_subjects.py         # Academic subjects seeder (7 courses with lessons + quizzes)
├── components/
│   └── layout.py            # 3-pane layout, UI fragments (cards, badges, progress bars)
├── static/
│   ├── app.css              # Dark theme (navy + amber), 3-pane grid, all components
│   └── chat.js              # SSE streaming chat client
├── requirements.txt
├── .env.example
└── LICENSE                  # MIT
```

## Database schema

All tables live in the `fastlms` PostgreSQL schema:

| Table | Purpose |
|-------|---------|
| `users` | Auth, XP, level, streak, role (student/instructor/admin) |
| `courses` | Title, slug, category, difficulty, publish state |
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

## AI Tutor

The chat supports three LLM providers via environment variables:

| Provider | `MODEL_PROVIDER` | `DEFAULT_MODEL` | API Key Var |
|----------|-----------------|-----------------|-------------|
| X.AI (Grok) | `xai` | `grok-4-1-fast-reasoning` | `XAI_API_KEY` |
| OpenAI | `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |

The tutor receives lesson context automatically when accessed from a lesson page. Chat history is persisted per user per lesson.

## Routes

| Route | Description |
|-------|-------------|
| `GET /` | Landing page |
| `GET /app` | Dashboard (enrolled courses, stats, badges) |
| `GET /app/courses` | Browse all published courses |
| `GET /app/course/{slug}` | Course detail with module/lesson sidebar |
| `POST /app/course/{slug}/enrol` | Enrol in a course |
| `GET /app/lesson/{id}` | Lesson view (markdown, video, actions) |
| `POST /app/lesson/{id}/complete` | Mark lesson complete, award XP |
| `GET /app/quiz/{id}` | Take a quiz |
| `POST /app/quiz/{id}/submit` | Submit quiz, auto-grade, award XP |
| `GET /app/chat` | AI Tutor chat page |
| `GET /app/chat/stream` | SSE streaming endpoint |
| `GET /app/leaderboard` | XP leaderboard |
| `GET /app/profile` | User profile, badges, progress to next level |
| `GET /app/manage` | Instructor course management |
| `GET /app/configure` | Course configuration wizard (5-step: course → modules → lessons → quizzes → publish) |
| `GET /healthz` | Health check |

## Supported Courses

FastLMS ships with 10 ready-to-use courses:

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

Run `python seed.py` for the 3 programming courses, then `python seed_subjects.py` for the 7 academic subjects.

## Design inspiration

The 3-pane layout, dark theme, SSE streaming chat, and interactivity engine are inspired by [LiquidRound](https://github.com/plai/liquidround), an M&A research platform built on the same FastHTML + PostgreSQL + HTMX stack. FastLMS adapts that architecture for education.

## License

MIT. See [LICENSE](LICENSE).
