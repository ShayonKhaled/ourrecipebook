"""Generate placeholder card images for the recipes listed in CARDS."""

import os

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 600
MARGIN = 90

# (bundle dir, dish name, category label, background, text colour)
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

FONTS = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def load_font(size):
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap(draw, text, font, max_width):
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

    size = 104
    while size > 44:
        font = load_font(size)
        lines = wrap(draw, title, font, WIDTH - 2 * MARGIN)
        if len(lines) <= 2:
            break
        size -= 4

    label_font = load_font(30)
    line_height = int(size * 1.18)
    total = line_height * len(lines) + 34 + 34
    y = (HEIGHT - total) // 2

    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=fg)
        y += line_height
    draw.text((MARGIN, y + 34), label, font=label_font, fill=fg)

    os.makedirs(out_dir, exist_ok=True)
    image.save(os.path.join(out_dir, "image.jpeg"), "JPEG", quality=88, optimize=True)


def main():
    for out_dir, title, label, bg, fg in CARDS:
        build_card(out_dir, title, label, bg, fg)


if __name__ == "__main__":
    main()
