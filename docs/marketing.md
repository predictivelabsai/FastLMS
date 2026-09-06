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
path. Struggle can trigger easier questions and remediation; sustained success
can raise the challenge and suggest extension material.

✅ **AI proposes; a teacher or parent approves** — new lessons and questions are
reviewable drafts. Nothing enters the learning path without human approval.

📚 **Useful subjects already included** — Python, machine learning, FastHTML,
mathematics, physics, biology, chemistry, English language and literature,
geography, creative writing, art history, music history, visual-art principles,
music principles, and a child-focused Chess Foundations course.

♞ **Chess is learned on the board, inside the conversation** — children aged
3–12 meet coordinates, rooks, bishops, queens, and knights through guided
selection, placement, route, and capture puzzles. Grading stays server-side;
mistakes bring a gentler retry while success advances the lesson.

🗣️ **Language learning from your native language** — choose among ten targets:
English, Spanish, French, German, Italian, Portuguese, Mandarin Chinese, Arabic,
Japanese, and Hindi. A frequency-informed dictionary introduces useful speech;
Pimsleur-style anticipation, listening, and graduated recall bring difficult
expressions back sooner and confident answers at expanding intervals.

🌍 **A multilingual demo** — the interface, courses, questions, and generated
material are available in English, Estonian, Lithuanian, and Spanish.

⏱️ **Measure active learning, not an open tab** — lesson, quiz, and AI Tutor time
uses visibility checks, 30-second heartbeats, and a 90-second inactivity pause.

💬 **A tutor that knows the lesson** — New Chat receives the current lesson
as context and supports multiple model providers.

🔌 **An API for families, schools, and builders** — localized published
curriculum and answer-safe exercises are public; bearer-protected endpoints
cover assignments, enrolment, progress, recorded practice, and chat history.
Swagger and ReDoc are included with the live deployment.

The stack (open source and self-hostable):

• FastHTML + HTMX — Python-first, server-rendered UI
• PostgreSQL — courses, progress, adaptive state, learning time, and audit data  
• python-chess — authoritative guided-board validation without exposing answers
• Multi-provider AI — Grok, OpenAI, or Claude through one configuration  
• Google SSO + Postmark — familiar sign-in and platform invitations  
• Docker + Coolify — automatic deployment from GitHub

If you are a parent, fork it and personalise the subjects, examples, language,
difficulty, and pace for your children. If you are a teacher or builder, help
make adaptive learning transparent, human-guided, and accessible.

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
