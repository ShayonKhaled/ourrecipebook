"""Turn a "New recipe" issue into a Hugo recipe page."""

import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

CONTENT_ROOT = Path("content/posts")

# Field labels to internal names. Each field lists the current label first and
# any earlier wording after it: someone with the form already open when a label
# changes will still submit the old wording, and the recipe must not be lost.
FIELDS = {
    "title": ("Name", "Recipe name"),
    "photo": ("Photo", "Photo of the dish"),
    "description": ("About", "A sentence or two about it"),
    "ingredients": ("Ingredients",),
    "method": ("Method", "How to make it"),
    "notes": ("Notes", "Anything worth remembering (optional)"),
    "tags": ("Tags", "Words to describe it (optional)"),
}

EMPTY_VALUES = {"", "_no response_", "no response"}


def find_field(body, labels):
    """Return the value under the first matching '### <label>' heading."""
    for label in labels:
        pattern = re.compile(
            r"^###\s+" + re.escape(label) + r"\s*$\n(.*?)(?=^###\s+|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(body)
        if not match:
            continue
        value = match.group(1).strip()
        if value.lower() not in EMPTY_VALUES:
            return value
    return ""


def parse_issue_body(body):
    """GitHub renders each field as '### <label>' followed by its value."""
    return {key: find_field(body, labels) for key, labels in FIELDS.items()}


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "recipe"


def flatten(text):
    return re.sub(r"\s+", " ", text).strip()


def yaml_string(value):
    """Single-quoted YAML scalar, so quotes in a recipe name are escaped."""
    cleaned = "".join(ch for ch in value if ch == "\t" or ord(ch) >= 32)
    return "'" + cleaned.replace("'", "''") + "'"


def indent_block(text, prefix="  "):
    return "\n".join(prefix + line if line.strip() else "" for line in text.splitlines())


NUMBERED = re.compile(r"^([-*+]|\d+[.)])\s+")


def as_bullet_list(text):
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        lines.append(line if NUMBERED.match(line) else f"- {line}")
    return "\n".join(lines)


def as_numbered_list(text):
    lines = []
    counter = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if NUMBERED.match(line):
            lines.append(line)
            counter = 0
            continue
        counter += 1
        lines.append(f"{counter}. {line}")
    return "\n".join(lines)


def build_markdown(fields, image_name):
    tags = []
    for raw in re.split(r"[,\n]", fields["tags"]):
        tag = re.sub(r"[^a-z0-9 \-]", "", flatten(raw).lower()).strip()
        if tag and tag not in tags:
            tags.append(tag)

    parts = [
        "---",
        f"title: {yaml_string(flatten(fields['title']))}",
        f"date: {datetime.now(timezone.utc):%Y-%m-%d}",
        f"image: {yaml_string(image_name)}",
    ]
    if tags:
        parts.append("tags:")
        parts.extend(f"  - {yaml_string(tag)}" for tag in tags)
    parts.append("---")
    parts.append("")

    described = flatten(fields["description"])
    if described:
        parts += [described, ""]

    if fields["ingredients"]:
        parts += ["## Ingredients", "", as_bullet_list(fields["ingredients"]), ""]

    if fields["method"]:
        parts += ["## Method", "", as_numbered_list(fields["method"]), ""]

    if fields["notes"]:
        parts += ["## Notes", "", indent_block(fields["notes"]), ""]

    return "\n".join(parts).rstrip() + "\n"


def unique_dir(base):
    if not base.exists():
        return base
    for n in range(2, 100):
        candidate = base.with_name(f"{base.name}-{n}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"no free directory name near {base}")


TITLE_RE = re.compile(r"""^\s*title:\s*(?P<value>.*?)\s*$""", re.MULTILINE)


def existing_titles():
    titles = []
    if not CONTENT_ROOT.is_dir():
        return titles
    for path in CONTENT_ROOT.rglob("index.md"):
        head = path.read_text(encoding="utf-8", errors="replace")[:2000]
        block = re.match(r"^---\s*\n(.*?)\n---", head, re.DOTALL)
        if not block:
            continue
        match = TITLE_RE.search(block.group(1))
        if not match:
            continue
        raw = match.group("value").strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
            raw = raw[1:-1]
        titles.append(raw.replace("''", "'"))
    return titles


def normalise(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def find_duplicate(title):
    wanted = normalise(title)
    if not wanted:
        return None
    for existing in existing_titles():
        if normalise(existing) == wanted:
            return existing
    return None


def main():
    body = os.environ.get("ISSUE_BODY", "")
    if not body.strip():
        print("ERROR: ISSUE_BODY is empty", file=sys.stderr)
        return 1

    fields = parse_issue_body(body)
    title = flatten(fields["title"])

    if not title:
        print("RESULT:missing-title")
        return 0

    duplicate = find_duplicate(title)
    if duplicate:
        print(f"RESULT:duplicate:{duplicate}")
        return 0

    image_name = os.environ.get("PHOTO_NAME", "image.jpeg").strip() or "image.jpeg"
    slug = slugify(title)
    if slug == "recipe":
        slug = slugify(os.environ.get("ISSUE_TITLE", ""))

    out_dir = unique_dir(CONTENT_ROOT / slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.md").write_text(
        build_markdown(fields, image_name), encoding="utf-8", newline="\n"
    )

    print(f"RESULT:created")
    print(f"dir={out_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
