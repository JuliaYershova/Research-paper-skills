"""Compare the citations in a LaTeX paper with its BibTeX file.

Usage: python3 -I bib_inventory.py main.tex refs.bib [more.bib ...]

Reports cited keys missing from the .bib files, entries that are never cited,
duplicate keys, and text that sits outside any entry (pasted by accident).
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texutil import find_group, read_lines, source_files  # noqa: E402

CITE_RE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
NOCITE_RE = re.compile(r"\\nocite\{([^}]*)\}")
ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")


def cited_keys(main_tex):
    keys, nocite_all = {}, False
    for path in source_files(main_tex):
        for n, line in enumerate(read_lines(path), start=1):
            for group in CITE_RE.findall(line) + NOCITE_RE.findall(line):
                for k in group.split(","):
                    k = k.strip()
                    if k == "*":
                        nocite_all = True
                    elif k:
                        keys.setdefault(k, []).append(f"{path.name}:{n}")
    return keys, nocite_all


def bib_entries(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    entries, outside = [], []
    pos = 0
    for m in ENTRY_RE.finditer(text):
        if m.start() < pos:
            continue
        gap = text[pos:m.start()]
        for n, line in enumerate(gap.splitlines(), start=text.count("\n", 0, pos) + 1):
            s = line.strip()
            if s and not s.startswith("%"):
                outside.append({"file": str(path), "line": n, "text": s[:80]})
        brace = text.index("{", m.start())
        end = find_group(text, brace)
        entries.append({"key": m.group(2), "type": m.group(1).lower(), "file": str(path),
                        "line": text.count("\n", 0, m.start()) + 1})
        pos = end
    for n, line in enumerate(text[pos:].splitlines(), start=text.count("\n", 0, pos) + 1):
        s = line.strip()
        if s and not s.startswith("%"):
            outside.append({"file": str(path), "line": n, "text": s[:80]})
    return entries, outside


def main(main_tex, bibs):
    cited, nocite_all = cited_keys(main_tex)
    entries, outside = [], []
    for b in bibs:
        e, o = bib_entries(b)
        entries += e
        outside += o
    by_key = {}
    for e in entries:
        by_key.setdefault(e["key"], []).append(e)
    real = [e for e in entries if e["type"] not in ("string", "preamble", "comment")]
    report = {
        "cited_missing_from_bib": {k: v for k, v in cited.items() if k not in by_key},
        "never_cited": [] if nocite_all else
            [{"key": e["key"], "line": e["line"]} for e in real if e["key"] not in cited],
        "duplicate_keys": {k: [x["line"] for x in v] for k, v in by_key.items() if len(v) > 1},
        "text_outside_entries": outside,
        "counts": {"entries": len(real), "cited_keys": len(cited)},
    }
    json.dump(report, sys.stdout, indent=1, ensure_ascii=False)
    print(f"\n{len(real)} entries, {len(cited)} cited keys | missing: "
          f"{len(report['cited_missing_from_bib'])}, never cited: {len(report['never_cited'])}, "
          f"duplicates: {len(report['duplicate_keys'])}, stray text lines: {len(outside)}",
          file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
