"""Seed additional academic subjects — Mathematics, Physics, Biology, Chemistry, English, Geography, Creative Writing.

Usage:
    python seed_subjects.py
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from dotenv import load_dotenv

import db

load_dotenv()

S = db.SCHEMA

COURSES = [
    # ---------------------------------------------------------------
    # MATHEMATICS
    # ---------------------------------------------------------------
    {
        "title": "Mathematics Foundations",
        "slug": "mathematics-foundations",
        "description": "Build a solid maths foundation — algebra, geometry, probability, and calculus basics. From equations to proofs, gain confidence with numbers.",
        "category": "Mathematics",
        "difficulty": "beginner",
        "is_published": True,
        "modules": [
            {
                "title": "Algebra",
                "lessons": [
                    {
                        "title": "Variables and Expressions",
                        "content_md": """# Variables and Expressions

## What is Algebra?

Algebra is the branch of mathematics that uses letters (variables) to represent unknown values and studies the rules for manipulating them.

## Expressions vs Equations

- **Expression**: a combination of numbers, variables, and operators — `3x + 7`
- **Equation**: a statement that two expressions are equal — `3x + 7 = 22`

## Order of Operations (BODMAS / PEMDAS)

1. **B**rackets / **P**arentheses
2. **O**rders / **E**xponents (powers, roots)
3. **D**ivision and **M**ultiplication (left to right)
4. **A**ddition and **S**ubtraction (left to right)

Example: `2 + 3 x 4 = 2 + 12 = 14` (not 20!)

## Simplifying Expressions

Combine **like terms** — terms with the same variable and exponent:

```
5x + 3y - 2x + 7y = (5x - 2x) + (3y + 7y) = 3x + 10y
```

## Substitution

Replace variables with values:

If `x = 4`, then `2x + 5 = 2(4) + 5 = 13`

> **Key insight**: Algebra is the language of patterns. Once you can write a pattern as an expression, you can solve problems you've never seen before.
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                        "quiz": {
                            "title": "Algebra Basics Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 30,
                            "questions": [
                                {"question_text": "What is 2 + 3 x 4 using correct order of operations?", "options": ["20", "14", "24", "18"], "correct_answer": "14", "explanation": "Multiplication before addition: 3 x 4 = 12, then 2 + 12 = 14."},
                                {"question_text": "Simplify: 5x + 3x", "options": ["8x", "15x", "8x^2", "53x"], "correct_answer": "8x", "explanation": "Like terms with the same variable are added: 5x + 3x = 8x."},
                                {"question_text": "If x = 3, what is 4x - 2?", "options": ["10", "12", "6", "14"], "correct_answer": "10", "explanation": "Substitute x = 3: 4(3) - 2 = 12 - 2 = 10."},
                            ],
                        },
                    },
                    {
                        "title": "Solving Linear Equations",
                        "content_md": """# Solving Linear Equations

## The Golden Rule

Whatever you do to one side of the equation, you must do to the other side.

## One-Step Equations

```
x + 5 = 12     →  x = 12 - 5  →  x = 7
3x = 21         →  x = 21 / 3  →  x = 7
```

## Two-Step Equations

```
2x + 3 = 11
2x = 11 - 3    (subtract 3 from both sides)
2x = 8
x = 4           (divide both sides by 2)
```

## Equations with Variables on Both Sides

```
5x - 3 = 2x + 9
3x = 12          (subtract 2x, add 3)
x = 4
```

## Checking Your Answer

Always substitute back: `5(4) - 3 = 17` and `2(4) + 9 = 17` ✓
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                    },
                ],
            },
            {
                "title": "Geometry",
                "lessons": [
                    {
                        "title": "Shapes, Area, and Perimeter",
                        "content_md": """# Shapes, Area, and Perimeter

## Key Formulas

| Shape | Area | Perimeter |
|-------|------|-----------|
| Rectangle | `l x w` | `2(l + w)` |
| Triangle | `½ x b x h` | `a + b + c` |
| Circle | `π r²` | `2πr` |
| Trapezoid | `½(a + b) x h` | `a + b + c + d` |

## Worked Example

A rectangle has length 8 cm and width 5 cm.

- **Area** = 8 x 5 = 40 cm²
- **Perimeter** = 2(8 + 5) = 2(13) = 26 cm

## Pythagoras' Theorem

For right-angled triangles: **a² + b² = c²**

If two sides are 3 and 4:
```
c² = 3² + 4² = 9 + 16 = 25
c = √25 = 5
```

> The 3-4-5 triangle is the most famous Pythagorean triple. Others include 5-12-13 and 8-15-17.
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                    },
                ],
            },
        ],
    },

    # ---------------------------------------------------------------
    # PHYSICS
    # ---------------------------------------------------------------
    {
        "title": "Physics Essentials",
        "slug": "physics-essentials",
        "description": "Understand the laws that govern the universe — mechanics, energy, waves, and electricity. Practical examples and problem-solving throughout.",
        "category": "Physics",
        "difficulty": "intermediate",
        "is_published": True,
        "modules": [
            {
                "title": "Mechanics",
                "lessons": [
                    {
                        "title": "Speed, Velocity, and Acceleration",
                        "content_md": """# Speed, Velocity, and Acceleration

## Speed vs Velocity

- **Speed** = distance / time (scalar — magnitude only)
- **Velocity** = displacement / time (vector — magnitude + direction)

A car driving 100 km around a circular track in 1 hour has **speed = 100 km/h** but **velocity = 0** (it's back where it started).

## Acceleration

Rate of change of velocity:

```
a = (v - u) / t
```

Where:
- `u` = initial velocity
- `v` = final velocity
- `t` = time taken

## SUVAT Equations

For **uniform acceleration** (constant `a`):

| Equation | Missing |
|----------|---------|
| `v = u + at` | `s` |
| `s = ut + ½at²` | `v` |
| `v² = u² + 2as` | `t` |
| `s = ½(u + v)t` | `a` |

## Worked Example

A car accelerates from 0 to 30 m/s in 6 seconds.

```
a = (30 - 0) / 6 = 5 m/s²
s = ½(0 + 30)(6) = 90 m
```

> **Free fall**: On Earth, `g ≈ 9.81 m/s²`. A dropped object (ignoring air resistance) gains ~10 m/s of speed every second.
""",
                        "xp_reward": 35,
                        "duration_min": 25,
                        "quiz": {
                            "title": "Mechanics Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 40,
                            "questions": [
                                {"question_text": "What is the acceleration if a car goes from 0 to 20 m/s in 4 seconds?", "options": ["5 m/s^2", "80 m/s^2", "4 m/s^2", "10 m/s^2"], "correct_answer": "5 m/s^2", "explanation": "a = (v - u) / t = (20 - 0) / 4 = 5 m/s^2."},
                                {"question_text": "What is the difference between speed and velocity?", "options": ["Speed has direction, velocity doesn't", "Velocity has direction, speed doesn't", "They are the same thing", "Speed is always faster"], "correct_answer": "Velocity has direction, speed doesn't", "explanation": "Speed is scalar (magnitude only), velocity is vector (magnitude + direction)."},
                            ],
                        },
                    },
                    {
                        "title": "Newton's Laws of Motion",
                        "content_md": """# Newton's Laws of Motion

## First Law (Inertia)

An object stays at rest or in uniform motion unless acted upon by an external force.

- A book on a table stays still until you push it
- A spaceship in empty space keeps moving forever (no friction)

## Second Law (F = ma)

Force equals mass times acceleration.

```
F = ma
```

A 10 kg box pushed with 50 N of force:
```
a = F/m = 50/10 = 5 m/s²
```

## Third Law (Action-Reaction)

For every action, there is an equal and opposite reaction.

- When you push a wall, the wall pushes back on you
- A rocket pushes exhaust down, the exhaust pushes the rocket up
- You push the ground backward when walking, the ground pushes you forward

## Weight vs Mass

- **Mass** = amount of matter (kg) — constant everywhere
- **Weight** = gravitational force (N) — `W = mg`

On Earth: `W = 70 x 9.81 = 687 N`
On the Moon: `W = 70 x 1.62 = 113 N`
""",
                        "xp_reward": 35,
                        "duration_min": 25,
                    },
                ],
            },
        ],
    },

    # ---------------------------------------------------------------
    # BIOLOGY
    # ---------------------------------------------------------------
    {
        "title": "Biology: Life Sciences",
        "slug": "biology-life-sciences",
        "description": "Explore living systems — cell biology, genetics, ecology, and human physiology. Understand how organisms grow, reproduce, and interact with their environment.",
        "category": "Biology",
        "difficulty": "beginner",
        "is_published": True,
        "modules": [
            {
                "title": "Cell Biology",
                "lessons": [
                    {
                        "title": "Cell Structure",
                        "content_md": """# Cell Structure

Cells are the fundamental building blocks of all living organisms.

## Animal vs Plant Cells

| Feature | Animal Cell | Plant Cell |
|---------|-------------|------------|
| Cell wall | No | Yes (cellulose) |
| Chloroplasts | No | Yes |
| Vacuole | Small, multiple | Large, central |
| Shape | Irregular | Regular / rectangular |
| Both have | Nucleus, mitochondria, ribosomes, cell membrane, cytoplasm |

## Key Organelles

- **Nucleus** — contains DNA, controls cell activities
- **Mitochondria** — "powerhouse of the cell", produces ATP via aerobic respiration
- **Ribosomes** — synthesise proteins from amino acids
- **Cell membrane** — selectively permeable barrier, controls what enters and leaves
- **Endoplasmic reticulum (ER)** — rough ER has ribosomes (protein transport), smooth ER makes lipids
- **Golgi apparatus** — packages and modifies proteins for secretion

## Prokaryotes vs Eukaryotes

| Feature | Prokaryote | Eukaryote |
|---------|------------|-----------|
| Nucleus | No (nucleoid) | Yes |
| Size | 1-10 μm | 10-100 μm |
| Examples | Bacteria | Animals, plants, fungi |
| DNA | Circular | Linear chromosomes |

> **Scale**: If a cell were the size of a football pitch, a mitochondrion would be the size of a person, and a ribosome would be the size of a football.
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                        "quiz": {
                            "title": "Cell Structure Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 30,
                            "questions": [
                                {"question_text": "Which organelle is the 'powerhouse of the cell'?", "options": ["Nucleus", "Ribosome", "Mitochondria", "Golgi apparatus"], "correct_answer": "Mitochondria", "explanation": "Mitochondria produce ATP through aerobic respiration."},
                                {"question_text": "Which feature do plant cells have that animal cells do not?", "options": ["Nucleus", "Cell membrane", "Cell wall", "Mitochondria"], "correct_answer": "Cell wall", "explanation": "Plant cells have a rigid cellulose cell wall outside the cell membrane."},
                                {"question_text": "Do prokaryotes have a nucleus?", "options": ["Yes", "No", "Only bacteria do", "Only when dividing"], "correct_answer": "No", "explanation": "Prokaryotes have a nucleoid region but no membrane-bound nucleus."},
                            ],
                        },
                    },
                ],
            },
            {
                "title": "Genetics",
                "lessons": [
                    {
                        "title": "DNA and Inheritance",
                        "content_md": """# DNA and Inheritance

## DNA Structure

DNA (deoxyribonucleic acid) is a double helix made of nucleotides. Each nucleotide has:
- A phosphate group
- A deoxyribose sugar
- A nitrogenous base (A, T, C, or G)

**Base pairing rules**: A-T (2 hydrogen bonds), C-G (3 hydrogen bonds)

## Genes and Chromosomes

- **Gene** — a section of DNA that codes for a specific protein
- **Chromosome** — a long DNA molecule wrapped around proteins (histones)
- Humans have **46 chromosomes** (23 pairs)
- Pair 23 = sex chromosomes: XX (female), XY (male)

## Inheritance

- **Allele** — a version of a gene (e.g., brown eye allele, blue eye allele)
- **Dominant** (B) — expressed when one or two copies present
- **Recessive** (b) — only expressed when two copies present
- **Genotype** — the alleles you carry (BB, Bb, bb)
- **Phenotype** — the observable trait (brown eyes, blue eyes)

## Punnett Square

Crossing Bb x Bb:

```
        B       b
  B    BB      Bb
  b    Bb      bb
```

Ratio: 3 dominant : 1 recessive (75% : 25%)
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                    },
                ],
            },
        ],
    },

    # ---------------------------------------------------------------
    # CHEMISTRY
    # ---------------------------------------------------------------
    {
        "title": "Chemistry Fundamentals",
        "slug": "chemistry-fundamentals",
        "description": "Understand matter at the atomic level — atomic structure, bonding, reactions, and the periodic table. From molecules to stoichiometry.",
        "category": "Chemistry",
        "difficulty": "intermediate",
        "is_published": True,
        "modules": [
            {
                "title": "Atomic Structure",
                "lessons": [
                    {
                        "title": "Atoms and the Periodic Table",
                        "content_md": """# Atoms and the Periodic Table

## Structure of an Atom

| Particle | Charge | Mass | Location |
|----------|--------|------|----------|
| Proton | +1 | 1 amu | Nucleus |
| Neutron | 0 | 1 amu | Nucleus |
| Electron | -1 | ~0 | Electron shells |

- **Atomic number** = number of protons (defines the element)
- **Mass number** = protons + neutrons
- **Isotopes** = same element, different number of neutrons (e.g., Carbon-12 vs Carbon-14)

## Electron Configuration

Electrons fill shells from the inside out:
- Shell 1: max 2 electrons
- Shell 2: max 8 electrons
- Shell 3: max 8 electrons (simplified)

Example — Sodium (Na, atomic number 11): `2, 8, 1`

## The Periodic Table

- **Groups** (columns) = same number of outer electrons → similar chemical properties
- **Periods** (rows) = same number of electron shells
- **Metals** on the left, **non-metals** on the right
- **Group 1** (alkali metals): reactive, 1 outer electron
- **Group 7** (halogens): reactive, 7 outer electrons
- **Group 0** (noble gases): unreactive, full outer shell

> **Mendeleev's genius**: He arranged elements by atomic mass AND left gaps for undiscovered elements — and predicted their properties correctly.
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                        "quiz": {
                            "title": "Atoms Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 35,
                            "questions": [
                                {"question_text": "What defines which element an atom is?", "options": ["Number of electrons", "Number of neutrons", "Number of protons", "Its mass"], "correct_answer": "Number of protons", "explanation": "The atomic number (number of protons) defines the element."},
                                {"question_text": "What is the electron configuration of Oxygen (atomic number 8)?", "options": ["2, 6", "2, 8", "8", "2, 4, 2"], "correct_answer": "2, 6", "explanation": "Shell 1 holds 2 electrons, shell 2 holds the remaining 6."},
                            ],
                        },
                    },
                ],
            },
            {
                "title": "Chemical Reactions",
                "lessons": [
                    {
                        "title": "Types of Reactions and Balancing Equations",
                        "content_md": """# Types of Reactions and Balancing Equations

## Types of Chemical Reactions

1. **Combustion**: Fuel + O₂ → CO₂ + H₂O (+ energy)
2. **Neutralisation**: Acid + Base → Salt + Water
3. **Decomposition**: AB → A + B (one compound breaks down)
4. **Displacement**: More reactive element displaces less reactive one
5. **Synthesis**: A + B → AB (two elements combine)

## Balancing Equations

Atoms in = atoms out (conservation of mass).

**Unbalanced**: `H₂ + O₂ → H₂O`

Count: Left has 2H, 2O. Right has 2H, 1O. Not balanced!

**Balanced**: `2H₂ + O₂ → 2H₂O`

Count: Left 4H, 2O. Right 4H, 2O. ✓

## Exothermic vs Endothermic

- **Exothermic**: releases energy (combustion, neutralisation). Temperature rises.
- **Endothermic**: absorbs energy (photosynthesis, thermal decomposition). Temperature drops.

## Rates of Reaction

Reactions go faster with:
- Higher **temperature** (particles move faster)
- Higher **concentration** (more particles per volume)
- Smaller **surface area** (more exposed particles)
- A **catalyst** (lowers activation energy, not consumed)
""",
                        "xp_reward": 35,
                        "duration_min": 25,
                    },
                ],
            },
        ],
    },

    # ---------------------------------------------------------------
    # ENGLISH
    # ---------------------------------------------------------------
    {
        "title": "English Language & Literature",
        "slug": "english-language-literature",
        "description": "Strengthen reading comprehension, essay writing, literary analysis, and grammar. Covers fiction, non-fiction, poetry, and persuasive writing.",
        "category": "English",
        "difficulty": "beginner",
        "is_published": True,
        "modules": [
            {
                "title": "Reading & Comprehension",
                "lessons": [
                    {
                        "title": "Analysing Texts",
                        "content_md": """# Analysing Texts

## The PEE Framework

Use **P**oint, **E**vidence, **E**xplanation for every analytical paragraph:

1. **Point** — state your argument clearly
2. **Evidence** — quote directly from the text
3. **Explanation** — analyse HOW the evidence supports your point

### Example

> **Point**: Shakespeare presents Lady Macbeth as ambitious.
> **Evidence**: She calls upon spirits to "unsex me here" and fill her with "direst cruelty."
> **Explanation**: The imperative verb "unsex" suggests she wants to reject femininity, which in the Jacobean era was associated with gentleness, in order to pursue power through violence.

## Language Techniques to Spot

| Technique | Definition | Effect |
|-----------|-----------|--------|
| Metaphor | Comparing without "like/as" | Creates a vivid image |
| Simile | Comparing with "like/as" | Makes abstract ideas concrete |
| Personification | Giving human qualities to non-human things | Creates empathy or menace |
| Alliteration | Repeated consonant sounds | Emphasises, creates rhythm |
| Pathetic fallacy | Weather reflecting mood | Sets atmosphere |
| Juxtaposition | Placing contrasts side by side | Highlights differences |

## Structure to Analyse

- **Opening** — how does the writer hook the reader?
- **Shift** — where does the tone or perspective change?
- **Ending** — circular? Open? Resolved? What's the effect?

> **Top tip**: Don't just identify techniques — always explain their **effect** on the reader.
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                        "quiz": {
                            "title": "Text Analysis Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 30,
                            "questions": [
                                {"question_text": "What does PEE stand for in essay writing?", "options": ["Point, Example, Explain", "Point, Evidence, Explanation", "Paragraph, Evidence, Example", "Point, Evaluate, Extend"], "correct_answer": "Point, Evidence, Explanation", "explanation": "PEE = Point, Evidence, Explanation — the building block of analytical paragraphs."},
                                {"question_text": "What is pathetic fallacy?", "options": ["A logical error", "Weather reflecting mood", "A type of metaphor", "An unreliable narrator"], "correct_answer": "Weather reflecting mood", "explanation": "Pathetic fallacy is when weather or environment mirrors a character's emotions."},
                            ],
                        },
                    },
                ],
            },
            {
                "title": "Writing Skills",
                "lessons": [
                    {
                        "title": "Essay Structure and Paragraphing",
                        "content_md": """# Essay Structure and Paragraphing

## The Hamburger Model

Every essay has three parts:

1. **Introduction** (top bun) — hook, context, thesis statement
2. **Body paragraphs** (filling) — 3-5 PEE paragraphs, each making one point
3. **Conclusion** (bottom bun) — summarise, reflect, final thought

## Writing a Strong Introduction

```
Hook → Context → Thesis

"From the very first line, Orwell establishes a world where truth
is malleable. Written in 1949 as a warning against totalitarianism,
1984 remains chillingly relevant. This essay argues that Orwell uses
language as the primary weapon of oppression."
```

## Linking Paragraphs

Use **discourse markers** to connect ideas:
- **Adding**: Furthermore, Moreover, Additionally
- **Contrasting**: However, On the other hand, Conversely
- **Concluding**: Therefore, Ultimately, In conclusion
- **Sequencing**: Firstly, Subsequently, Finally

## Common Grammar Pitfalls

- **Their / They're / There** — possession / contraction / place
- **Its / It's** — possession / contraction ("it is")
- **Affect / Effect** — verb / noun (usually)
- **Comma splices** — don't join two sentences with just a comma
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                    },
                ],
            },
        ],
    },

    # ---------------------------------------------------------------
    # GEOGRAPHY
    # ---------------------------------------------------------------
    {
        "title": "Geography: Physical & Human",
        "slug": "geography-physical-human",
        "description": "Study the Earth's landscapes, climate systems, and human geography — urbanisation, globalisation, resource management, and sustainability.",
        "category": "Geography",
        "difficulty": "beginner",
        "is_published": True,
        "modules": [
            {
                "title": "Physical Geography",
                "lessons": [
                    {
                        "title": "Plate Tectonics and Earthquakes",
                        "content_md": """# Plate Tectonics and Earthquakes

## The Earth's Structure

- **Crust** — thin outer layer (5-70 km). Oceanic crust is thinner and denser than continental.
- **Mantle** — hot, semi-molten rock. Convection currents drive plate movement.
- **Outer core** — liquid iron and nickel (~5,000°C)
- **Inner core** — solid iron and nickel (~6,000°C)

## Plate Boundaries

| Type | Movement | Features | Example |
|------|----------|----------|---------|
| **Constructive** | Plates move apart | Mid-ocean ridges, volcanoes | Mid-Atlantic Ridge |
| **Destructive** | Plates collide | Trenches, fold mountains, volcanoes | Andes, Japan |
| **Conservative** | Plates slide past | Earthquakes (no volcanoes) | San Andreas Fault |

## Earthquakes

Caused by sudden release of energy at plate boundaries.

- **Focus** — point underground where the earthquake originates
- **Epicentre** — point on the surface directly above the focus
- **Seismic waves** — P-waves (fastest, longitudinal), S-waves (transverse), L-waves (surface, most destructive)
- **Richter scale** — measures magnitude (logarithmic: each step = 10x more energy)

## Why Do People Live Near Volcanoes?

- Fertile volcanic soil
- Geothermal energy
- Tourism
- Mineral deposits
- Cultural/historical roots

> **Key stat**: 80% of earthquakes occur along the "Ring of Fire" around the Pacific plate.
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                        "quiz": {
                            "title": "Plate Tectonics Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 35,
                            "questions": [
                                {"question_text": "At which type of plate boundary do plates move apart?", "options": ["Destructive", "Conservative", "Constructive", "Transform"], "correct_answer": "Constructive", "explanation": "At constructive boundaries, plates diverge and new crust forms from rising magma."},
                                {"question_text": "What percentage of earthquakes occur along the Ring of Fire?", "options": ["50%", "65%", "80%", "95%"], "correct_answer": "80%", "explanation": "Approximately 80% of the world's earthquakes occur along the Pacific Ring of Fire."},
                            ],
                        },
                    },
                ],
            },
            {
                "title": "Human Geography",
                "lessons": [
                    {
                        "title": "Urbanisation and Megacities",
                        "content_md": """# Urbanisation and Megacities

## What is Urbanisation?

The increasing percentage of a population living in urban areas. In 2025, ~56% of the world's population lives in cities. By 2050, this will reach ~68%.

## Push and Pull Factors

| Push (rural → city) | Pull (city attracts) |
|---------------------|---------------------|
| Lack of jobs | Employment opportunities |
| Poor services | Better healthcare, education |
| Natural disasters | Higher wages |
| Conflict | Entertainment, culture |

## Megacities

A megacity has a population of **10 million+**. In 2025, there are 33 megacities.

Top 5: Tokyo (37M), Delhi (32M), Shanghai (29M), Sao Paulo (22M), Mexico City (22M)

## Urban Challenges

- **Housing** — slums, informal settlements, homelessness
- **Transport** — congestion, pollution, infrastructure strain
- **Services** — water, sanitation, electricity for growing populations
- **Environment** — urban heat island, waste management, air quality

## Sustainable Urban Living

- Green spaces and urban forests
- Public transport and cycling infrastructure
- Renewable energy in buildings
- Waste recycling and circular economy
- Mixed-use development (reduce commuting)
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                    },
                ],
            },
        ],
    },

    # ---------------------------------------------------------------
    # CREATIVE WRITING
    # ---------------------------------------------------------------
    {
        "title": "Creative Writing",
        "slug": "creative-writing",
        "description": "Develop your voice as a writer — narrative techniques, character development, world-building, poetry forms, and the craft of revision.",
        "category": "Creative Writing",
        "difficulty": "beginner",
        "is_published": True,
        "modules": [
            {
                "title": "Storytelling Fundamentals",
                "lessons": [
                    {
                        "title": "Show, Don't Tell",
                        "content_md": """# Show, Don't Tell

The most important rule in creative writing. Instead of telling the reader what to feel, show them through concrete detail.

## Telling vs Showing

**Telling**: "She was angry."

**Showing**: "Her knuckles whitened around the edge of the table. She spoke through clenched teeth, each word a separate sentence."

## How to Show

1. **Use sensory details** — sight, sound, smell, touch, taste
2. **Show through action** — what does the character DO?
3. **Show through dialogue** — what do they SAY (and how)?
4. **Show through physical response** — body language, involuntary reactions

## Practice: Rewrite These

Try rewriting these "telling" sentences as "showing":

- "The house was old and creepy."
- "He was very tired."
- "They were in love."

## When Telling Is OK

- **Transitions**: "Three weeks later, they arrived in Paris."
- **Minor details**: "She ordered coffee" (no need to show the ordering process)
- **Pacing**: Sometimes you need to speed past less important moments

> **Chekhov's advice**: "Don't tell me the moon is shining; show me the glint of light on broken glass."
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                        "quiz": {
                            "title": "Show Don't Tell Quiz",
                            "pass_threshold": 60,
                            "xp_reward": 30,
                            "questions": [
                                {"question_text": "Which is an example of 'showing' rather than 'telling'?", "options": ["She was sad", "Tears ran down her cheeks as she stared at the empty chair", "The weather was bad", "He felt happy"], "correct_answer": "Tears ran down her cheeks as she stared at the empty chair", "explanation": "This uses concrete sensory detail and action rather than naming the emotion directly."},
                                {"question_text": "When is 'telling' acceptable in creative writing?", "options": ["Never", "For transitions and minor details", "Only in non-fiction", "Always"], "correct_answer": "For transitions and minor details", "explanation": "Telling is fine for transitions ('Three weeks later...') and unimportant details to maintain pacing."},
                            ],
                        },
                    },
                    {
                        "title": "Creating Characters",
                        "content_md": """# Creating Characters

## The Character Iceberg

What the reader sees (above the water):
- Name, appearance, speech patterns
- Actions and decisions
- Relationships with others

What drives the character (below the water):
- Backstory, formative experiences
- Fears, desires, contradictions
- Worldview and values

## Character vs Caricature

A **character** has:
- Contradictions ("a generous miser")
- Internal conflict
- The capacity to surprise the reader
- Growth or change (arc)

A **caricature** has:
- One defining trait
- Predictable behaviour
- No internal life

## Dialogue That Reveals Character

Good dialogue does double duty — it advances the plot AND reveals character.

```
"I don't need anyone's help," she said, already reaching for his hand.
```

This single line tells us more than a paragraph of description: she's proud but lonely.

## Exercise: Character Sheet

For your next character, answer:
1. What do they want more than anything?
2. What are they afraid of?
3. What's the gap between how they see themselves and how others see them?
4. What would they never do? (Then make them do it in the climax.)

> **Fitzgerald**: "Begin with an individual, and before you know it you have created a type; begin with a type, and you have created — nothing."
""",
                        "xp_reward": 30,
                        "duration_min": 20,
                    },
                ],
            },
            {
                "title": "Poetry",
                "lessons": [
                    {
                        "title": "Forms and Free Verse",
                        "content_md": """# Forms and Free Verse

## Why Forms Matter

Poetic forms are constraints — and constraints breed creativity. Writing a sonnet forces you to compress, choose, and surprise within 14 lines.

## Common Forms

### Haiku (3 lines: 5-7-5 syllables)
```
An old silent pond
A frog jumps into the pond—
Splash! Silence again.
    — Basho (translated)
```

### Sonnet (14 lines, iambic pentameter)
- **Shakespearean**: ABAB CDCD EFEF GG (volta at line 13)
- **Petrarchan**: ABBAABBA CDECDE (volta at line 9)

### Villanelle (19 lines, 2 repeating refrains)
```
Do not go gentle into that good night,
Old age should burn and rave at close of day;
Rage, rage against the dying of the light.
    — Dylan Thomas
```

## Free Verse

No fixed rhyme, metre, or form — but not "anything goes." Free verse still uses:
- **Line breaks** for emphasis and pacing
- **Imagery** and concrete detail
- **Sound** (assonance, consonance, internal rhyme)
- **Rhythm** (even without metre, there's cadence)

## The Line Break

The most powerful tool in poetry. Where you break the line changes the meaning:

```
I love you more than
anything
```

vs

```
I love you more
than anything
```

> **Mary Oliver**: "Poetry is a life-cherishing force. And it requires a vision — a faith, to use an old-fashioned term. Yes, indeed."
""",
                        "xp_reward": 25,
                        "duration_min": 15,
                    },
                ],
            },
        ],
    },
]


def seed_subjects():
    print("Bootstrapping schema...")
    db.bootstrap_schema()

    with db.begin() as conn:
        instructor = db.get_user_by_email(conn, "instructor@fastlms.dev")
        if not instructor:
            print("ERROR: Run seed.py first to create demo instructor account")
            return

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
                    sa.text(f"INSERT INTO {S}.modules (course_id, title, order_idx) VALUES (:c, :t, :o) ON CONFLICT DO NOTHING"),
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
                                VALUES (:l, :title, :pass_threshold, :xp_reward) ON CONFLICT DO NOTHING
                            """),
                            {"l": lesson["id"], "title": quiz_data["title"],
                             "pass_threshold": quiz_data.get("pass_threshold", 70), "xp_reward": quiz_data.get("xp_reward", 50)},
                        )
                        quiz = conn.execute(sa.text(f"SELECT * FROM {S}.quizzes WHERE lesson_id = :l"), {"l": lesson["id"]}).mappings().first()
                        for q_idx, q in enumerate(questions):
                            conn.execute(
                                sa.text(f"""
                                    INSERT INTO {S}.quiz_questions (quiz_id, question_text, options, correct_answer, explanation, order_idx)
                                    VALUES (:q, :question_text, :options, :correct_answer, :explanation, :o) ON CONFLICT DO NOTHING
                                """),
                                {"q": quiz["id"], "question_text": q["question_text"], "options": json.dumps(q["options"]),
                                 "correct_answer": q["correct_answer"], "explanation": q.get("explanation", ""), "o": q_idx},
                            )

            print(f"  {course_data['title']} ({len(modules)} modules)")

    print("Done! 7 new subjects seeded.")


if __name__ == "__main__":
    seed_subjects()
