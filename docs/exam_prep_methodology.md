# FastLearn Exam Prep Methodology

**Status:** curriculum and product methodology for the planned Exam Prep area.
It describes the standards for content before courses are published; it is not
an official UKiset, GCSE awarding-body, or College Board product.

FastLearn teaches through a guided loop: establish the learner's starting
point, teach one small idea clearly, practise it with feedback, then return to
it in a mixed and timed context. Exam Prep uses that loop without presenting
practice as a replica of, endorsement by, or score prediction for any exam.

## Table of contents

1. [Scope and course structure](#scope-and-course-structure)
2. [General FastLearn learning methodology](#general-fastlearn-learning-methodology)
3. [Authoring, quality and accessibility](#authoring-quality-and-accessibility)
4. [Assessment, feedback and adaptivity](#assessment-feedback-and-adaptivity)
5. [UKiset preparation](#ukiset-preparation)
6. [GCSE preparation](#gcse-preparation)
7. [Digital SAT preparation](#digital-sat-preparation)
8. [Public samples, intellectual property and provenance](#public-samples-intellectual-property-and-provenance)
9. [Evaluation and release gates](#evaluation-and-release-gates)
10. [Delivery order and change control](#delivery-order-and-change-control)
11. [Reference links](#reference-links)

## Scope and course structure

Exam Prep is a distinct product area, separate from the general student
catalogue from its first release. A learner may use both areas, but exam goals,
timed practice, readiness indicators and progress reports must never distort
the guided learning journeys used by the wider catalogue.

The first release scope is:

- **UKiset 9–11:** vocabulary, reading for meaning, foundational mathematics,
  verbal reasoning and introductory non-verbal reasoning.
- **UKiset 11–13:** more complex verbal, mathematical and non-verbal
  reasoning, plus academic-English confidence.
- **UKiset 13–16:** demanding reasoning, data handling, multi-step maths and
  academic-English practice suitable for older applicants.
- **GCSE Mathematics:** board-neutral common core, with separate Foundation
  and Higher pathways from launch.
- **GCSE English Language:** board-neutral reading and writing skills, with
  distinct comprehension, analysis and composition routes.
- **GCSE Combined Science:** board-neutral biology, chemistry and physics,
  including working scientifically, practical-method reasoning and data
  interpretation.
- **Digital SAT:** Reading and Writing and Mathematics skill practice and
  fixed-difficulty mini mocks first; adaptive practice is a later, explicitly
  labelled capability.

The existing England-first science pathway remains available outside Exam Prep:
Primary Science is the beginner course, Chemistry Fundamentals supports the
KS3–GCSE bridge, and Advanced Chemistry reaches A-level and broad first-year
university foundations. English and Estonian are the first supported languages;
additional languages are introduced only after subject and assessment review.

## General FastLearn learning methodology

### 1. Start with a light diagnostic

The first interaction samples a small number of skills, confidence statements
and learner goals. It is not an entrance decision, an intelligence judgement,
or an exam-score estimate. The app uses it to choose a sensible first lesson
and to avoid making a learner repeat material they can already demonstrate.

### 2. Teach one observable idea at a time

Each guided lesson states a learner-friendly goal, gives a short explanation,
then asks for an action or explanation. A worked example makes the method
visible before independent practice. Feedback names the specific misconception
or missing step and offers the next smallest useful action rather than merely
showing a final answer.

For science and chemistry, visual models appear where they make an otherwise
invisible relationship easier to understand: particle movement, a reaction
model, an atom, a molecule, graph or measurement. Web lessons can use
interactive 3D molecular views from the start; mobile uses the best equivalent
accessible renderer supported by Flutter, with a labelled 2D/text fallback.
Every visualization has a learning purpose, an accessible description and a
task that can be completed without relying on colour, animation or WebGL.

### 3. Practise from supported to independent

Practice advances through four modes:

1. **Notice:** identify a feature in an example, diagram, source or model.
2. **Rehearse:** complete one constrained step with a hint or scaffold.
3. **Apply:** solve a new, original item without the scaffold.
4. **Transfer:** use the skill in a mixed, timed or unfamiliar context.

The app interleaves older skills with new ones and schedules brief retrieval
after a delay. A learner can revisit the explanation at any time; a timed mock
never removes their access to a clear learning route afterwards.

### 4. Make progress understandable

Progress is reported by skill evidence, not by a vague percentage alone:
what was attempted, what is secure, what needs another retrieval and what the
next recommended activity is. Confidence is collected separately from
correctness so that overconfidence and uncertainty can be addressed kindly.

## Authoring, quality and accessibility

All assessed items are original FastLearn material. An item has a skill tag,
learning objective, age/course band, difficulty rationale, valid answer set,
explanation, common-error notes, accessibility review and provenance record.
Subject reviewers check factual accuracy, language level, fairness and whether
the claimed skill is actually what the question measures.

Question sets include multiple representations: short text, diagrams, tables,
graphs and structured response. They avoid needless cultural knowledge,
ambiguous wording, inaccessible colour-only cues and trick wording. Any source
passage, diagram or data set is either newly authored, openly licensed with
attribution, or used through a documented permission.

English is the source version for high-stakes assessment wording. Estonian is
translated and reviewed by a subject-aware linguist; translations preserve the
skill being assessed rather than word-for-word phrasing. A translation must not
accidentally make an item easier, harder or scientifically different. Learners
can obtain simple language support while practising a concept, but modes that
are intended to model a language assessment state clearly which support is
enabled.

## Assessment, feedback and adaptivity

Short diagnostics and skill practice are formative: their job is to improve
the next lesson. Mini mocks are summative practice: they use a fixed blueprint,
fixed difficulty band, clear time guidance and a post-mock review. They do not
claim to reproduce an official test, produce an official score or predict an
admissions decision.

For constructed responses, marking distinguishes method, evidence and final
answer. Feedback first identifies the strongest completed step, then the one
change most likely to improve the response. A correct answer with an unsafe,
unsupported or impossible explanation is not treated as fully secure.

Adaptive practice is deliberately phased:

- **Launch:** learners select or are offered a transparent fixed difficulty;
  mini mocks remain fixed and comparable.
- **Calibration:** collect enough reviewed response evidence to validate item
  difficulty, fairness and skill tags.
- **Later adaptive mode:** vary the next practice item within a stated skill
  and difficulty range, explain the recommendation, and always allow a learner
  to choose an easier, standard or harder route.

No adaptive algorithm is presented as an official UKiset, GCSE or SAT scoring
engine. Changes in practice difficulty are not a claim about exam performance.

## UKiset preparation

UKiset describes itself as an online assessment of academic potential and
English proficiency for applicants to UK independent education. Its published
administration material describes a 40–45 minute reasoning component spanning
verbal, mathematical and non-verbal reasoning; candidates can use blank paper
and a pen for the mathematics part. FastLearn uses those public capability
categories as a planning reference, not as permission to recreate the test.

### Course bands and learner experience

The 9–11, 11–13 and 13–16 courses are separate from the outset. They share a
common skill vocabulary so progress can be understood across bands, but their
reading load, mathematical complexity, distractors, time pressure and visual
reasoning tasks are independently authored. A learner moving bands receives a
brief bridge diagnostic rather than being silently moved to a harder course.

Each course has four strands:

- verbal reasoning and precise vocabulary;
- mathematics reasoning, including multi-step thinking and data where
  appropriate to the band;
- non-verbal and spatial reasoning using original figures; and
- academic English: understanding an instruction, explaining a choice and
  reading efficiently.

The practice route is guided skill work, mixed sets, then short fixed-length
reasoning sessions. A session may suggest using paper for working, but it does
not imitate a secure test environment. Results report the demonstrated
practice skills and recommended next lessons, never a UKiset result, percentile
or school-admission prediction.

Prominent external-resource links lead learners and families to the official
[UKiset test-administration information](https://ukiset.com/test-administration/)
and [UKiset welcome guide](https://ukiset.com/wp-content/uploads/2023/09/UKiset-Welcome-Guide-FINAL.pdf).
Those pages are the source of truth for registration, current conditions and
what an official assessment involves.

## GCSE preparation

GCSE content is board-neutral. The Department for Education's published
subject-content collections establish the common knowledge, understanding and
skills that qualifications must cover, while exam boards differ in assessment
language, paper design and optional content. FastLearn teaches the common core
and does not imply alignment to a specific awarding body or guarantee a grade.

### Mathematics: separate Foundation and Higher from launch

Foundation and Higher are distinct course pathways, with shared skills linked
where appropriate. Both teach number, ratio/proportion, algebra, geometry and
measures, probability and statistics through deliberate progression. Higher
adds the depth, generalisation and multi-step reasoning appropriate to that
route; Foundation does not become a shortened or disguised Higher course.

Practice includes calculation fluency, method selection, mathematical
reasoning, proof/justification where appropriate, graphs and interpretation of
data. A review identifies whether an error came from notation, calculation,
method choice or interpretation.

### English Language

English Language is organised by transferable skills: locating and inferring
meaning, analysing writers' choices, comparing sources, planning, crafting a
response, technical accuracy and editing. Texts and prompts are newly authored
or appropriately licensed. The app teaches command words and response
structure without copying board papers or using copyrighted extracts without
permission.

### Combined Science

Combined Science is arranged as biology, chemistry, physics and working
scientifically. Lessons connect content knowledge with interpreting methods,
variables, safety, units, graphs, uncertainties and conclusions. Chemistry
uses guided models and interactive visualisations for particles, atoms,
bonding and reactions, but does not simulate unsafe practical work as an
instruction to perform it unsupervised.

Foundation and Higher routes are separate for Combined Science as well. Shared
concepts retain a consistent explanation; the assessment demand, calculation,
application and independence of reasoning are adjusted rather than simply
adding difficult vocabulary.

Prominent official links should take a learner to the
[DfE GCSE subject-content collection](https://www.gov.uk/government/collections/gcse-subject-content)
and to the relevant current awarding-body specification and sample-materials
page. They are reference resources, not content imported into FastLearn.

## Digital SAT preparation

The Digital SAT course is a separate US-general route, initially split into
Reading and Writing and Mathematics. College Board describes the current
digital format as two modules in each section: Reading and Writing is 64
minutes with 54 questions, and Mathematics is 70 minutes with 44 questions.
The course can explain this public format and link to official practice, but
does not reproduce official questions, score scales or adaptive logic.

### First-release sequence

1. **Skill practice:** short, guided Reading and Writing and Mathematics
   activities tagged to a narrow skill.
2. **Fixed-difficulty mini mocks:** transparent easy, standard and stretch
   sets with consistent timing, original items and an evidence-based review.
3. **Mixed review:** retrieval and interleaving across skills before a learner
   increases time pressure.

The later adaptive mode is contingent on item calibration and review. It must
clearly say that it adapts *practice difficulty*, not an official SAT module;
the learner can see and override the proposed level. Full official practice is
linked prominently through [College Board's official practice tests](https://satsuite.collegeboard.org/practice/practice-tests)
and [Student Question Bank](https://satsuite.collegeboard.org/practice/student-question-bank),
not copied into the product.

## Public samples, intellectual property and provenance

Publicly available sample questions, mark schemes and practice tests are useful
research material for understanding a qualification's published scope, command
words, response format, accessibility and mark allocation. They are not a
source pool for FastLearn questions.

The authoring rule is: **extrapolate the capability, never copy, lightly
rewrite or reverse-engineer the item.** Authors create a new context, data,
figures, wording, answer path and distractors. No official question, sample
answer, proprietary passage, diagram, image or close paraphrase is embedded in
the course. Links can send learners to official resources so that they can use
those materials at their source.

Every item records its own origin and review history. Similarity review is a
release gate, particularly for items inspired by a common public format. If an
item's independence cannot be demonstrated, it is removed or rewritten from a
fresh learning objective.

## Evaluation and release gates

Student-learning evaluation combines deterministic contracts with an LLM judge
where judgement of a free-text explanation is genuinely needed. Ground-truth
fixtures cover course/module structure, answer grading, public answer-key
privacy and portable visualisation specifications. The offline judge evaluates
age-appropriate explanations against a supplied reference, required ideas and
prohibited claims.

The judge is configured through `JUDGE_LLM` (default `gpt-5.1`) and wrapped by
LangChain structured output. `OPENAI_API_KEY` is stored only as a local or
deployment secret; it is never committed, shown in a report or exposed to the
client. A missing key is marked as skipped; a judge request failure is visible
as a failed result. Scheduled reports are introduced only after the local
baseline is accepted and the report-retention/access policy is set.

Before a course or substantial item update is released, the required gates are:

- deterministic tests for curriculum and grading contracts;
- student-API test confirming answer keys remain private;
- visualisation validation and an accessible non-WebGL route;
- subject, language and originality review;
- representative learner-path and mobile checks; and
- regression report review, including LLM-judge failures where configured.

## Delivery order and change control

1. Publish this methodology and the landing-page link.
2. Build the three UKiset course bands with original diagnostics, guided skills
   and fixed mini mocks.
3. Build GCSE Mathematics, English Language and Combined Science with separate
   Foundation/Higher pathways and board-neutral coverage maps.
4. Add SAT skill practice and fixed-difficulty mini mocks.
5. Calibrate authored items, then evaluate whether transparent adaptive
   practice is warranted.

The methodology is reviewed whenever an official provider changes a public
format or curriculum reference, when item analysis detects bias or poor
calibration, or when a learner-support feature could change what an item
measures. The linked official pages, rather than this document, remain the
authoritative source for registrations, current exam conditions and scoring.

## Reference links

- [UKiset: about the assessment](https://ukiset.com/about-ukiset/)
- [UKiset: test administration](https://ukiset.com/test-administration/)
- [UKiset welcome guide (PDF)](https://ukiset.com/wp-content/uploads/2023/09/UKiset-Welcome-Guide-FINAL.pdf)
- [Department for Education: GCSE subject content](https://www.gov.uk/government/collections/gcse-subject-content)
- [College Board: SAT practice tests](https://satsuite.collegeboard.org/practice/practice-tests)
- [College Board: SAT structure](https://satsuite.collegeboard.org/sat/whats-on-the-test)
- [College Board: Student Question Bank](https://satsuite.collegeboard.org/practice/student-question-bank)
