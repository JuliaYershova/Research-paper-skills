"""Tests for the paper-audit scripts.

Run from the skill folder:  python3 -m unittest discover -s tests -v

The fixture paper (tests/fixtures/main.tex) contains the LaTeX cases that broke
earlier versions: thousands separators, ranges, bounds, macros, multi-line
author blocks, comments, code listings, lengths, names with digits, included
files, tables with \\multicolumn and a missing cell, and a broken .bib.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
FIX = HERE / "fixtures"


def run(script, *args, expect_ok=True):
    result = subprocess.run([sys.executable, "-I", str(SCRIPTS / script), *map(str, args)],
                            capture_output=True, text=True)
    if expect_ok and result.returncode != 0:
        raise AssertionError(f"{script} failed:\n{result.stderr}")
    return result


class TexInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = json.loads(run("tex_inventory.py", FIX / "main.tex").stdout)
        cls.numbers = [n["text"] for n in cls.inv["numbers"]]

    def test_included_file_is_read(self):
        self.assertEqual([Path(f).name for f in self.inv["files"]], ["main.tex", "results.tex"])
        self.assertIn("0.456", self.numbers)

    def test_reported_values_are_found(self):
        for value in ["0.873", "12.5\\%", "-0.25", "0.03", "3.25", "6.50", "240", "120"]:
            self.assertIn(value, self.numbers, value)

    def test_thousands_separator_is_joined(self):
        self.assertIn("1024", self.numbers)
        self.assertNotIn("024", self.numbers)

    def test_range_gives_both_ends(self):
        self.assertIn("0.004", self.numbers)
        self.assertIn("0.010", self.numbers)

    def test_bound_is_marked(self):
        bounds = {n["text"]: n["bound"] for n in self.inv["numbers"] if n["bound"]}
        self.assertEqual(bounds, {"0.001": "<"})

    def test_number_defining_macro_is_kept(self):
        self.assertIn("0.912", self.numbers)

    def test_non_results_are_skipped(self):
        # comment, code listing, author block, lengths, names and versions
        for value in ["0.999", "1000", "160", "00", "12", "0.5", "200", "2011", "0.1.14", "14"]:
            self.assertNotIn(value, self.numbers, value)

    def test_line_numbers(self):
        lines_of = {}
        for n in self.inv["numbers"]:
            lines_of.setdefault(n["text"], []).append(n["line"])
        self.assertEqual(lines_of["0.873"], [8, 23])      # text and table
        self.assertEqual(lines_of["6.50"], [13])

    def test_todo_spanning_lines(self):
        self.assertEqual(len(self.inv["todos"]), 1)
        self.assertEqual(self.inv["todos"][0]["text"], "Fix the {nested} braces here on two lines")

    def test_citations_and_refs(self):
        self.assertEqual(sorted(c["key"] for c in self.inv["citations"]), ["known", "unknown"])
        self.assertEqual(sorted(r["key"] for r in self.inv["refs"]), ["tab:a", "tab:none"])


class TraceNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            inv = Path(tmp) / "inv.json"
            inv.write_text(run("tex_inventory.py", FIX / "main.tex").stdout)
            out = run("trace_numbers.py", inv, FIX / "results" / "report.json",
                      "--also", FIX / "other").stdout
        cls.report = json.loads(out)

    def texts(self, category):
        return {n["text"] for n in self.report[category]}

    def test_primary_matches_at_paper_precision(self):
        # 0.8731 -> 0.873, 3.2511 -> 3.25, 12.5% = err_pct, 1024 after joining
        self.assertTrue({"0.873", "3.25", "12.5\\%", "1024", "240"} <= self.texts("in_primary"))

    def test_long_lists_count_as_other(self):
        self.assertIn("0.456", self.texts("only_other"))        # only in a 22-value fold list

    def test_other_files(self):
        self.assertIn("6.50", self.texts("only_other"))         # only in config.py

    def test_not_found(self):
        self.assertTrue({"0.004", "0.010", "-0.25"} <= self.texts("not_found"))

    def test_bounds_are_not_traced(self):
        self.assertEqual(self.texts("bounds"), {"0.001"})


class BibInventory(unittest.TestCase):
    def test_bib_problems(self):
        r = json.loads(run("bib_inventory.py", FIX / "main.tex", FIX / "refs.bib").stdout)
        self.assertEqual(list(r["cited_missing_from_bib"]), ["unknown"])
        self.assertEqual([e["key"] for e in r["never_cited"]], ["unused"])
        self.assertEqual(r["duplicate_keys"], {"known": [1, 4]})
        self.assertEqual([t["text"] for t in r["text_outside_entries"]], ["stray pasted text here"])


class CheckSource(unittest.TestCase):
    def test_problems_found(self):
        r = run("check_source.py", FIX / "main.tex", FIX / "refs.bib", expect_ok=False)
        self.assertEqual(r.returncode, 1)
        lines = r.stdout.strip().splitlines()
        self.assertEqual(len(lines), 3, r.stdout)
        self.assertTrue(any("2 cells, column spec has 3" in l for l in lines))
        self.assertTrue(any("tab:none" in l for l in lines))
        self.assertTrue(any("'unknown'" in l for l in lines))

    def test_clean_file_passes(self):
        r = run("check_source.py", FIX / "old.tex")
        self.assertEqual(r.stdout.strip(), "")


class DeletedText(unittest.TestCase):
    def test_deletion_and_commented_out_text(self):
        out = run("deleted_text.py", FIX / "old.tex", FIX / "new.tex").stdout
        self.assertIn("Second sentence is removed.", out)
        # the trailing comment in new.tex must not hide anything or count as text
        self.assertNotIn("Third sentence stays. Third", out)


class CheckQuotes(unittest.TestCase):
    def test_found_moved_missing(self):
        findings = [
            {"file": str(FIX / "main.tex"), "line": 8, "quote": "We reach 0.873 accuracy"},
            {"file": str(FIX / "main.tex"), "line": 1, "quote": "Missing ref"},
            {"file": str(FIX / "main.tex"), "line": 8, "quote": "an invented sentence"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f.json"
            path.write_text(json.dumps(findings))
            r = run("check_quotes.py", path, expect_ok=False)
        lines = r.stdout.splitlines()
        self.assertIn("FOUND", lines[0])
        self.assertIn("MOVED to line", lines[1])
        self.assertIn("NOT FOUND", lines[2])
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
