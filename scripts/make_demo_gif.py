#!/usr/bin/env python3
"""Build the English LinkedIn walkthrough from live Playwright captures.

Run after refreshing ``output/playwright/linkedin-demo/*.png``. The public
asset is written to ``static/fastlearn-demo.gif``.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "output" / "playwright" / "linkedin-demo"
OUT = ROOT / "static" / "fastlearn-demo.gif"
SIZE = (1200, 675)

SCENES = [
    ("01-home.png", "FastLearn", "One clear step at a time", 2200),
    ("02-catalogue.png", "15 COURSES", "Choose a subject or explore freely", 1900),
    ("03-mathematics.png", "MATHEMATICS", "Turn patterns into confident problem-solving", 1900),
    ("04-physics.png", "PHYSICS", "Connect equations to motion and the real world", 1900),
    ("05-geography.png", "GEOGRAPHY", "Understand our changing planet", 1900),
    ("06-art.png", "ART", "Learn to read colour, space and composition", 1900),
    ("07-chess.png", "CHESS", "Practise directly on the board", 2100),
    ("08-languages.png", "10 LANGUAGES", "Start from the language you already know", 2300),
]

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GREEN = (22, 101, 91, 242)
YELLOW = (242, 201, 76, 255)
WHITE = (255, 255, 255, 255)


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def decorate(path: Path, eyebrow: str, caption: str, index: int) -> Image.Image:
    base = Image.open(path).convert("RGB")
    if base.size != SIZE:
        base = base.resize(SIZE, Image.Resampling.LANCZOS)
    image = base.convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    x0, y0, x1, y1 = 300, 590, 1178, 657
    draw.rounded_rectangle((x0, y0, x1, y1), radius=15, fill=GREEN)
    draw.rounded_rectangle((x0 + 16, y0 + 13, x0 + 176, y0 + 53), radius=10, fill=(255, 255, 255, 34))
    draw.text((x0 + 29, y0 + 22), eyebrow, font=_font(FONT_BOLD, 14), fill=YELLOW)
    draw.text((x0 + 199, y0 + 20), caption, font=_font(FONT_BOLD, 21), fill=WHITE)

    progress_width = int((x1 - x0) * index / len(SCENES))
    draw.rounded_rectangle((x0, y1 - 4, x0 + progress_width, y1), radius=2, fill=YELLOW)
    return image.convert("RGB")


def crossfade(left: Image.Image, right: Image.Image, steps: int = 4) -> list[Image.Image]:
    return [Image.blend(left, right, step / (steps + 1)) for step in range(1, steps + 1)]


def main() -> None:
    missing = [name for name, *_ in SCENES if not (SHOTS / name).is_file()]
    if missing:
        raise SystemExit("Missing demo frames: " + ", ".join(missing))

    scenes = [
        (decorate(SHOTS / name, eyebrow, caption, index), duration)
        for index, (name, eyebrow, caption, duration) in enumerate(SCENES, 1)
    ]
    frames: list[Image.Image] = []
    durations: list[int] = []
    for index, (scene, hold) in enumerate(scenes):
        frames.append(scene)
        durations.append(hold)
        if index + 1 < len(scenes):
            fades = crossfade(scene, scenes[index + 1][0])
            frames.extend(fades)
            durations.extend([110] * len(fades))

    palette_frames = [frame.quantize(colors=192, method=Image.Quantize.MEDIANCUT) for frame in frames]
    palette_frames[0].save(
        OUT,
        save_all=True,
        append_images=palette_frames[1:],
        optimize=True,
        duration=durations,
        loop=0,
        disposal=2,
    )
    total_seconds = sum(durations) / 1000
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024 / 1024:.1f} MB, {total_seconds:.1f}s)")


if __name__ == "__main__":
    main()
