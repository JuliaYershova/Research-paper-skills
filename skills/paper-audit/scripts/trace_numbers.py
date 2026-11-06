"""Find where each number in the paper appears in the result files.

Usage: python3 -I trace_numbers.py inventory.json PRIMARY [PRIMARY ...] [--also OTHER ...]

PRIMARY: the files or folders that hold the reported results (summary tables,
report JSON). OTHER (optional): everything else that may contain a source,
such as code, configs, logs, per-item outputs.

Reads JSON, notebooks, CSV/TSV, code, config and plain-text files (skipping
hidden folders such as .ipynb_checkpoints) and indexes every numeric value that
stands on its own (digits inside names, paths and version strings are ignored).
A paper number matches a source value when the source value, rounded to the
paper's number of decimals, equals it. Percentages also match fractions
(98.9% ~ 0.989). Integers below 10 are reported separately.

Categories:
  in_primary      found in a PRIMARY file. Still confirm the field means what
                  the paper says.
  only_other      found only in OTHER files, or only inside long lists
                  (more than 20 values, e.g. per-fold scores) of a PRIMARY file. With many values there, this is
                  often a coincidence: confirm by hand or treat as not found.
  not_found       no source contains it.
  bounds          numbers written as a bound (p < 0.001, \\approx 3): not traced,
                  check by hand that the source value satisfies the bound.
  small_integers  not traced.
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# A value that stands on its own: not part of a name, path or version string.
NUM_RE = re.compile(r"(?<![\w.\-/:])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w.\-/:])")
MAX_DECIMALS = 6
MAX_HITS_PER_KEY = 20
LONG_LIST = 20      # values inside longer lists (per fold, per item) count as "other"
TEXT_SUFFIXES = (".txt", ".md", ".log", ".yaml", ".yml", ".py", ".toml", ".cfg", ".ini", ".r", ".jl")


def parse_paper_number(text):
    t = text.replace("\\%", "").replace("%", "").replace("−", "-").replace("{,}", "")
    if t.count(",") == 1 and t.count(".") == 0 and len(t.split(",")[1]) != 3:
        t = t.replace(",", ".")          # decimal comma
    t = t.replace(",", "")               # thousands separator
    try:
        value = float(t)
    except ValueError:
        return None, None
    decimals = len(t.split(".")[1]) if "." in t else 0
    return value, decimals


def key(value, decimals):
    return (decimals, round(value, decimals))


class Index:
    def __init__(self):
        self.hits = defaultdict(list)
        self.values = 0

    weak = False

    def add(self, value, where):
        if value != value or abs(value) == float("inf"):
            return
        self.values += 1
        for d in range(MAX_DECIMALS + 1):
            k = key(value, d)
            if len(self.hits[k]) < MAX_HITS_PER_KEY:
                self.hits[k].append((self.weak, where))

    def walk_json(self, obj, path, where):
        if isinstance(obj, dict):
            for k, v in obj.items():
                self.walk_json(v, f"{path}.{k}" if path else str(k), where)
        elif isinstance(obj, list):
            outer = self.weak
            self.weak = outer or len(obj) > LONG_LIST
            for i, v in enumerate(obj):
                self.walk_json(v, f"{path}[{i}]", where)
            self.weak = outer
        elif isinstance(obj, bool):
            return
        elif isinstance(obj, (int, float)):
            self.add(float(obj), f"{where} :: {path}")
        elif isinstance(obj, str):
            self.text(obj, f"{where} :: {path}")

    def text(self, s, where):
        for m in NUM_RE.finditer(s):
            try:
                self.add(float(m.group(0)), where)
            except ValueError:
                pass

    def load(self, path):
        name = str(path)
        suffix = path.suffix.lower()
        try:
            if suffix in (".json", ".ipynb"):
                self.walk_json(json.loads(path.read_text(encoding="utf-8")), "", name)
            elif suffix in (".csv", ".tsv"):
                with open(path, newline="", encoding="utf-8", errors="replace") as f:
                    rows = csv.reader(f, delimiter="\t" if suffix == ".tsv" else ",")
                    header = next(rows, [])
                    for r, row in enumerate(rows, start=2):
                        for c, cell in enumerate(row):
                            col = header[c] if c < len(header) else c
                            self.text(cell, f"{name} :: row {r}, column {col}")
            elif suffix in TEXT_SUFFIXES:
                for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    self.text(line, f"{name}:{n}")
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"skipped {name}: {e}", file=sys.stderr)


def main(inventory_path, primary, other):
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    index = Index()
    files = 0
    for folder, weak in [(Path(f), False) for f in primary] + [(Path(f), True) for f in other]:
        index.weak = weak
        paths = [folder] if folder.is_file() else sorted(folder.rglob("*"))
        for path in paths:
            parts = path.relative_to(folder).parts if folder.is_dir() else ()
            if path.is_file() and not any(p.startswith(".") for p in parts):
                index.load(path)
                files += 1

    matched, weak_only, unmatched, small, bounds = [], [], [], [], []
    for entry in inventory["numbers"]:
        value, decimals = parse_paper_number(entry["text"])
        if value is None:
            continue
        hits = list(index.hits.get(key(value, decimals), []))
        if entry["percent"]:
            hits += index.hits.get(key(value / 100, decimals + 2), [])
        hits.sort(key=lambda h: h[0])                 # primary first
        item = {**entry, "value": value, "n_matches": len(hits),
                "matches": [("other: " if w else "") + where for w, where in hits[:5]]}
        if entry.get("bound"):
            bounds.append(item)
        elif decimals == 0 and abs(value) < 10:
            small.append(item)
        elif any(not w for w, _ in hits):
            matched.append(item)
        elif hits:
            weak_only.append(item)
        else:
            unmatched.append(item)

    report = {"source_files": files, "source_values": index.values,
              "not_found": unmatched, "only_other": weak_only, "in_primary": matched,
              "bounds": bounds, "small_integers": small}
    json.dump(report, sys.stdout, indent=1, ensure_ascii=False)
    print(f"\n{files} source files, {index.values} values | paper numbers: "
          f"{len(matched)} in primary, {len(weak_only)} only in other files, {len(unmatched)} not found, "
          f"{len(bounds)} bounds, {len(small)} small integers "
          f"(not traced)", file=sys.stderr)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--also" in args:
        k = args.index("--also")
        args, other = args[:k], args[k + 1:]
    else:
        other = []
    if len(args) < 2:
        sys.exit(__doc__)
    main(args[0], args[1:], other)
