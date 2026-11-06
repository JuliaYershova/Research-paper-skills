"""Check that quotes in review findings really exist in the cited files.

Usage: python3 -I check_quotes.py findings.json

findings.json is a list of {"file": path, "line": number or null, "quote": text}.
Whitespace and line breaks are ignored when matching. Each quote is reported as
FOUND (within 15 lines of the given line), MOVED (elsewhere in the file, with
the real line), or NOT FOUND. A finding with a NOT FOUND quote must not be
reported without checking it by hand.
"""

import json
import re
import sys
from pathlib import Path

WINDOW = 15


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def locate(lines, quote):
    """Line numbers (1-based) where the normalised quote starts."""
    q = norm(quote)
    joined, starts = "", []
    for n, line in enumerate(lines, start=1):
        starts.append((len(joined), n))
        joined += norm(line) + " "
    hits, pos = [], joined.find(q)
    while pos >= 0 and q:
        line = max(n for offset, n in starts if offset <= pos)
        hits.append(line)
        pos = joined.find(q, pos + 1)
    return hits


def main(path):
    findings = json.loads(Path(path).read_text(encoding="utf-8"))
    bad = 0
    for i, f in enumerate(findings, start=1):
        try:
            lines = Path(f["file"]).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as e:
            print(f"[{i}] NOT FOUND  file cannot be read: {e}")
            bad += 1
            continue
        hits = locate(lines, f["quote"])
        given = f.get("line")
        if hits and (given is None or any(abs(h - given) <= WINDOW for h in hits)):
            status = "FOUND    "
        elif hits:
            status = f"MOVED to line {hits[0]}"
        else:
            status = "NOT FOUND"
            bad += 1
        print(f"[{i}] {status}  {Path(f['file']).name}:{given}  \"{f['quote'][:70]}\"")
    print(f"{len(findings)} quote(s), {bad} not found", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
