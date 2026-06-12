"""Seed FastLMS with demo data — courses, modules, lessons, quizzes, badges.

Usage:
    python seed.py          # seed all demo data
    python seed.py --reset  # drop and recreate schema first
"""

from __future__ import annotations

import argparse
import json

import sqlalchemy as sa
from dotenv import load_dotenv

import db

load_dotenv()

S = db.SCHEMA

# ---------------------------------------------------------------------------
# Badge definitions
# ---------------------------------------------------------------------------

BADGES = [
    {"slug": "first-lesson", "name": "First Steps", "description": "Complete your first lesson", "icon": "🎯", "criteria_type": "lessons_completed", "criteria_value": 1},
    {"slug": "ten-lessons", "name": "Dedicated Learner", "description": "Complete 10 lessons", "icon": "📚", "criteria_type": "lessons_completed", "criteria_value": 10},
    {"slug": "fifty-lessons", "name": "Knowledge Seeker", "description": "Complete 50 lessons", "icon": "🧠", "criteria_type": "lessons_completed", "criteria_value": 50},
    {"slug": "streak-3", "name": "On Fire", "description": "Maintain a 3-day streak", "icon": "🔥", "criteria_type": "streak", "criteria_value": 3},
    {"slug": "streak-7", "name": "Week Warrior", "description": "Maintain a 7-day streak", "icon": "⚡", "criteria_type": "streak", "criteria_value": 7},
    {"slug": "streak-30", "name": "Month Master", "description": "Maintain a 30-day streak", "icon": "💎", "criteria_type": "streak", "criteria_value": 30},
    {"slug": "quiz-ace", "name": "Quiz Ace", "description": "Score 100% on a quiz", "icon": "🏆", "criteria_type": "quiz_score", "criteria_value": 100},
    {"slug": "xp-500", "name": "Rising Star", "description": "Earn 500 XP", "icon": "⭐", "criteria_type": "xp_total", "criteria_value": 500},
    {"slug": "xp-2000", "name": "Scholar", "description": "Earn 2000 XP", "icon": "🎓", "criteria_type": "xp_total", "criteria_value": 2000},
    {"slug": "xp-5000", "name": "Expert", "description": "Earn 5000 XP", "icon": "👑", "criteria_type": "xp_total", "criteria_value": 5000},
    {"slug": "course-complete", "name": "Graduate", "description": "Complete an entire course", "icon": "🎉", "criteria_type": "course_completed", "criteria_value": 1},
]

# ---------------------------------------------------------------------------
# Demo courses
# ---------------------------------------------------------------------------

COURSES = [
    {
        "title": "Python Fundamentals",
        "slug": "python-fundamentals",
        "description": "Master the basics of Python programming — variables, control flow, functions, data structures, and file I/O. Perfect for absolute beginners.",
        "category": "Programming",
        "difficulty": "beginner",
        "is_published": True,
        "modules": [
            {
                "title": "Getting Started",
                "lessons": [
                    {
                        "title": "What is Python?",
                        "content_md": """# What is Python?

Python is a high-level, interpreted programming language created by Guido van Rossum in 1991. It's known for its clean syntax and readability.

## Why Learn Python?

- **Beginner-friendly**: Clean syntax that reads like English
- **Versatile**: Web dev, data science, AI/ML, automation, scripting
- **Huge ecosystem**: Over 400,000 packages on PyPI
- **In-demand**: One of the most requested skills in tech

## Your First Program

```python
print("Hello, World!")
```

That's it! No boilerplate, no ceremony. This is what makes Python special.

## How Python Runs

Python is an **interpreted** language. Your code is executed line by line by the Python interpreter, unlike compiled languages (C, Java) that convert everything to machine code first.

> **Key takeaway**: Python prioritises developer productivity over raw execution speed. For most applications, this is the right trade-off.
""",
                        "xp_reward": 20,
                        "duration_min": 5,
                    },
                    {
                        "title": "Installing Python",
                        "content_md": """# Installing Python

## Check if Python is Already Installed

```bash
python3 --version
```

## Installation by Platform

### macOS
```bash
brew install python
```

### Ubuntu / Debian
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv
```

### Windows
Download from [python.org](https://python.org) and run the installer. **Check "Add Python to PATH"**.

## Virtual Environments

Always use a virtual environment for projects:

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\\Scripts\\activate     # Windows
```

## Verify Your Setup

```bash
python3 -c "import sys; print(f'Python {sys.version}')"
```

> **Tip**: Use `python3` explicitly on macOS/Linux to avoid accidentally using Python 2.
""",
                        "xp_reward": 15,
                        "duration_min": 10,
                    },
                ],
            },
            {
                "title": "Core Concepts",
                "lessons": [
                    {
                        "title": "Variables and Data Types",
                        "content_md": """# Variables and Data Types

## Variables

Python variables don't need type declarations:

```python
name = "Alice"       # str
age = 30             # int
height = 1.75        # float
is_student = True    # bool
```

## Common Data Types

| Type | Example | Description |
|------|---------|-------------|
| `str` | `"hello"` | Text |
| `int` | `42` | Whole numbers |
| `float` | `3.14` | Decimal numbers |
| `bool` | `True` / `False` | Boolean |
| `list` | `[1, 2, 3]` | Ordered, mutable sequence |
| `dict` | `{"key": "value"}` | Key-value mapping |
| `tuple` | `(1, 2, 3)` | Ordered, immutable sequence |
| `set` | `{1, 2, 3}` | Unordered unique elements |

## Type Checking

```python
x = 42
print(type(x))        # <class 'int'>
print(isinstance(x, int))  # True
```

## Type Conversion

```python
int("42")      # 42
str(42)        # "42"
float("3.14")  # 3.14
list("abc")    # ['a', 'b', 'c']
```
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                        "quiz": {
                            "title": "Variables & Types Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 30,
                            "questions": [
                                {
                                    "question_text": "What is the type of `x = 3.14`?",
                                    "options": ["int", "float", "str", "decimal"],
                                    "correct_answer": "float",
                                    "explanation": "Numbers with decimal points are `float` in Python.",
                                },
                                {
                                    "question_text": "Which data structure uses key-value pairs?",
                                    "options": ["list", "tuple", "dict", "set"],
                                    "correct_answer": "dict",
                                    "explanation": "Dictionaries (`dict`) store key-value pairs like `{'name': 'Alice'}`.",
                                },
                                {
                                    "question_text": "What does `type(True)` return?",
                                    "options": ["<class 'str'>", "<class 'int'>", "<class 'bool'>", "<class 'true'>"],
                                    "correct_answer": "<class 'bool'>",
                                    "explanation": "`True` and `False` are `bool` type in Python.",
                                },
                            ],
                        },
                    },
                    {
                        "title": "Control Flow",
                        "content_md": """# Control Flow

## If / Elif / Else

```python
temperature = 22

if temperature > 30:
    print("Hot!")
elif temperature > 20:
    print("Nice weather")
else:
    print("A bit chilly")
```

## For Loops

```python
# Iterate over a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# Range
for i in range(5):      # 0, 1, 2, 3, 4
    print(i)

# Enumerate (index + value)
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
```

## While Loops

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## List Comprehensions

```python
# Traditional
squares = []
for x in range(10):
    squares.append(x ** 2)

# Comprehension (Pythonic)
squares = [x ** 2 for x in range(10)]

# With filter
evens = [x for x in range(20) if x % 2 == 0]
```

> **Style tip**: Use comprehensions for simple transformations, regular loops for complex logic.
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                    },
                    {
                        "title": "Functions",
                        "content_md": """# Functions

## Defining Functions

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("Alice"))  # Hello, Alice!
```

## Default Arguments

```python
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

greet("Bob")              # Hello, Bob!
greet("Bob", "Hi there")  # Hi there, Bob!
```

## *args and **kwargs

```python
def flexible(*args, **kwargs):
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

flexible(1, 2, 3, name="Alice", age=30)
# Args: (1, 2, 3)
# Kwargs: {'name': 'Alice', 'age': 30}
```

## Lambda Functions

```python
square = lambda x: x ** 2
print(square(5))  # 25

# Often used with sorted, map, filter
names = ["Charlie", "Alice", "Bob"]
sorted(names, key=lambda n: len(n))  # ['Bob', 'Alice', 'Charlie']
```

## Type Hints (Python 3.9+)

```python
def add(a: int, b: int) -> int:
    return a + b
```

Type hints are optional and not enforced at runtime, but they help with readability and IDE support.
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                        "quiz": {
                            "title": "Functions Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 35,
                            "questions": [
                                {
                                    "question_text": "What keyword defines a function in Python?",
                                    "options": ["func", "function", "def", "fn"],
                                    "correct_answer": "def",
                                    "explanation": "Python uses `def` to define functions.",
                                },
                                {
                                    "question_text": "What does `*args` collect?",
                                    "options": ["Keyword arguments", "Positional arguments as a tuple", "A list", "A dictionary"],
                                    "correct_answer": "Positional arguments as a tuple",
                                    "explanation": "`*args` collects extra positional arguments into a tuple.",
                                },
                            ],
                        },
                    },
                ],
            },
        ],
    },
    {
        "title": "Machine Learning with scikit-learn",
        "slug": "ml-sklearn",
        "description": "Practical machine learning — from data preparation to model evaluation. Learn classification, regression, and clustering with scikit-learn.",
        "category": "Data Science",
        "difficulty": "intermediate",
        "is_published": True,
        "modules": [
            {
                "title": "Introduction to ML",
                "lessons": [
                    {
                        "title": "What is Machine Learning?",
                        "content_md": """# What is Machine Learning?

Machine learning is a subset of AI where systems learn patterns from data instead of being explicitly programmed.

## Three Types of ML

### 1. Supervised Learning
The model learns from labeled examples (input → output pairs).
- **Classification**: Predict a category (spam/not spam, cat/dog)
- **Regression**: Predict a continuous value (house price, temperature)

### 2. Unsupervised Learning
The model finds patterns in unlabeled data.
- **Clustering**: Group similar items (customer segments)
- **Dimensionality reduction**: Compress features (PCA, t-SNE)

### 3. Reinforcement Learning
The agent learns by interacting with an environment and receiving rewards.
- Game playing (AlphaGo)
- Robotics
- Recommendation systems

## The ML Workflow

```
Data Collection → Preprocessing → Feature Engineering → Model Training → Evaluation → Deployment
```

## When to Use ML

Use ML when:
- The problem has patterns in data
- You have enough labeled examples (supervised)
- Rules are too complex to hard-code
- The pattern may change over time

Don't use ML when:
- Simple rules work fine
- You don't have enough data
- The cost of errors is too high for a probabilistic system
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                    },
                    {
                        "title": "Setting Up scikit-learn",
                        "content_md": """# Setting Up scikit-learn

## Installation

```bash
pip install scikit-learn pandas numpy matplotlib
```

## Your First Model (5 lines)

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Load data
X, y = load_iris(return_X_y=True)

# Split into train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, predictions):.2%}")
```

## Key Concepts

- **Features (X)**: Input variables (measurements, attributes)
- **Target (y)**: What you're predicting
- **Train/Test split**: Use 80% for training, 20% for evaluation
- **Overfitting**: Model memorises training data, fails on new data
- **Underfitting**: Model is too simple to capture the pattern
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                    },
                ],
            },
        ],
    },
    {
        "title": "Building Web Apps with FastHTML",
        "slug": "fasthtml-web-apps",
        "description": "Build modern web applications using FastHTML — Python-first, HTMX-powered, no JavaScript framework required.",
        "category": "Web Development",
        "difficulty": "intermediate",
        "is_published": True,
        "modules": [
            {
                "title": "FastHTML Basics",
                "lessons": [
                    {
                        "title": "Why FastHTML?",
                        "content_md": """# Why FastHTML?

FastHTML lets you build full-stack web applications entirely in Python. No React, no Vue, no npm.

## The Problem with Modern Web Dev

Traditional stack: Python backend → JSON API → React/Vue/Svelte frontend → npm, webpack, TypeScript, state management...

**FastHTML stack**: Python backend → HTML responses → HTMX for interactivity.

## Key Ideas

1. **HTML is the API**: The server returns HTML fragments, not JSON
2. **HTMX handles interactivity**: Clicks, forms, and updates without writing JavaScript
3. **Server-side rendering**: No client-side state management
4. **Python all the way down**: Routes, templates, logic — all Python

## Hello World

```python
from fasthtml.common import *

app = FastHTML()

@app.get("/")
def home():
    return H1("Hello, World!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
```

## When to Use FastHTML

- Internal tools and dashboards
- Data apps and admin panels
- MVPs and prototypes
- Any app where you want to move fast without a JS framework
""",
                        "xp_reward": 25,
                        "duration_min": 10,
                    },
                ],
            },
        ],
    },
]


def seed_all():
    print("Bootstrapping schema...")
    db.bootstrap_schema()

    with db.begin() as conn:
        # Badges
        for b in BADGES:
            conn.execute(
                sa.text(f"""
                    INSERT INTO {S}.badges (slug, name, description, icon, criteria_type, criteria_value)
                    VALUES (:slug, :name, :description, :icon, :criteria_type, :criteria_value)
                    ON CONFLICT (slug) DO UPDATE SET name = :name, description = :description,
                        icon = :icon, criteria_type = :criteria_type, criteria_value = :criteria_value
                """),
                b,
            )
        print(f"  {len(BADGES)} badges seeded")

        # Demo instructor
        conn.execute(
            sa.text(f"""
                INSERT INTO {S}.users (email, password_hash, display_name, role)
                VALUES ('instructor@fastlms.dev', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Demo Instructor', 'instructor')
                ON CONFLICT (email) DO NOTHING
            """),
        )
        instructor = db.get_user_by_email(conn, "instructor@fastlms.dev")

        # Demo student
        conn.execute(
            sa.text(f"""
                INSERT INTO {S}.users (email, password_hash, display_name, role)
                VALUES ('student@fastlms.dev', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Demo Student', 'student')
                ON CONFLICT (email) DO NOTHING
            """),
        )

        # Courses
        for course_data in COURSES:
            modules = course_data.pop("modules", [])
            course_data["instructor_id"] = instructor["id"]
            conn.execute(
                sa.text(f"""
                    INSERT INTO {S}.courses (title, slug, description, category, difficulty, is_published, instructor_id)
                    VALUES (:title, :slug, :description, :category, :difficulty, :is_published, :instructor_id)
                    ON CONFLICT (slug) DO UPDATE SET title = :title, description = :description,
                        category = :category, difficulty = :difficulty, is_published = :is_published
                """),
                course_data,
            )
            course = db.get_course(conn, course_data["slug"])

            for m_idx, mod_data in enumerate(modules):
                lessons = mod_data.pop("lessons", [])
                conn.execute(
                    sa.text(f"""
                        INSERT INTO {S}.modules (course_id, title, order_idx)
                        VALUES (:c, :t, :o)
                        ON CONFLICT DO NOTHING
                    """),
                    {"c": course["id"], "t": mod_data["title"], "o": m_idx},
                )
                module = conn.execute(
                    sa.text(f"SELECT * FROM {S}.modules WHERE course_id = :c AND title = :t"),
                    {"c": course["id"], "t": mod_data["title"]},
                ).mappings().first()

                for l_idx, les_data in enumerate(lessons):
                    quiz_data = les_data.pop("quiz", None)
                    conn.execute(
                        sa.text(f"""
                            INSERT INTO {S}.lessons (module_id, title, content_md, xp_reward, duration_min, order_idx)
                            VALUES (:m, :title, :content_md, :xp_reward, :duration_min, :o)
                            ON CONFLICT DO NOTHING
                        """),
                        {"m": module["id"], "title": les_data["title"], "content_md": les_data.get("content_md", ""),
                         "xp_reward": les_data.get("xp_reward", 25), "duration_min": les_data.get("duration_min", 10), "o": l_idx},
                    )
                    lesson = conn.execute(
                        sa.text(f"SELECT * FROM {S}.lessons WHERE module_id = :m AND title = :t"),
                        {"m": module["id"], "t": les_data["title"]},
                    ).mappings().first()

                    if quiz_data and lesson:
                        questions = quiz_data.pop("questions", [])
                        conn.execute(
                            sa.text(f"""
                                INSERT INTO {S}.quizzes (lesson_id, title, pass_threshold, xp_reward)
                                VALUES (:l, :title, :pass_threshold, :xp_reward)
                                ON CONFLICT DO NOTHING
                            """),
                            {"l": lesson["id"], "title": quiz_data["title"],
                             "pass_threshold": quiz_data.get("pass_threshold", 70),
                             "xp_reward": quiz_data.get("xp_reward", 50)},
                        )
                        quiz = conn.execute(
                            sa.text(f"SELECT * FROM {S}.quizzes WHERE lesson_id = :l"),
                            {"l": lesson["id"]},
                        ).mappings().first()

                        for q_idx, q in enumerate(questions):
                            conn.execute(
                                sa.text(f"""
                                    INSERT INTO {S}.quiz_questions (quiz_id, question_text, options, correct_answer, explanation, order_idx)
                                    VALUES (:q, :question_text, :options, :correct_answer, :explanation, :o)
                                    ON CONFLICT DO NOTHING
                                """),
                                {"q": quiz["id"], "question_text": q["question_text"],
                                 "options": json.dumps(q["options"]), "correct_answer": q["correct_answer"],
                                 "explanation": q.get("explanation", ""), "o": q_idx},
                            )

            print(f"  Course: {course_data['title']} ({len(modules)} modules)")

    # school-administration layer (students/programs/gradebook/attendance/fees)
    import school
    with db.begin() as conn:
        s = school.seed_school(conn)
    print(f"  School: {s['students']} students · {s['programs']} programmes · {s['groups']} groups")

    print("Done! Demo accounts:")
    print("  Instructor: instructor@fastlms.dev / admin")
    print("  Student:    student@fastlms.dev / admin")


def reset():
    print(f"Dropping schema {S}...")
    with db.begin() as conn:
        conn.execute(sa.text(f"DROP SCHEMA IF EXISTS {S} CASCADE"))
    print("Schema dropped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.reset:
        reset()
    seed_all()
