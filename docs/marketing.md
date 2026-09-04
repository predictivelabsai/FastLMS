# FastLearn marketing

## LinkedIn post — 4 September 2026

Brilliant.org, Duolingo, Khan Academy, and IXL are powerful. But children learn
differently—and families still have to fit someone else's curriculum and pace.

I built **FastLearn** for my daughters at the beginning of the school year. It
started with a simple question: what if every parent could personalise learning
for their own children instead of accepting one fixed path?

FastLearn is an open-source, AI-native learning platform for building that path.

A few things FastLearn does differently from incumbent learning platforms 👇

🧭 **Linear when it works, adaptive when it helps** — courses start with a clear
linear path. If a learner struggles, FastLearn can lower the difficulty by one
level, reorder upcoming work, and recommend remediation. After sustained
success, it can raise the challenge and suggest extension material.

✅ **AI proposes; a teacher or parent approves** — new lessons and questions are
reviewable drafts. Nothing enters the learning path without human approval.

🌍 **Learning in the language that fits the family** — the interface, courses,
questions, and generated material support English, Estonian, and Lithuanian.

🎓 **Assignment without a walled garden** — assigned courses are clearly marked,
while learners remain free to explore the full catalogue.

⏱️ **Measure active learning, not an open tab** — lesson, quiz, and AI Tutor time
uses visibility checks, 30-second heartbeats, and a 90-second inactivity pause.

💬 **A tutor that knows the lesson** — the AI Tutor receives the current lesson
as context and supports multiple model providers.

👥 **Designed for a learning team** — administrator, teacher, and student roles;
email invitations; assignments; scoped access; progress, assessment, and
active-time reports; and an audit trail.

The stack (open source and self-hostable):

• FastHTML + HTMX — a Python-first, server-rendered interface without a
JavaScript framework  
• PostgreSQL — courses, progress, adaptive state, learning time, and audit data  
• Multi-provider AI — Grok, OpenAI, or Claude through one configuration  
• Google SSO + Postmark — familiar sign-in and platform invitations  
• Docker + Coolify — automatic deployment from GitHub

If you are a parent, fork it and personalise the subjects, examples, language,
difficulty, and pace for your own children. If you are a teacher or builder,
help us make adaptive learning more transparent, human-guided, and accessible.

🌐 Live demo: https://fastlearn.fun  
🎬 Animated walkthrough: https://fastlearn.fun/static/fastlearn-demo.gif  
📘 Platform guide (PDF): https://github.com/predictivelabsai/FastLMS/blob/main/docs/fastlearn_platform_guide.pdf  
⭐ Source code: https://github.com/predictivelabsai/FastLMS

#OpenSource #EdTech #AdaptiveLearning #AI #GenAI #Education #PersonalisedLearning
#FastHTML

## Publishing assets

- Animated GIF in this repository: [`static/fastlearn-demo.gif`](../static/fastlearn-demo.gif)
- Public animated GIF: <https://fastlearn.fun/static/fastlearn-demo.gif>
- Platform guide source: [`docs/fastlearn_platform_guide.md`](fastlearn_platform_guide.md)
- Platform guide PDF: [`docs/fastlearn_platform_guide.pdf`](fastlearn_platform_guide.pdf)
- Live demo: <https://fastlearn.fun>
- GitHub repository: <https://github.com/predictivelabsai/FastLMS>
