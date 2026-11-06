"""Shared helpers for the paper-audit scripts: reading LaTeX sources.

Standard library only, Python 3.9+.
"""

import re
from pathlib import Path

INPUT_RE = re.compile(r"\\(?:input|include|subfile)\{([^}]+)\}")


def strip_comment(line):
    """Remove a LaTeX comment (an unescaped %) from one line."""
    out = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            out.append(line[i:i + 2])
            i += 2
            continue
        if ch == "%":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def read_lines(path):
    """The file's lines with comments removed, keeping line numbers."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return [strip_comment(line) for line in text.splitlines()]


def source_files(main):
    """The main file and every file it includes, in order, without repeats."""
    main = Path(main)
    seen, order = set(), []

    def visit(path):
        path = path if path.suffix else path.with_suffix(".tex")
        if path in seen or not path.exists():
            return
        seen.add(path)
        order.append(path)
        for line in read_lines(path):
            for name in INPUT_RE.findall(line):
                visit((main.parent / name.strip()))

    visit(main)
    return order


def find_group(text, start):
    """Index just past the brace group that opens at text[start] == '{'."""
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)
