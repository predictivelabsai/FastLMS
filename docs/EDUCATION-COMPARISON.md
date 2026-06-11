# FastLMS vs Frappe — comparison & suggested additions

Part of the [`fasthtml-oss-migrations`](https://github.com/predictivelabsai/fasthtml-oss-migrations)
analysis. Two upstream Frappe apps are relevant; they cover **different** halves
of "education", and FastLMS sits mostly in the first:

| Upstream | What it is | Doctypes | FastLMS coverage |
|---|---|---|---|
| **`frappe/lms`** | Course-delivery platform | 69 | **strong** — this is FastLMS's domain |
| **`frappe/education`** | School/college administration | 74 | **gap** — barely touched |

## What FastLMS already has 🟢

Tables: `users · courses · modules · lessons · quizzes · quiz_questions ·
lesson_progress · quiz_attempts · badges · user_badges · enrolments ·
discussions · chat_messages`.

This maps cleanly onto the **`frappe/lms`** core:

| FastLMS | frappe/lms equivalent |
|---|---|
| courses / modules / lessons | `LMS Course` / `Course Chapter` / `Course Lesson` |
| quizzes / quiz_questions / quiz_attempts | `LMS Quiz` / `LMS Question` / `LMS Quiz Submission` |
| lesson_progress | `LMS Course Progress` |
| enrolments | `LMS Enrollment` |
| badges / user_badges (+ XP, streaks, levels) | `LMS Badge` / `LMS Badge Assignment` (gamification is a FastLMS extra) |
| discussions | `Course Lesson`/topic comments |
| chat_messages (AI tutor) | *(not upstream — a FastLMS original)* |

FastLMS also adds Duolingo-style **XP / levels / streaks / leaderboard** and an
**SSE-streaming AI tutor** that upstream lacks. So for course *delivery*, FastLMS
is at or beyond parity.

## Gaps vs `frappe/lms` (course platform) — near-term 🟡

Upstream `LMS` features FastLMS doesn't yet have, in rough priority:

1. **Batches / cohorts** — `LMS Batch`, `LMS Batch Enrollment`,
   `LMS Batch Timetable`, `Live Class`. Time-boxed cohort runs of a course with a
   schedule. *Add:* a `batches` + `batch_enrolments` + `batch_timetable` set and a
   cohort calendar view.
2. **Certificates** — `LMS Certificate`, `Certificate Request`,
   `Certificate Evaluation`. *Add:* issue a completion certificate (PDF via the
   pandoc/WeasyPrint pipeline already used elsewhere in the org) when a course hits 100%.
3. **Assignments** (vs quizzes only) — `LMS Assignment`,
   `LMS Assignment Submission`, evaluator flow. *Add:* free-text/file
   assignments with an evaluator-grading queue.
4. **Course reviews & ratings** — `LMS Course Review`. *Add:* per-course
   star rating + review list.
5. **Instructors / mentors** — `Course Instructor`, `Course Mentor Mapping`.
   *Add:* an instructor role distinct from author, shown on the course page.
6. **Programs** (course bundles / learning paths) — group courses into a path
   with ordering and combined progress.
7. **Payments / coupons** — `LMS Payment`, `LMS Coupon` (paid courses). Lower
   priority for a demonstrator.

## Gaps vs `frappe/education` (school admin) — the bigger opportunity ⚪

If FastLMS should also serve **schools/colleges** (not just self-serve courses),
these `frappe/education` capabilities are missing entirely. Each is a clean,
self-contained addition:

1. **Academic calendar** — `Academic Year`, `Academic Term`. Scopes everything
   below to a term. *Add:* `academic_years` / `academic_terms`.
2. **Students & guardians** — `Student`, `Guardian`, `Guardian Student`,
   `Student Group`. A first-class **Student** distinct from a generic learner,
   with guardian contacts and class/section grouping. *Add:* `students`,
   `guardians`, `student_groups` (FastLMS `users` stays for accounts).
3. **Program enrolment** — `Program`, `Program Enrollment`,
   `Program Enrollment Course`. Enrol a student into a *program* for a term, not
   just a single course.
4. **Formal assessment & grading** — `Assessment Plan`, `Assessment Criteria`,
   `Assessment Result`, `Grading Scale`, `Grading Scale Interval`. Gradebook with
   weighted criteria and letter grades — a step beyond auto-graded quizzes. *Add:*
   `grading_scales`, `assessments`, `assessment_results` → a **gradebook view**.
5. **Attendance** — `Student Attendance`, `Student Leave Application`. Per-session
   attendance register. *Add:* `attendance` + a register UI per student group.
6. **Fees & billing** — `Fee Structure`, `Fee Schedule`, `Fees`,
   `Payment Record`, `Fee Category`. Tuition/fees per program/term with a
   payment ledger. *Add:* `fee_structures`, `fees`, `fee_payments` → a **finance
   tab**. (Mirrors the activation/finance modules in FastClinic.)
7. **Course schedule / timetable** — `Course Schedule`, `Course Scheduling Tool`.
   Room/instructor/time slots → a weekly timetable grid.

## Recommended additions to FastLMS (concrete)

Phase the school-admin layer in without disturbing the existing learner UX:

```
# new tables (SQLite/Postgres) to add in db.py
academic_years(id, name, start, end, current)
academic_terms(id, year_id, name, start, end)
students(id, user_id, code, first_name, last_name, dob, group_id)
guardians(id, name, email, phone)
guardian_student(guardian_id, student_id, relation)
student_groups(id, name, term_id, program_id)          # class/section
programs(id, name, description)
program_courses(program_id, course_id, position)
program_enrolments(id, student_id, program_id, term_id, status)
grading_scales(id, name) / grading_intervals(scale_id, grade, threshold)
assessments(id, course_id, term_id, name, max_score, weight, scale_id)
assessment_results(id, assessment_id, student_id, score, grade)
attendance(id, student_id, group_id, date, status)
fee_structures(id, program_id, term_id, amount, category)
fees(id, student_id, fee_structure_id, due_date, amount, status)
fee_payments(id, fee_id, paid_on, amount, method)
```

New left-nav sections to match: **School** (Students, Guardians, Groups,
Programs, Enrolments), **Academics** (Gradebook, Attendance, Timetable),
**Finance** (Fee structures, Fees, Payments). The existing **Learning** (courses,
lessons, quizzes, AI tutor) and **gamification** stay as-is — they become the
"course delivery" layer underneath the school-admin layer.

The **AI assistant** extends naturally: "who is at risk of failing this term?",
"show overdue fees", "summarise attendance for Group 9B" — grounded the same way
FastCRM grounds chat in a live data snapshot.

## Summary

- For **course delivery** (`frappe/lms`): FastLMS is at/above parity; add
  **batches, certificates, assignments, reviews** to close the gap.
- For **school administration** (`frappe/education`): FastLMS has a **large green
  field** — students/guardians, programs/enrolment, gradebook, attendance, and
  fees are the high-value additions, and each is a self-contained module.
