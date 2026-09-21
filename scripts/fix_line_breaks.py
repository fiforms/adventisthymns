#!/usr/bin/env python3
"""Fix markdown hard-line-break trailing spaces within each slide (verse block).

A slide/block is a maximal run of consecutive lines that are neither blank
(possibly whitespace-only) nor a bare "---" separator. Within each block,
every line except the last must end with two trailing spaces (a Markdown
hard line break); the last line of the block must NOT end with trailing
spaces.
"""
import sys
from pathlib import Path


def is_separator(line: str) -> bool:
    stripped = line.rstrip("\n")
    return stripped.strip() == "" or stripped.strip() == "---"


def normalize_separators(lines: list[str]) -> list[str]:
    """Ensure every bare "---" separator has a blank line before and after it."""
    result = []
    pending_blank_after = False
    for line in lines:
        if pending_blank_after and line.strip() != "":
            result.append("")
        pending_blank_after = False

        if line.strip() == "---":
            if result and result[-1].strip() != "":
                result.append("")
            result.append(line)
            pending_blank_after = True
        else:
            result.append(line)
    return result


def fix_text(text: str) -> tuple[str, bool]:
    had_trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if had_trailing_newline:
        lines = lines[:-1]

    lines = normalize_separators(lines)

    # Group indices into blocks of consecutive non-separator lines.
    blocks = []
    current = []
    for i, line in enumerate(lines):
        if is_separator(line):
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(i)
    if current:
        blocks.append(current)

    for block in blocks:
        for pos, idx in enumerate(block):
            is_last = pos == len(block) - 1
            content = lines[idx].rstrip(" ")
            lines[idx] = content if is_last else content + "  "

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
