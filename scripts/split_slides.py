#!/usr/bin/env python3
"""Split overlong hymn-verse slide blocks into slides of at most 4 lyric
lines each, choosing break points that follow the hymn's meter/punctuation
rather than a fixed line count.

A block is the text between two `---` separators. Each block may start
with a label line like `_Verse 1_` or `_Refrain_`; the label is never
counted toward the 4-line limit and always stays attached to the first
slide of its verse.

Within a block, candidate slides (1-4 lyric lines each) are scored and
the lowest-total-cost partition is chosen via dynamic programming:
  - slides ending on strong punctuation (. ! ? ; : -- --) score best,
  - slides ending on a comma score worse,
  - slides ending with no punctuation at all score worst,
  - 1-line slides carry a heavy penalty so a trailing orphan line (e.g. a
    lone "Amen.") gets folded into a neighboring slide instead of left
    standing alone; 2-line slides carry a small penalty; 3- and 4-line
    slides are free.
This tends to reproduce natural stanza/couplet/quatrain breaks instead of
a naive "every 4 lines" cut.

Usage: split_slides.py FILE.md [FILE2.md ...]
Blocks that already have <=4 lyric lines are left untouched.
"""
import re
import sys

LABEL_RE = re.compile(r'^_[^_]+_\s*$')
# Colons are excluded from STRONG_CHARS: in these hymn texts a
# line-ending colon almost always introduces the line that follows
# (e.g. "This my song thro' endless ages: / Jesus led me all the way;"),
# so it is treated as a continuation like a comma, not a full stop.
STRONG_CHARS = set('.!?;—–')
WEAK_CHARS = set(',:')
CLOSERS = set('"”’\')')

MAX_SLIDE_LINES = 4
SIZE_COST = {1: 5, 2: 1, 3: 0, 4: 0}
STRONG_END_COST = 0
WEAK_END_COST = 2
NO_END_COST = 3


def strip_trailing_closers(s):
    s = s.rstrip()
    while s and s[-1] in CLOSERS:
        s = s[:-1]
    return s


def strong_end(line):
    s = strip_trailing_closers(line)
    return bool(s) and s[-1] in STRONG_CHARS


def weak_end(line):
    s = strip_trailing_closers(line)
    return bool(s) and s[-1] in WEAK_CHARS


def end_cost(line):
    if strong_end(line):
        return STRONG_END_COST
    if weak_end(line):
        return WEAK_END_COST
    return NO_END_COST


def chunk_cost(lines, a, b):
    size = b - a
    return SIZE_COST[size] + end_cost(lines[b - 1])


def group_lines(lines):
    """Partition lines into chunks of size 1..MAX_SLIDE_LINES minimizing
    total cost, via dynamic programming. Returns a list of line-lists."""
    n = len(lines)
    INF = float('inf')
    dp = [INF] * (n + 1)
    dp[0] = 0
    back = [None] * (n + 1)
    for i in range(1, n + 1):
        for size in range(1, MAX_SLIDE_LINES + 1):
            a = i - size
            if a < 0:
                continue
            cost = dp[a] + chunk_cost(lines, a, i)
            if cost < dp[i]:
                dp[i] = cost
                back[i] = a

    groups = []
    i = n
    while i > 0:
        a = back[i]
        groups.append(lines[a:i])
        i = a
    groups.reverse()
    return groups


def render_group(lines):
    out = []
    for idx, line in enumerate(lines):
        text = line.rstrip()
        if idx != len(lines) - 1:
            text += '  '
        out.append(text)
    return out


def process_block(block_text):
    raw_lines = block_text.split('\n')
    while raw_lines and raw_lines[0].strip() == '':
        raw_lines.pop(0)
    while raw_lines and raw_lines[-1].strip() == '':
        raw_lines.pop()
    if not raw_lines:
        return None  # nothing to do, leave block untouched

    label = None
    lyric = raw_lines
    if LABEL_RE.match(raw_lines[0].strip()):
        label = raw_lines[0].rstrip()
        lyric = raw_lines[1:]

    if len(lyric) <= MAX_SLIDE_LINES:
        return None  # already fine

    groups = group_lines(lyric)
    sub_blocks = []
    for gi, g in enumerate(groups):
        rendered = render_group(g)
        if gi == 0 and label is not None:
            label_text = label.rstrip()
            if not label_text.endswith('  '):
                label_text += '  '
            rendered = [label_text] + rendered
        sub_blocks.append('\n'.join(rendered))
    return sub_blocks


def process_file(path):
    with open(path, encoding='utf-8') as f:
        content = f.read()

    parts = re.split(r'\n\s*\n---\s*\n\s*\n', content)
    changed = False
    new_parts = []
    for part in parts:
        result = process_block(part)
        if result is None:
            new_parts.append(part.strip('\n'))
        else:
            changed = True
            new_parts.append(result)

    if not changed:
        return False

    flat_blocks = []
    for p in new_parts:
        if isinstance(p, list):
            flat_blocks.extend(p)
        else:
            flat_blocks.append(p)

    new_content = ('\n\n---\n\n'.join(flat_blocks)) + '\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True


if __name__ == '__main__':
    for path in sys.argv[1:]:
        did = process_file(path)
        print(f"{'CHANGED' if did else 'unchanged'}: {path}")
