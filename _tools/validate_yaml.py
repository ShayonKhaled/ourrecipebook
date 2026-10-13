"""Validate the workflow and issue-form YAML files.

GitHub Actions uses YAML 1.2, where a bare `on` key is a plain string. PyYAML
implements YAML 1.1 and resolves it to the boolean True, which would make every
workflow look broken, so that one resolver is disabled here.

Run from the project root (needs PyYAML):

    python _tools/validate_yaml.py
"""

import sys

import yaml


class GitHubLoader(yaml.SafeLoader):
    """SafeLoader with boolean resolution removed for keys like `on`."""


for _first, _resolvers in list(GitHubLoader.yaml_implicit_resolvers.items()):
    GitHubLoader.yaml_implicit_resolvers[_first] = [
        (tag, regexp)
        for tag, regexp in _resolvers
        if tag != "tag:yaml.org,2002:bool"
    ]


FILES = [
    ".github/workflows/recipe-from-issue.yml",
    ".github/workflows/hugo.yml",
    ".github/ISSUE_TEMPLATE/new-recipe.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
]


def main() -> int:
    ok = True

    for path in FILES:
        try:
            with open(path, encoding="utf-8") as handle:
                doc = yaml.load(handle, Loader=GitHubLoader)
        except Exception as exc:  # noqa: BLE001 - report and continue
            ok = False
            print(f"FAIL {path}: {exc}")
            continue

        print(f"OK   {path}")

        if "workflows" in path:
            triggers = doc.get("on") or {}
            if not triggers:
                ok = False
                print("     ERROR: no 'on' trigger found")
            else:
                names = list(triggers.keys()) if isinstance(triggers, dict) else triggers
                print(f"     triggers: {names}")

            for job, spec in (doc.get("jobs") or {}).items():
                steps = spec.get("steps", []) if isinstance(spec, dict) else []
                print(f"     job '{job}': {len(steps)} steps")
                for step in steps:
                    if "run" not in step and "uses" not in step:
                        ok = False
                        print(f"       ERROR: step has neither run nor uses: {step}")

        if "ISSUE_TEMPLATE/new-recipe" in path:
            body = doc.get("body") or []
            ids = [e["id"] for e in body if "id" in e]
            print(f"     fields: {[(e['type'], e.get('id', '-')) for e in body]}")
            duplicates = sorted({i for i in ids if ids.count(i) > 1})
            print(f"     duplicate ids: {duplicates or 'none'}")
            print(f"     top-level keys: {sorted(doc.keys())}")

    print("\nALL PARSED OK" if ok else "\nERRORS PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
