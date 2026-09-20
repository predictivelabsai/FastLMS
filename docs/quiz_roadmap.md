# Quiz and two-mode lesson roadmap

## Lesson-mode contract

Every student lesson should offer two explicit ways to learn:

1. **Chat mode** opens a lesson-grounded tutor conversation. The learner can
   ask free-form questions, receive streamed explanations, choose structured
   next actions, use visualizations and complete guided activities.
2. **Classic mode** presents the authored lesson, available visualizations and
   an answer-safe multiple-choice review with immediate explanations.

Both modes use the same lesson ID and curriculum source. Answers remain on the
server, attempts contribute to the same learning record on the web, and a
learner can switch modes without searching for the lesson again.

Chat is the default student entry mode from course cards, course lesson lists
and mobile lesson taps. Classic remains an explicit secondary action on web
and mobile.

## Answer-feedback contract

Chat mode applies one global rule to every assessable student answer:

- for a correct answer, state that it is correct and explain why;
- for an incorrect answer, state that it is incorrect, reveal the correct
  answer, and explain why that answer is correct; and
- do not invent a correctness verdict when the learner is asking a question
  rather than attempting an answer.

Structured quizzes and guided exercises enforce this from the protected
server-side answer key. Free-form text and voice tutors receive the same rule
in their system instructions. The science question bank stores bilingual
answer explanations alongside, but never inside, the public exercise payload.

## Fixed and AI-assisted question sources

Teacher and administrator course settings expose two question-source modes:

- **AI-assisted approved questions** is the default. LangChain generates an
  original EN/ET/LT/ES structured draft from the selected lesson, difficulty
  and optional teacher guidance. A teacher or administrator must approve it
  before it enters the quiz bank.
- **Fixed approved questions** uses only authored and seeded questions.

Published questions retain their provenance. AI-assisted mode draws from the
approved LLM pool and automatically falls back to the fixed bank when no AI
question has been approved, so every science lesson remains usable. Prompt
quality and automated evaluation remain ongoing controls; they do not replace
human approval.

## Science and chemistry coverage

| Course | Authored lessons | Chat review coverage | Classic quiz coverage | Rich activities |
|---|---:|---:|---:|---:|
| Primary Science | 9 | 9/9 | 9/9 | 2 |
| Chemistry Fundamentals | 10 | 10/10 | 10/10 | 4 |
| Advanced Chemistry | 9 | 9/9 | 9/9 | 3 |
| Estonia Grade 8 Chemistry | 47 (12 prelude + 35 formal) | 47/47 | 47/47; 515 questions | 47 + 3D/Plotly visuals |

Two older Chemistry Fundamentals lessons may still exist in upgraded
deployments: **Atoms and the Periodic Table** and **Types of Reactions and
Balancing Equations**. The seeder gives both a Chat review and Classic quiz, so
an upgraded 12-lesson deployment remains 12/12 while existing progress is
preserved.

The 28 canonical reviews and two compatibility reviews are original English
and Estonian questions. Each is stored twice from one authored record:

- as an answer-safe `multiple_choice` interactive exercise used by Chat and
  native mobile Classic mode; and
- as a conventional quiz question used by web Classic mode.

The richer activities remain additional practice: atom construction, equation
balancing, mole calculation, 3D molecular shape, particle state, material
choice, spectroscopy and mechanism reasoning.

The Estonia course is a separate, versioned national programme rather than a
translation of Chemistry Fundamentals. Estonian is canonical, English is an
explicit support translation, its prelude is mastery-gated, and its question
prompts carry outcome IDs plus Grade 9 exclusions. Country/curriculum/grade is
locked after the first learner attempt; a different curriculum requires a
clone.

## Remaining catalogue gaps

These gaps are outside the completed Primary Science and Chemistry scope:

| Course group | Current authored quiz coverage | Structured interactive coverage | Next work |
|---|---:|---:|---|
| Python Fundamentals | 2/5 lessons | 0/5 | Add coding checks and reviews to three lessons |
| Machine Learning | 0/2 | 0/2 | Add model-selection and evaluation reviews |
| FastHTML Web Apps | 0/1 | 0/1 | Add request/response and component practice |
| Mathematics Foundations | 1/3 | 0/3 | Add reviews and equation/geometry interactions |
| Physics Essentials | 1/2 | 0/2 | Add numerical and graph activities |
| Biology Life Sciences | 1/2 | 0/2 | Add classification and process reviews |
| English Language & Literature | 1/2 | 0/2 | Add reading-evidence and writing-choice reviews |
| Geography | 1/2 | 0/2 | Add map/data interpretation reviews |
| Creative Writing | 1/3 | 0/3 | Add planning and revision choices |
| Art and Music courses | 1/2 per course | 0/2 per course | Add visual/listening evidence activities |
| Chess Foundations | 0 conventional quizzes | 10/10 | Decide whether rich board practice makes a separate quiz useful |

Visualizations already exist in parts of mathematics, physics, geography, art
and science, but a visualization alone is not counted as a reviewed activity.

## Product gaps after content coverage

- Mobile Classic mode is native, but lesson Chat currently uses the secure web
  tutor handoff. A native authenticated SSE client with structured choice and
  exercise rendering remains future work.
- Mobile completion is currently stored on the device; web quiz attempts and
  XP use the server-side learner record. These should converge after the mobile
  authentication flow is finalized.
- Structured lesson actions remain visible after a free-form tutor answer, but
  new choices written only in generated prose are not converted into buttons.
  A typed tutor-action event should replace prompt-only lettered suggestions.
- English and Estonian science reviews are authored and reviewed first. Other
  interface languages currently fall back to English for these questions.
- One baseline review question now guarantees mode coverage. Additional item
  banks, difficulty calibration and fixed mini-mocks remain separate depth and
  exam-preparation work rather than prerequisites for the two-mode contract.
- AI-assisted pools begin empty and rely on teacher/admin generation and
  approval. Automated ambiguity, curriculum-alignment and explanation-quality
  evals should be expanded before relaxing the approval gate.

## Release gates

- Every canonical science lesson maps to exactly one baseline review record.
- Every deployed canonical or known legacy science lesson has at least one
  answer-safe interactive exercise and one Classic quiz question.
- Student web routes allow both Classic and Chat instead of redirecting Classic
  requests into Chat.
- Web and mobile show an explicit mode switch that retains the lesson ID.
- English and Estonian correct answers grade identically.
- Correct Chat answers include reasoning; incorrect answers include the
  correct answer and reasoning.
- AI-authored questions are schema-valid, provenance-tagged and unavailable to
  students until approved.
- Public lesson bundles never expose `answer_payload`, quiz answer keys or
  grading tolerances.
- Estonia Grade 8 retains exactly 35 formal units / 70 periods, 12 additional
  zero-knowledge prelude units, 50 mapped outcomes and 515 deterministic items.
- Country-specific courses default to their canonical language when no learner
  override is supplied.
