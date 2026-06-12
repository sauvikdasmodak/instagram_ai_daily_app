from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = BASE_DIR / "static" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        try:
            if path and Path(path).exists():
                return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap_text(text: str, width: int) -> list[str]:
    text = " ".join(text.split())
    return textwrap.wrap(text, width=width, break_long_words=False)


def _gradient(size: Tuple[int, int], start=(20, 25, 40), end=(42, 68, 110)) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, start)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(start[0] * (1 - ratio) + end[0] * ratio)
        g = int(start[1] * (1 - ratio) + end[1] * ratio)
        b = int(start[2] * (1 - ratio) + end[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def build_post_image(title: str, subtitle: str, brand_name: str, handle: str, post_id: str) -> str:
    width, height = 1080, 1080
    img = _gradient((width, height))
    draw = ImageDraw.Draw(img)

    # Decorative cards/circles
    draw.ellipse((-180, -160, 320, 340), fill=(63, 105, 170))
    draw.ellipse((780, 740, 1240, 1200), fill=(30, 95, 120))
    draw.rounded_rectangle((70, 90, 1010, 990), radius=42, outline=(255, 255, 255), width=3)

    small_font = _font(34, bold=True)
    title_font = _font(72, bold=True)
    subtitle_font = _font(42)
    footer_font = _font(30)

    draw.text((105, 125), brand_name.upper(), fill=(235, 245, 255), font=small_font)
    draw.line((105, 180, 360, 180), fill=(235, 245, 255), width=4)

    y = 280
    for line in _wrap_text(title, 18)[:5]:
        draw.text((105, y), line, fill=(255, 255, 255), font=title_font)
        y += 84

    y += 30
    for line in _wrap_text(subtitle, 32)[:5]:
        draw.text((105, y), line, fill=(225, 235, 245), font=subtitle_font)
        y += 54

    footer = f"@{handle.strip().lstrip('@')}" if handle else "AI daily insight"
    draw.text((105, 930), footer, fill=(235, 245, 255), font=footer_font)

    filename = f"ai_post_{post_id}.jpg"
    path = GENERATED_DIR / filename
    img.save(path, quality=92, optimize=True)
    return filename
