"""List every number, todo, citation, label and reference in a LaTeX paper.

Usage: python3 -I tex_inventory.py main.tex > inventory.json

Comments are ignored. Numbers inside \\label, \\ref, \\cite, \\url and file
names are skipped. Each number keeps its file, line and a short context.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texutil import find_group, read_lines, source_files  # noqa: E402

# A number not glued to a word, path or name (skips CUB-200, 1938/4, v0.1.14).
NUMBER_RE = re.compile(r"(?<![\w.\-/:])[-\u2212]?\d+(?:[.,]\d+)*(?:\\?%)?(?![\w.\-/])")
LENGTH_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:\\(?:line|text|column|paper)width|"
                       r"\\(?:text|paper)height|pt|cm|mm|em|ex|in|bp)\b")
VERBATIM_ENVS = ("lstlisting", "verbatim", "minted", "Verbatim", "comment")
MACRO_RE = re.compile(r"\\(?:newcommand|renewcommand|providecommand|def)\*?\s*\{?\\[A-Za-z@]+\}?(?:\[[^\]]*\])*\{")
BOUND_RE = re.compile(r"(?:<|>|\\le(?:q|qslant)?|\\ge(?:q|qslant)?|\\lesssim|\\gtrsim|\\approx|\\sim|\\ll|\\gg)\s*\$?\s*$")
SKIP_ARGS_RE = re.compile(
    r"\\(?:label|ref|eqref|autoref|cref|Cref|pageref|cite[pt]?|citeauthor|citeyear|url|href|"
    r"input|include|includegraphics|bibliography|bibliographystyle|usepackage|documentclass|"
    r"todo|definecolor|hspace|vspace|setlength|author|address|email|"
    r"editor|jmlrheading|ShortHeadings|firstpageno|thanks|date)\*?(?:\[[^\]]*\])*\{")
CITE_RE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|pageref)\{([^}]*)\}")
TODO_RE = re.compile(r"\\todo(?:\[[^\]]*\])?\{")


def blank(chars, start, end):
    for i in range(start, end):
        if chars[i] != "\n":
            chars[i] = " "


def mask(text, keep_preamble_macros):
    """Blank out everything whose numbers are not reported values, keeping line breaks.

    Skips: arguments of labels, refs, cites, sizes, author blocks and similar;
    lengths (0.5\\linewidth, 2cm); code listings and verbatim blocks; and, for the
    main file, the preamble except number-defining macros (\\newcommand{\\acc}{0.91}).
    """
    chars = list(text)
    for m in SKIP_ARGS_RE.finditer(text):
        blank(chars, m.start(), find_group(text, m.end() - 1))
    for env in VERBATIM_ENVS:
        for m in re.finditer(r"\\begin\{%s\}" % env, text):
            end = text.find("\\end{%s}" % env, m.end())
            blank(chars, m.start(), end if end >= 0 else len(text))
    for m in LENGTH_RE.finditer(text):
        blank(chars, m.start(), m.end())
    if keep_preamble_macros is not None:
        begin = text.find("\\begin{document}")
        end_doc = text.find("\\end{document}")
        macros = [(m.start(), find_group(text, text.index("{", m.end() - 1)))
                  for m in MACRO_RE.finditer(text, 0, max(begin, 0))]
        keep = set()
        for a, b in macros:
            keep.update(range(a, b))
        for i in range(0, max(begin, 0)):
            if i not in keep and chars[i] != "\n":
                chars[i] = " "
        if end_doc >= 0:
            blank(chars, end_doc, len(text))
    return "".join(chars)


def normalise(text):
    """Join split numbers (1{,}024, 1\\,024) and separate ranges (0.004--0.010).

    Keeps every line break where it was, so line numbers stay correct.
    """
    text = re.sub(r"(?<=\d)\{,\}(?=\d)", lambda m: " " * 0, text)
    text = re.sub(r"(?<=\d)\\,(?=\d{3})", "", text)
    text = re.sub(r"(?<=\d)-{2,3}(?=[\d\-])", lambda m: " " * len(m.group(0)), text)
    return text


def todos_in(path, raw):
    """Todos with their full text (they can span lines)."""
    found = []
    for m in TODO_RE.finditer(raw):
        end = find_group(raw, m.end() - 1)
        line = raw.count("\n", 0, m.start()) + 1
        found.append({"file": str(path), "line": line,
                      "text": " ".join(raw[m.end():end - 1].split())})
    return found


def main(main_tex):
    files = source_files(main_tex)
    inv = {"files": [str(f) for f in files], "numbers": [], "todos": [],
           "citations": [], "labels": [], "refs": []}
    for k, path in enumerate(files):
        lines = read_lines(path)
        text = "\n".join(lines)
        inv["todos"] += todos_in(path, text)
        for n, line in enumerate(lines, start=1):
            for m in CITE_RE.finditer(line):
                for key in m.group(1).split(","):
                    if key.strip():
                        inv["citations"].append({"file": str(path), "line": n, "key": key.strip()})
            for key in LABEL_RE.findall(line):
                inv["labels"].append({"file": str(path), "line": n, "key": key})
            for key in REF_RE.findall(line):
                inv["refs"].append({"file": str(path), "line": n, "key": key})
        normal = normalise(text)
        masked = mask(normal, True if k == 0 else None)
        for m in NUMBER_RE.finditer(masked):
            token = m.group(0)
            line_no = normal.count("\n", 0, m.start()) + 1
            before = normal[max(0, m.start() - 15):m.start()]
            bound = BOUND_RE.search(before)
            lo, hi = max(0, m.start() - 50), min(len(normal), m.end() + 50)
            inv["numbers"].append({
                "file": str(path), "line": line_no, "text": token,
                "percent": token.endswith("%"),
                "bound": bound.group(0).strip(" $") if bound else None,
                "context": " ".join(normal[lo:hi].split())})
    return inv


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    result = main(sys.argv[1])
    json.dump(result, sys.stdout, indent=1, ensure_ascii=False)
    print(f"\n{len(result['files'])} files, {len(result['numbers'])} numbers, "
          f"{len(result['todos'])} todos, {len(result['citations'])} citations, "
          f"{len(result['labels'])} labels, {len(result['refs'])} refs", file=sys.stderr)
