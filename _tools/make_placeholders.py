"""
Generates solid-colour placeholder card images for each recipe.

These are intentionally simple placeholder cards (background colour + dish name),
meant to be replaced by real photographs later. Run with:

    python _tools/make_placeholders.py

Output is written straight into each recipe's page bundle as image.jpeg.
"""

import os
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 600
MARGIN = 90

# (output bundle dir, dish name, category label, background, text colour)
CARDS = [
    (
        "content/posts/lemon-garlic-pasta",
        "Lemon Garlic Pasta",
        "PASTA - 25 MIN",
        (214, 173, 96),
        (58, 42, 12),
    ),
    (
        "content/posts/roasted-tomato-soup",
        "Roasted Tomato Soup",
        "SOUP - 45 MIN",
        (176, 82, 62),
        (255, 240, 232),
    ),
    (
        "content/posts/blueberry-crumble",
        "Blueberry Crumble",
        "DESSERT - 55 MIN",
        (92, 106, 158),
        (240, 243, 255),
    ),
]

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_to_width(draw, text, font, max_width):
    """Greedy word wrap so the title fills the card without spilling over."""
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_card(out_dir, title, label, bg, fg):
    image = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(image)

    max_width = WIDTH - 2 * MARGIN

    # Shrink the title font until it wraps into at most two lines.
    size = 104
    while size > 44:
        font = load_font(size)
        lines = wrap_to_width(draw, title, font, max_width)
        if len(lines) <= 2:
            break
        size -= 4

    label_font = load_font(30)
    line_height = int(size * 1.18)
    block_height = line_height * len(lines)
    label_gap = 34
    label_height = 34

    total = block_height + label_gap + label_height
    y = (HEIGHT - total) // 2

    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=fg)
        y += line_height

    draw.text((MARGIN, y + label_gap), label, font=label_font, fill=fg)

    os.makedirs(out_dir, exist_ok=True)
    destination = os.path.join(out_dir, "image.jpeg")
    image.save(destination, "JPEG", quality=88, optimize=True)
    print(f"wrote {destination}  ({WIDTH}x{HEIGHT})")


def main():
    for out_dir, title, label, bg, fg in CARDS:
        build_card(out_dir, title, label, bg, fg)


if __name__ == "__main__":
    main()
