"""List all text deleted or replaced between two versions of a LaTeX file.

Usage: python3 -I deleted_text.py old.tex new.tex

Comments are removed first, so a line that was accidentally turned into a
comment shows up as deleted. Every deletion printed here must correspond to an
approved change.
"""

import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texutil import read_lines  # noqa: E402


def words_with_lines(path):
    words, lines = [], []
    for n, line in enumerate(read_lines(path), start=1):
        for w in line.split():
            words.append(w)
            lines.append(n)
    return words, lines


def main(old, new):
    a, a_lines = words_with_lines(old)
    b, _ = words_with_lines(new)
    count = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op in ("delete", "replace"):
            count += 1
            removed = " ".join(a[i1:i2])
            added = " ".join(b[j1:j2])
            print(f"old line {a_lines[i1]}: DELETED: {removed}")
            if op == "replace":
                print(f"{'':>{len(str(a_lines[i1])) + 10}}REPLACED BY: {added}")
    print(f"{count} deletion(s) or replacement(s)", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
