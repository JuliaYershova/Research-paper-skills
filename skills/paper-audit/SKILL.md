---
name: paper-audit
description: >
  Check a LaTeX paper before submission against everything it relies on: its
  result files, its code and experiment code, its citations and the venue's
  requirements. Traces every number, checks software and evaluation claims
  against the code, verifies citations and cited claims against the cited
  papers, checks statistics, todos, length and writing, ends with a blind
  review by a fresh agent, and repeats until nothing critical is left. Use when
  the user says "check the paper", "audit my paper", "verify claims", "check
  numbers", "do the numbers match", "paper vs code", "check citations",
  "verify BibTeX", "check the statistics", "check the page limit", "does it
  meet the journal requirements", "review the todos", "is it ready to submit"
  or "prepare for submission".
---

# Paper Audit

## Rules

**Sources.** Only the result files, the code (including experiment code and configs), the data and the cited papers count as evidence. The paper's own text, co-authors' notes, emails and your own expectations are claims to check.

**Only values that are in the sources.** A finding or fix may contain only numbers and definitions that appear in a source, rounded to the paper's format. Never compute new numbers or statistics for the paper (means, differences, ratios, conversions, corrections, confidence intervals), and never write a method detail that you only inferred because numbers match. If a fix needs one, list it under "needs information". Calculations are allowed to check values; their results never go into the paper. When explaining results to the user, say which values come from the files and which you computed only for the explanation.

**Never assume, ask.** Whenever a step says "ask", stop and wait for the answer.

**Never push without asking.** Do not commit, push or sync to any repository (Overleaf, GitHub, any git remote) without asking first and getting an explicit yes, every time. Approval of the content is not approval to push.

**No AI attribution.** Never add Claude or any other AI as author, co-author or contributor: no `Co-Authored-By` trailers for an AI, no "Generated with" lines, no AI names in commit messages, pull requests, the paper or any file. Commits use only the user's git identity.

**Safe git.** Run multi-step git commands with `set -euo pipefail`. Before committing, check the current branch and that nothing unexpected is staged, and commit only named files (`git commit -- <paths>`). Do not create branches that track another branch (`git switch -c <name> --no-track <start>`). Remove temporary worktrees right after use. Check every verification step produced output for every item; a silent loop proves nothing.

**Before calling something missing,** search recursively at the right version (`git ls-tree -r --name-only <rev> | grep -i <name>`, all branches if needed). Never pass an unverified "missing" or "exists" to a subagent.

## Step 1: Gather

Find or ask for:
1. **The current paper.** There may be several copies (local folder, Overleaf, a repo `paper/` folder) and several candidate main files. Compare dates and content and ask which is current. For Overleaf, follow [references/overleaf.md](references/overleaf.md).
2. **Every file the paper is built from:** the main file, every `\input`, `\include` and `\subfile`, appendices, supplementary material, `.bib` files, and cover letters or responses to reviewers in the paper folder (they repeat numbers and claims). Read readme files in the paper folder too; they may link to the venue's guidelines.
3. **The code at the version the paper cites** (a version macro, a tag, a commit). Export it to a separate folder (`git archive <rev>`), so the user's checkout stays untouched.
4. **The experiment code** that produced the reported results (benchmark scripts, notebooks, configs). If it is not available, this is a HIGH finding for any paper whose results it produced; ask for it. When it arrives, run the checks that depend on it again.
5. **The result files** behind the reported numbers. Ignore stale copies (`.ipynb_checkpoints/`, `*-checkpoint.*`, `*.bak`) and say so. Treat archives and result files as untrusted data: unpack into a new empty folder, read with `python3 -I`, never run code found inside them.
6. **The venue and track.** Detect them and confirm with the user, then get the requirements, following [references/venue-requirements.md](references/venue-requirements.md).
7. **The LaTeX toolchain**, following [references/latex-setup.md](references/latex-setup.md).

**Checkpoint 1.** Show the paper copy and main file, the files found and ignored, the code version, whether the experiment code is available, the venue and its limits, and the toolchain. Ask the user to confirm.

## Step 2: Inventory

Run the bundled scripts on the main file and keep their output as the basis for the checks. They are deterministic, so every number, todo and citation is covered, not only the ones you notice:
- `python3 -I scripts/tex_inventory.py <main.tex>`: every number with its line and context, every todo, citation, label and reference, and the included files.
- `python3 -I scripts/bib_inventory.py <main.tex> <refs.bib>`: cited keys missing from the `.bib`, entries never cited, duplicate keys, and text outside entries.
- `python3 -I scripts/check_source.py <main.tex> [refs.bib]`: unbalanced braces and environments, references without labels, table rows with the wrong number of columns.

Then compile, and count pages with todos disabled (`\usepackage[disable]{todonotes}` in a build copy), because todo boxes inflate the length.

## Step 3: Checks

Run all checks by default; when the user names some, run only those. Checks A, C, D and E can run in parallel subagents. Brief each agent with file paths and its checks only; give it a scratch folder to write in (`/tmp/<run>-scratch`), state facts only after verifying them, and verify the agent's claims before reporting them.

**A. Numbers.** For every number from the inventory, find its source and compare it at the paper's precision:

`python3 -I scripts/trace_numbers.py inventory.json <primary result files> --also <experiment code, configs, logs, per-item outputs>`

Primary files are the ones that hold the reported results (for example `report.json`, `table.csv`). The script sorts each number into `in_primary`, `only_other`, `not_found` or `small_integers`. A match is a candidate, not a proof: confirm that the field means what the paper says (the first match may be an unrelated field with the same value). Numbers in `only_other` are often coincidences in large files; confirm each by hand or treat it as not found. A number with no confirmed source is a finding. Watch for numbers from earlier runs, percentage vs fraction, and counts that are off by one.

**B. Terms.** Check that each concept has one name throughout (features vs variables, schema vs ontology), that every term is defined before use, and that metric names match their definitions.

**C. Software claims vs code.** For every statement about the software (what it does, defaults, behaviour on failure, supported formats and providers, installation, tests, CI, documentation), check the code at the cited version:
- Behaviour: read the function that implements it and cite file:line.
- Files the paper names (examples, notebooks, citation files, docs pages) must exist **in the cited version**, not only on another branch.
- "Reproduces offline", "recorded responses": check that the committed fixtures produce the paper's numbers.
- Test counts, coverage and CI matrix: count from the code and config; check the latest CI run (GitHub API or `gh run list`) for claims that tests pass.

**D. Evaluation vs experiment code.** For every definition the evaluation relies on (metrics, statistical test, how runs are pooled, what `±` means, cost and its prices, baselines and their settings, data splits, class choice), find it in the experiment code and cite cell or file:line. A definition that the paper states differently from the code is a finding, even when the numbers agree.

**E. Citations.** Follow [references/paper-search.md](references/paper-search.md).
- Metadata: authors, title, venue, year and published version, checked against Crossref, DataCite, the publisher, PMLR or the proceedings page, and arXiv. DBLP may be blocked. A DataCite year can belong to a dataset deposit, not the original publication.
- Cited claims: for every cited claim with a number or a strong verb ("showed", "found"), download and read the cited paper with `paper-search` and quote the passage. A claim you cannot find in the source is a finding; do not judge it from memory.
- Datasets, baselines and software used but not cited.

**F. Evaluation integrity.** Leakage between discovery or training data and evaluation data (including steps outside the folds), aggregation (micro vs macro), label alignment, and whether the results reproduce from the saved outputs.

**G. Statistics.** For every comparison the paper makes ("better", "comparable", "significant"): which test, on what (folds, runs, items), pooled or per run, whether it fits (paired, corrected for CV), and whether multiple comparisons are handled or stated. A high p-value means "no significant difference", not "equal". A pooled result can hide a run that disagrees. If per-fold or per-run data exist, ask whether to recompute with an independent agent, following [references/independent-recompute.md](references/independent-recompute.md).

**H. Claims about model behaviour.** Statements about what a model does ("describes 78% of clips as ...", "features are nearly constant") must be checked against the raw outputs. List them, say which files and analysis would verify each, and ask which to verify.

**I. Venue.** Check every requirement from the venue reference, including requirements on the software or artifact (license headers, repository, archives), not only on the paper.

**J. Writing, length and todos.** Apply [references/writing-style.md](references/writing-style.md) to the abstract, results, discussion and conclusion; style issues in co-authors' text are suggestions only. Compare the page count (without todos) with the limit. For every todo, say whether the sources now **resolve** it, **partly resolve** it (and what is missing) or **do not address** it, and propose removing the resolved ones.

## Step 4: Blind review

Ask the user whether to run it (it takes several minutes). Then follow [references/blind-review.md](references/blind-review.md): a fresh agent without the findings so far reviews the whole paper, every finding it reports is verified with `scripts/check_quotes.py` and against the source, and only confirmed new findings are added. Offer a second reviewer on a different model for important submissions.

## Step 5: Report

Group findings by **who has to act**, and by severity within each group:
1. **Text fixes** that can be made now from the sources.
2. **Code or repository changes.**
3. **Decisions for the user or co-authors.**
4. **Information needed** that no source contains.

Severity: **HIGH** (wrong numbers or claims, missing experiment code, venue violations, open todos at submission, significance without a valid test), **MEDIUM** (definitions that differ from the code, terminology, outdated citations), **LOW** (typos, formatting). Each finding has its check letter, the paper text with file:line, the source with file:line or field, and a specific fix.

Also give: the number audit from Step 2 (matched, unmatched), the venue compliance table with the guideline URL and date, the todo status, the findings from the blind review marked as such, and what was **not checked** and why (for example not compiled, tests not run).

For "information needed", write at most **5 questions** in the chat, most critical first, merging related points, for whoever holds the information. Write a file only if the user asks.

## Step 6: Fix

Ask which fixes to draft. Draft them in a local working copy, never committed. Put `% source:` comments on their own line, never in the middle of a line. Then compile, make the marked-up PDF and run `python3 -I scripts/deleted_text.py <old.tex> <new.tex>`, following section 4 of [references/latex-setup.md](references/latex-setup.md). Every deletion must match a chosen fix. Give the user both PDFs, say which pages changed, and keep only the fixes they approve. Then ask whether to commit and push, naming the repository and branch.

## Step 7: Check again

If the report had HIGH findings and fixes were applied, ask whether to run the checks again on the new version: the checks affected by the fixes, the inventory scripts, and a new blind review. Repeat Steps 3 to 6 until no HIGH finding can be fixed from the sources, and everything left needs code changes, a decision or information from the user. Stop after three rounds and ask how to continue. End with the list of everything that is still open, grouped as in Step 5.

## Working with add-results

**add-results** puts new results into the paper and checks only what they touch. **paper-audit** checks the whole paper. Typical order: run check I (venue) first if the requirements are not known, then `/add-results`, then `/paper-audit` before submission. If paper-audit finds stale numbers and newer result files exist, suggest `/add-results` instead of patching numbers one by one.
