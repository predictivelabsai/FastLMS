# FastLearn Platform Guide

**Published:** 2026-09-04  
**Platform:** [https://fastlearn.fun](https://fastlearn.fun)  
**Open-source foundation:** [FastLMS](https://lms.fastsme.com)  
**Interface and catalogue languages:** English, Estonian, Lithuanian and Spanish<br>
**Language-learning targets:** English, Spanish, French, German, Italian, Portuguese, Mandarin Chinese, Arabic, Japanese and Hindi

This guide explains how students, teachers and the administrator use FastLearn, including role-based access, learning-time reporting and configurable adaptive learning.

Screenshots were reviewed on 2026-09-04. Learner screens come from the current FastLearn product tour; teacher screens use a controlled documentation account on the same application build. No production learner data is shown.

## 1. Platform overview

FastLearn provides structured courses, focused lessons, quizzes, visible progress and an AI Tutor. The public product runs at `fastlearn.fun`; FastLMS remains the open-source implementation and developer-facing reference.

![FastLearn landing page](img/fastlearn-platform-guide/01-home.png)

### Platform capabilities

- Ten published courses across programming, mathematics, science, language, geography and creative writing.
- Course modules, lessons, quizzes, XP, streaks, badges and a leaderboard.
- An AI Tutor grounded in the lesson being studied.
- English, Estonian, Lithuanian and Spanish interface and course content.
- Native-to-target language practice across ten major languages.
- Google OAuth and password authentication.
- Enforced admin, teacher and student permissions.
- Team invitations and teacher/course assignments.
- Active learning-time measurement.
- Linear and adaptive learning strategies.
- Teacher-reviewed generation for question variants and remedial or extension lessons.

## 2. Roles and permissions

| Capability | Admin | Teacher | Student |
|---|:---:|:---:|:---:|
| Browse all published courses | Yes | Yes | Yes |
| Learn from any published course | Yes | Yes | Yes |
| See own progress and active time | Yes | Yes | Yes |
| Create and edit assigned courses | Yes | Yes | No |
| Invite students to the platform | Yes | Yes | No |
| Assign students to a teacher-owned course | Yes | Yes | No |
| View learners in assigned courses | Yes | Yes | No |
| Manage all users, roles and courses | Yes | No | No |
| Change users between teacher and student roles | Yes | No | No |

`kaljuvee@gmail.com` is the sole administrator. During signup, a new user chooses **Student** or **Teacher**, and the same choice is carried through password registration or Google SSO. Existing accounts keep their saved role when signing in again. Invitation roles take precedence, and no signup option can create another administrator. The administrator can later move other accounts between student and teacher.

### Access principles

- Permissions are checked by the server, not merely by hiding navigation links.
- Teachers manage only courses assigned to them and only see learner records relevant to those courses.
- Teachers may invite a student to the whole platform. The invitation does not restrict the student to one course.
- Students can explore every published course.
- A course assigned by a teacher or administrator displays an **Assigned** tag. Self-selected courses remain available without that tag.
- Role changes, invitations and assignments are written to an audit log.

## 3. Signing in

Open [fastlearn.fun](https://fastlearn.fun), select **Sign In**, then choose **Create your account**.

![FastLearn account creation with Student and Teacher choices](img/fastlearn-platform-guide/02-sign-in.png)

Students and teachers may use their email and password. Google SSO is available at [fastlearn.fun/auth/google](https://fastlearn.fun/auth/google); it returns the authenticated user to the FastLearn application. The registered callback is:

```text
https://fastlearn.fun/auth/google/callback
```

The original FastLMS callback remains registered separately. Never share a password, OAuth code or recovery token with another user.

On **Create account**, select **Student** to learn and explore courses or **Teacher** to teach and manage learners. The selected role also applies when **Continue with Google** is used from that signup screen. Returning Google users retain their existing database role.

## 4. Student guide

### 4.1 Browse the catalogue

Select **Courses** in the left navigation. Course cards show subject, difficulty, description and progress where applicable.

![Student course catalogue](img/fastlearn-platform-guide/03-student-course-catalogue.png)

An **Assigned** tag distinguishes a teacher/admin assignment from a course the student chose independently. Assignment is a recommendation or curriculum requirement; it does not hide the rest of the catalogue.

### 4.2 Open a course and follow its path

Select a course card to see its modules, lessons and overall progress. In the default **linear** strategy, lessons follow the teacher-defined order.

![Student course path](img/fastlearn-platform-guide/04-student-course-path.png)

Select a lesson title to begin. A completed indicator appears beside finished lessons, and the progress bar updates as the course advances.

### 4.3 Study a lesson

Lessons contain explanations, examples, practical material and optional media. The header shows expected duration and XP.

![Student lesson](img/fastlearn-platform-guide/05-student-lesson.png)

Use the actions at the end of a lesson to:

1. Mark the lesson complete.
2. Open its quiz, when provided.
3. Ask the AI Tutor for help in the current context.
4. Continue to the next recommended lesson.

### 4.4 Complete quizzes

Choose one answer for each question and submit the quiz. FastLearn displays the score, pass status, correct answers and explanations.

![Student quiz](img/fastlearn-platform-guide/06-student-quiz.png)

Quiz attempts contribute to progress and, in adaptive mode, to the learner's current difficulty and recommendation state. An unsuccessful attempt is evidence for extra support—not a punishment or a permanent label.

### 4.5 Use the AI Tutor

Open **AI Tutor** from the navigation or from a lesson. When opened from a lesson, the tutor receives the relevant lesson context. Suggested prompts can request a simpler explanation, a practical example or a short knowledge check.

![AI Tutor in Estonian](img/fastlearn-platform-guide/07-student-ai-tutor.png)

The tutor responds in the selected interface language unless the student asks for another language. Students should not submit passwords, private identifiers or information they are not permitted to share.

### 4.6 Understand active learning time

FastLearn counts active learning in three contexts:

- reading or interacting with a lesson;
- answering a quiz;
- using the AI Tutor within a course.

The browser sends a heartbeat every 30 seconds. Time pauses immediately when the tab is hidden and after 90 seconds without keyboard, pointer or touch activity. Returning to the page starts a new active interval. This prevents a page left open overnight from being counted as study time.

Students see their total active time on their profile. Teachers see the lesson, quiz and AI Tutor split for their own courses. Historical time from before tracking was enabled cannot be reconstructed reliably.

### 4.7 Understand adaptive recommendations

Courses remain linear unless a teacher enables **adaptive** mode.

In adaptive mode:

- core lessons remain mandatory;
- prerequisites are always respected;
- optional lessons may be skipped;
- weak performance can insert an easier question set and a remedial lesson;
- sustained strong performance can raise question difficulty and prioritize an extension lesson;
- the student can see why a recommendation changed;
- a teacher can override the recommendation or restore the standard sequence.

The default rules are:

| Evidence | Adjustment |
|---|---|
| Recent accuracy below 60% | Reduce question difficulty by one level and queue relevant remedial material |
| Accuracy above 85% across two assessments | Increase difficulty by one level and prioritize an extension activity |
| Accuracy between those thresholds | Keep the current level |

FastLearn never changes by more than one difficulty level at a time and falls back to the nearest approved material when an exact match is unavailable.

### 4.8 Learn another language

Open **Language learning** in the left navigation. Choose the language the student already speaks, the target language and a daily practice goal.

![Native-to-target language practice](img/fastlearn-platform-guide/13-language-learning.png)

#### Supported language pairs

The target-language engine currently supports:

- English;
- Spanish;
- French;
- German;
- Italian;
- Portuguese;
- Mandarin Chinese;
- Modern Standard Arabic;
- Japanese;
- Hindi.

Estonian and Lithuanian are also available as native starting languages. This lets a student begin with familiar instructions even when the target language uses another script.

#### How practice works

Each practice turn follows an audio-first recall loop:

1. Read the meaning in the native language.
2. Anticipate and say the target expression aloud before revealing it.
3. Reveal the target expression and its romanisation where appropriate.
4. Listen to browser-generated pronunciation.
5. Rate recall as **Again**, **Hard** or **Got it**.
6. Let FastLearn schedule the next appearance.

The initial dictionary contains 30 frequency-informed words and functional expressions aligned across every supported language. Difficult expressions return sooner. Successful recall expands from short in-session intervals to hours, days and months. This is a Pimsleur-style use of anticipation and graduated interval recall with original content; FastLearn does not reproduce proprietary Pimsleur lessons or recordings.

## 5. Teacher guide

### 5.1 Manage assigned courses

Open **Manage courses** to review course title, subject, difficulty and publication status.

![Teacher course management](img/fastlearn-platform-guide/08-teacher-manage-courses.png)

This list contains only courses owned by or assigned to the teacher. The administrator retains access to every course.

### 5.2 Build and publish a course

Open **Course setup**. The authoring flow has five stages:

1. Create or select a course.
2. Add modules.
3. Add lessons.
4. Create quizzes and questions.
5. Review and publish.

![Teacher course configuration](img/fastlearn-platform-guide/09-teacher-course-setup.png)

Draft courses remain invisible to students until published. Teachers should preview titles, lesson order, answer options and translations before publication.

### 5.3 Invite and assign students

Open **Team**, enter the student's email and send an invitation through the existing Postmark service.

![Team invitations, roles and course assignments](img/fastlearn-platform-guide/10-team.png)

- Invitations do not expire.
- Each invitation is single-use and can be revoked.
- Accepting an invitation gives the learner access to the whole platform.
- The teacher may then assign the learner to one of the teacher's courses.
- An administrator may assign any learner to any course.
- Assigned courses display an **Assigned** tag in the learner catalogue.

Teachers cannot change a user's platform role. The administrator can change users between student and teacher roles and can grant teachers access to courses.

### 5.4 Configure a learning strategy

Open **Manage courses**, then select **Learning strategy** for a course.

![Adaptive strategy and generated drafts](img/fastlearn-platform-guide/11-adaptive-strategy.png)

**Linear** preserves the normal module and lesson order. For **Adaptive**, configure:

- low- and high-performance thresholds;
- whether recommendations may reorder the path;
- whether FastLearn should generate support lessons;
- lesson type: `core`, `remedial` or `optional`;
- question difficulty: easier, standard or harder.

Core lessons determine required course completion. Remedial and optional extension material can be inserted or prioritized according to performance; explicit prerequisites remain ahead of dependent lessons.

### 5.5 Generate material for approval

A teacher may request generated material for a selected lesson. FastLearn produces:

- easy, standard and challenging question variants;
- answer options, correct answer and explanation;
- remedial lesson drafts for common misconceptions;
- extension lesson drafts for learners ready to move further;
- English, Estonian, Lithuanian and Spanish versions.

Generated material always starts as **Pending**. Before approval, the teacher should verify factual accuracy, difficulty, age appropriateness, wording, translations and that the correct answer appears exactly among the answer options. Only approved variants become lessons or quiz questions.

### 5.6 Review learner progress and time

Teachers see reporting only for learners in their assigned courses. The administrator sees platform-wide reporting.

![Learning progress, difficulty and active-time report](img/fastlearn-platform-guide/12-learning-reports.png)

Reports include:

- active time by course, split across lessons, quizzes and AI Tutor;
- completed core lessons;
- average quiz score;
- current adaptive difficulty;
- the learner and course associated with each total.

Time is an engagement signal, not proof of understanding. It should be considered alongside assessment evidence and teacher observation.

## 6. Administrator guide

The administrator uses **Team** to:

- invite students or teachers;
- change student and teacher roles;
- assign teachers to courses;
- assign any student to any course;
- revoke unused invitations;
- view platform-wide learning and time reports.

Role changes take effect on the next authorized request. The server will reject unauthorized direct URLs and form submissions even if a user attempts to bypass the interface.

## 7. Adaptive-learning decision process

The adaptive engine is deterministic and explainable:

1. Record the student's individual answers and assessment score.
2. Update the learner's course difficulty and consecutive-high-score count.
3. Compare performance with the course thresholds.
4. Move at most one difficulty level.
5. Select the nearest approved question difficulty and keep prerequisites ahead of dependent lessons.
6. Keep all core lessons, insert remedial work after difficulty, or prioritize extension work after sustained success.
7. Store the decision, evidence and rule used.
8. Show the student a plain-language reason and make the decision visible to the teacher.

If no approved material exists at the selected level, FastLearn uses the closest available approved question or returns to the teacher-defined linear path.

## 8. Language support

Use the flag selector in the navigation to switch between:

- English;
- Eesti;
- Lietuvių;
- Español.

![FastLearn landing page in Spanish](img/fastlearn-platform-guide/14-spanish-demo.png)

The selected language applies to navigation, course and lesson content, quizzes, answer explanations, AI Tutor prompts and generated drafts. Difficulty changes must never silently switch the learner's language.

The interface language and language-learning pair are independent. For example, a student can use the Spanish interface while learning Mandarin Chinese from English, or use the Estonian interface while learning Spanish from Estonian.

## 9. Data and audit records

FastLearn retains:

- user role and status;
- invitations and their sender, recipient, use or revocation state;
- teacher/course and student/course assignments;
- active learning sessions and aggregated durations;
- quiz attempts and individual responses;
- adaptive difficulty, recommendations and their assessment evidence;
- generated content versions and teacher approval decisions.
- native and target language preferences, recall ratings and next-due intervals.

Access follows least privilege: students see their own data, teachers see relevant assigned-course data, and administrators see platform-wide records. Passwords and OAuth tokens are never part of learning analytics.

## 10. Quick reference

### Student

1. Sign in and choose a language.
2. Open an assigned course or explore the catalogue.
3. Work through the recommended lesson.
4. Complete its quiz.
5. Use AI Tutor when an explanation is unclear.
6. Review progress, active time and adaptive recommendations.
7. Open **Language learning** to practise a chosen target language from the student's native language.

### Teacher

1. Open **Manage courses**.
2. Build content through **Course setup**.
3. Preview and publish the course.
4. Use **Team** to invite students and assign them to teacher-owned courses.
5. Configure linear or adaptive learning.
6. Generate variants, review every draft and approve suitable material.
7. Monitor progress, adaptive difficulty and active time.

### Support

- Product: [https://fastlearn.fun](https://fastlearn.fun)
- Open-source project: [https://github.com/predictivelabsai/FastLMS](https://github.com/predictivelabsai/FastLMS)
- FastLMS reference: [https://lms.fastsme.com](https://lms.fastsme.com)
