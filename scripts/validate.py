#!/usr/bin/env python3
"""Validate form.json and examples/*.json against schema.json."""
import glob
import json
import os
import sys

try:
    import jsonschema
except ImportError:
    sys.exit("Missing dependency: pip install jsonschema")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    schema = load(os.path.join(ROOT, "schema.json"))
    paths = [
        os.path.join(ROOT, "form.json"),
        os.path.join(ROOT, "form.en.json"),
    ] + sorted(
        glob.glob(os.path.join(ROOT, "examples", "**", "*.json"), recursive=True)
    )
    failed = False
    for path in paths:
        rel = os.path.relpath(path, ROOT)
        try:
            jsonschema.validate(load(path), schema)
            print("OK   " + rel)
        except jsonschema.ValidationError as exc:
            failed = True
            print("FAIL " + rel + ": " + exc.message)
    if failed:
        return 1
    print("\nAll valid: %d files" % len(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
