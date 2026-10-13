"""Turn a "New recipe" GitHub issue into a Hugo recipe page.

Reads the issue body GitHub generates from .github/ISSUE_TEMPLATE/new-recipe.yml
and writes content/posts/<slug>/index.md.

Inputs come from the environment so that untrusted issue text is never
interpolated into a shell command:

    ISSUE_BODY      the issue body (required)
    ISSUE_TITLE     the issue title, used only to derive a fallback slug
    PHOTO_STATUS    "saved" if the workflow already downloaded the photo,
                    "" / unset if there was no photo
    PHOTO_NAME      bare filename of the saved photo, e.g. cover.jpg

Prints the directory it wrote to on stdout, so the workflow can use it.
"""

import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

CONTENT_ROOT = Path("content/posts")

# Field label in the issue form -> internal name.
LABELS = {
    "Recipe name": "title",
    "Photo of the dish": "photo",
    "A sentence or two about it": "description",
    "Ingredients": "ingredients",
    "How to make it": "method",
    "Anything worth remembering (optional)": "notes",
    "Words to describe it (optional)": "tags",
}


def parse_issue_body(body: str) -> dict:
    """Split the issue body into {internal name: value}.

    GitHub renders each form field as '### <label>' followed by the value. An
    untouched optional field is rendered as the literal '_No response_'.
    """
    sections = {}
    for label, key in LABELS.items():
        # Match the heading and capture everything up to the next '### ' heading.
        pattern = re.compile(
            r"^###\s+" + re.escape(label) + r"\s*$\n(.*?)(?=^###\s+|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(body)
        value = match.group(1).strip() if match else ""
        if value.lower() in {"_no response_", "no response", ""}:
            value = ""
        sections[key] = value
    return sections


def slugify(text: str) -> str:
    """A URL-safe, filesystem-safe slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60] or "recipe"


def flatten(text: str) -> str:
    """Collapse a multi-line value into a single line."""
    return re.sub(r"\s+", " ", text).strip()


def yaml_string(value: str) -> str:
    """Render a value as a safe YAML single-quoted scalar.

    A recipe name like `Grandma's "special" cobbler` would otherwise produce
    invalid YAML and break the whole site build, so this always quotes and
    escapes rather than hoping the text is well behaved.

    In YAML single-quoted scalars the only escape is '' for a literal quote,
    which keeps backslashes and colons literal too.
    """
    # Drop control characters, which are not valid in YAML at all.
    cleaned = "".join(ch for ch in value if ch == "\t" or ord(ch) >= 32)
    return "'" + cleaned.replace("'", "''") + "'"


def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line if line.strip() else "" for line in text.splitlines())


def as_bullet_list(text: str) -> str:
    """Turn loose lines into Markdown bullets.

    Plain text typed into a textarea has no Markdown line breaks, so without
    this every ingredient runs together into a single paragraph.
    """
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Already a bullet or numbered item: keep it as written.
        if re.match(r"^([-*+]|\d+[.)])\s+", line):
            lines.append(line)
        else:
            lines.append(f"- {line}")
    return "\n".join(lines)


def as_numbered_list(text: str) -> str:
    """Turn loose lines into an ordered list, numbering them if needed."""
    lines = []
    counter = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.match(r"^([-*+]|\d+[.)])\s+", line):
            # Keep anything already numbered or bulleted as-is.
            lines.append(line)
            counter = 0
            continue
        counter += 1
        lines.append(f"{counter}. {line}")
    return "\n".join(lines)


def build_markdown(fields: dict, image_name: str) -> str:
    title = flatten(fields["title"])
    described = flatten(fields["description"])

    tags = []
    for raw in re.split(r"[,\n]", fields["tags"]):
        tag = flatten(raw).lower()
        # Keep tags simple: letters, numbers, spaces and hyphens.
        tag = re.sub(r"[^a-z0-9 \-]", "", tag).strip()
        if tag and tag not in tags:
            tags.append(tag)

    parts = [
        "---",
        f"title: {yaml_string(title)}",
        f"date: {datetime.now(timezone.utc):%Y-%m-%d}",
        f"image: {yaml_string(image_name)}",
    ]
    if tags:
        parts.append("tags:")
        parts.extend(f"  - {yaml_string(tag)}" for tag in tags)
    parts.append("---")
    parts.append("")

    if described:
        parts.append(described)
        parts.append("")

    if fields["ingredients"]:
        parts.append("## Ingredients")
        parts.append("")
        parts.append(as_bullet_list(fields["ingredients"]))
        parts.append("")

    if fields["method"]:
        parts.append("## Method")
        parts.append("")
        parts.append(as_numbered_list(fields["method"]))
        parts.append("")

    if fields["notes"]:
        parts.append("## Notes")
        parts.append("")
        parts.append(indent_block(fields["notes"]))
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def unique_dir(base: Path) -> Path:
    """Avoid clobbering an existing recipe with the same name."""
    if not base.exists():
        return base
    for n in range(2, 100):
        candidate = base.with_name(f"{base.name}-{n}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"could not find a free directory name near {base}")


TITLE_RE = re.compile(r"""^\s*title:\s*(?P<value>.*?)\s*$""", re.MULTILINE)


def existing_titles() -> list:
    """Every recipe title already in the content tree, for duplicate checking."""
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


def normalise(text: str) -> str:
    """Compare titles ignoring case, punctuation and spacing."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def find_duplicate(title: str):
    """Return the existing title that clashes with this one, if any."""
    wanted = normalise(title)
    if not wanted:
        return None
    for existing in existing_titles():
        if normalise(existing) == wanted:
            return existing
    return None


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    if not body.strip():
        print("ERROR: ISSUE_BODY is empty", file=sys.stderr)
        return 1

    fields = parse_issue_body(body)
    title = flatten(fields["title"])

    if not title:
        # Machine-readable so the workflow can explain this kindly rather than
        # posting a confusing generic failure.
        print("ERROR: no recipe name was filled in", file=sys.stderr)
        print("RESULT:missing-title")
        return 0

    duplicate = find_duplicate(title)
    if duplicate:
        print(f"ERROR: a recipe called '{duplicate}' already exists", file=sys.stderr)
        print(f"RESULT:duplicate:{duplicate}")
        return 0

    photo_status = os.environ.get("PHOTO_STATUS", "").strip()
    image_name = os.environ.get("PHOTO_NAME", "image.jpeg").strip() or "image.jpeg"

    slug = slugify(title)
    if not slug or slug == "recipe":
        slug = slugify(os.environ.get("ISSUE_TITLE", ""))

    out_dir = unique_dir(CONTENT_ROOT / slug)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "index.md").write_text(
        build_markdown(fields, image_name), encoding="utf-8", newline="\n"
    )

    if photo_status == "saved":
        print(f"wrote {out_dir} with photo {image_name}", file=sys.stderr)
    else:
        print(f"wrote {out_dir} with no photo", file=sys.stderr)

    # Consumed by the workflow.
    print(f"RESULT:created")
    print(f"dir={out_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
