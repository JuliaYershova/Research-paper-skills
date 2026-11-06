"""Structural checks on LaTeX sources that do not need a compiler.

Usage: python3 -I check_source.py main.tex [refs.bib ...]

Checks: unbalanced braces per file, \\begin/\\end mismatches, references
without a label, citations missing from the .bib files (if given), and
tabular rows whose number of cells differs from the column specification.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texutil import find_group, read_lines, source_files  # noqa: E402

BEGIN_END_RE = re.compile(r"\\(begin|end)\{([^}]+)\}")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|pageref)\{([^}]*)\}")
CITE_RE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
BIBKEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,")
TABULAR_RE = re.compile(r"\\begin\{(tabular\*?|tabularx|longtable)\}")
MULTICOL_RE = re.compile(r"\\multicolumn\{(\d+)\}")
RULE_RE = re.compile(r"^\s*\\(?:toprule|midrule|bottomrule|hline|cline|cmidrule|addlinespace)")


def count_columns(spec):
    """Number of columns in a tabular column specification."""
    s = spec
    s = re.sub(r"[@!<>]\s*\{", "\x00{", s)        # @{..} !{..} >{..} <{..} add no column
    out, i = [], 0
    while i < len(s):
        if s[i] == "\x00":
            i = find_group(s, i + 1)
            continue
        if s[i] == "{":
            i = find_group(s, i)
            continue
        out.append(s[i])
        i += 1
    s = "".join(out)
    total = 0
    for m in re.finditer(r"\*\s*(\d+)", spec):    # *{3}{c}
        total += int(m.group(1)) - 1
    return total + sum(1 for ch in s if ch.isalpha())


def check_tables(path, text, problems):
    for m in TABULAR_RE.finditer(text):
        pos = m.end()
        if m.group(1) in ("tabular*", "tabularx"):
            pos = find_group(text, text.index("{", pos))       # width argument
        brace = text.index("{", pos)
        spec_end = find_group(text, brace)
        ncols = count_columns(text[brace + 1:spec_end - 1])
        end = text.find("\\end{" + m.group(1) + "}", spec_end)
        body = text[spec_end:end if end >= 0 else len(text)]
        offset = text.count("\n", 0, spec_end) + 1
        for row in re.split(r"\\\\(?:\[[^\]]*\])?", body):
            lines = [l for l in row.split("\n") if l.strip() and not RULE_RE.match(l)]
            cell_text = " ".join(lines).strip()
            if not cell_text:
                continue
            cells = 1 + len(re.findall(r"(?<!\\)&", cell_text))
            for mc in MULTICOL_RE.finditer(cell_text):
                cells += int(mc.group(1)) - 1
            if cells != ncols:
                line = offset + body[:body.find(row)].count("\n") if row in body else offset
                problems.append(f"{path.name}:{line}: table row has {cells} cells, "
                                f"column spec has {ncols}: {cell_text[:70]}")


def main(main_tex, bibs):
    problems, labels, refs, cites = [], set(), [], []
    for path in source_files(main_tex):
        lines = read_lines(path)
        text = "\n".join(lines)
        depth = 0
        for n, line in enumerate(lines, start=1):
            depth += len(re.findall(r"(?<!\\)\{", line)) - len(re.findall(r"(?<!\\)\}", line))
            if depth < 0:
                problems.append(f"{path.name}:{n}: closing brace without opening brace")
                depth = 0
            labels.update(LABEL_RE.findall(line))
            refs += [(path.name, n, k) for k in REF_RE.findall(line)]
            cites += [(path.name, n, k.strip()) for g in CITE_RE.findall(line) for k in g.split(",") if k.strip()]
        if depth:
            problems.append(f"{path.name}: {depth} unclosed brace(s) at end of file")
        stack = []
        for n, line in enumerate(lines, start=1):
            for kind, env in BEGIN_END_RE.findall(line):
                if kind == "begin":
                    stack.append((env, n))
                elif not stack or stack[-1][0] != env:
                    opened = ("\\begin{%s} at line %d" % stack[-1]) if stack else "any begin"
                    problems.append("%s:%d: \\end{%s} does not match %s" % (path.name, n, env, opened))
                else:
                    stack.pop()
        for env, n in stack:
            problems.append(f"{path.name}:{n}: \\begin{{{env}}} is never closed")
        check_tables(path, text, problems)

    for f, n, k in refs:
        if k not in labels:
            problems.append(f"{f}:{n}: \\ref{{{k}}} has no \\label")
    if bibs:
        keys = set()
        for b in bibs:
            keys.update(BIBKEY_RE.findall(Path(b).read_text(encoding="utf-8", errors="replace")))
        for f, n, k in cites:
            if k not in keys:
                problems.append(f"{f}:{n}: citation '{k}' not in the .bib files")

    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
