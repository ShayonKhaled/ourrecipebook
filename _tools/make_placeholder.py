"""Make a simple card image for a recipe that was submitted without a photo.

    python _tools/make_placeholder.py "Recipe name" output/image.jpeg

Same look as _tools/make_placeholders.py, but for one recipe at a time. Used by
the recipe-from-issue workflow so that every recipe has an image and the site
build never fails on a missing file.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 600
MARGIN = 90
BACKGROUND = (176, 152, 116)
FOREGROUND = (255, 255, 255)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
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


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: make_placeholder.py <title> <output-path>", file=sys.stderr)
        return 2

    title = sys.argv[1].strip() or "Recipe"
    destination = sys.argv[2]

    # Keep to characters the bundled fonts can actually render.
    title = title.encode("ascii", "replace").decode("ascii").replace("?", "-")

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    max_width = WIDTH - 2 * MARGIN

    size = 92
    while size > 40:
        font = load_font(size)
        lines = wrap(draw, title, font, max_width)
        if len(lines) <= 2:
            break
        size -= 4

    line_height = int(size * 1.18)
    y = (HEIGHT - line_height * len(lines)) // 2
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=FOREGROUND)
        y += line_height

    parent = os.path.dirname(destination)
    if parent:
        os.makedirs(parent, exist_ok=True)
    image.save(destination, "JPEG", quality=88, optimize=True)
    print(f"wrote {destination} {WIDTH}x{HEIGHT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
