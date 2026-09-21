#!/usr/bin/env python3
"""Uppercase the first letter of every line in the hymn markdown files.

Leading non-letter characters (quotes, punctuation, markdown "_", etc.)
are left untouched; the first alphabetic character found on each line
is uppercased.
"""
import re
import sys
from pathlib import Path

FIRST_LETTER = re.compile(r"[a-zA-Z]")


def fix_text(text: str) -> tuple[str, bool]:
    had_trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if had_trailing_newline:
        lines = lines[:-1]

    for i, line in enumerate(lines):
        lines[i] = FIRST_LETTER.sub(lambda m: m.group(0).upper(), line, count=1)

    new_text = "\n".join(lines)
    if had_trailing_newline:
        new_text += "\n"
    return new_text, new_text != text


def main():
    files = sys.argv[1:]
    if not files:
        files = sorted(str(p) for p in Path(".").glob("*.md"))

    total_changed = 0
    for f in files:
        path = Path(f)
        text = path.read_text()
        new_text, changed = fix_text(text)
        if changed:
            path.write_text(new_text)
            total_changed += 1
            print(f"fixed: {f}")

    print(f"\n{total_changed} file(s) changed out of {len(files)}")


if __name__ == "__main__":
    main()
