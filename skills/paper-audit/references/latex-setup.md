# LaTeX Setup

Used by paper-audit and add-results when the paper should be compiled.

## 1. Check for a toolchain

Run `command -v latexmk pdflatex xelatex lualatex tectonic`. Check every name in the list. Any one of them is enough to compile. Compile with `latexmk -pdf <main>.tex` (or the engine the paper needs, for example `xelatex` when it uses `fontspec`), or with `tectonic -X compile <main>.tex` if only Tectonic is available. Report errors and warnings for undefined references and citations. Count pages with `mdls -name kMDItemNumberOfPages` (macOS) or `pdfinfo`. If these return nothing, for example for files in `/tmp`, read the `/Count` of the PDF's page tree.

## 2. If there is none, say so and offer help

Tell the user that no LaTeX toolchain was found, so the paper cannot be compiled or its pages counted locally. Do not install anything without asking. Check the system first:
- OS and version: `uname -a`; on macOS `sw_vers`; on Linux `cat /etc/os-release`.
- CPU architecture (`uname -m`), free disk space (`df -h ~`), and whether a package manager is available (`brew`, `apt`, `dnf`, `pacman`, `winget`, `choco`).

Then offer the options that fit that system, with their size:
- **TinyTeX** (about 250 MB; installs missing packages on demand). Works on macOS, Linux and Windows without admin rights.
- **Tectonic** (single binary, downloads packages as needed). On macOS `brew install tectonic`.
- **Full TeX Live / MacTeX** (about 5 to 7 GB, everything included). On macOS `brew install --cask mactex-no-gui`; on Debian or Ubuntu `sudo apt install texlive-full`.
- **No install**: compile on Overleaf and give the skill the downloaded PDF.

Recommend one and wait for the user's choice.

## 3. Without compiling

If the paper is not compiled, still check the source: balanced braces and environments, every `\ref` has a `\label`, every `\cite` key exists in the `.bib` files, and every included file and figure exists. Say that the paper was not compiled.

## 4. Marked-up PDF of the changes

Before the user approves applying, committing or pushing any change to the paper, produce a PDF that shows the changes visually, and a list of all deleted text. Do this every time, also for small changes.

1. **Work in a separate build folder.** Copy the paper folder to a new temp folder without `.git`. Put the original version there as `old.tex` (for git: `git show HEAD:<main>.tex > old.tex`) and the edited version as `new.tex`.
2. **Make the diff.** `latexdiff -t UNDERLINE old.tex new.tex > changes.tex`. Recolour added text to green: replace `\color{blue}` with `\color[rgb]{0,0.55,0}` in `changes.tex`. Deleted text stays red and struck through. If `latexdiff` is missing, say so and offer to install it (`brew install latexdiff`, or `tlmgr install latexdiff`, or the system package manager); do not install without approval.
3. **Compile both** `changes.tex` and the clean edited file. Report errors, undefined references and citations, and overfull boxes caused by the changes. A compile error in the edited version is a finding, not something to work around.
4. **List all deleted text** with `python3 -I scripts/deleted_text.py old.tex new.tex` (in the paper-audit skill). It strips comments from both versions, compares them word by word, and prints every deleted or replaced run of words with its line. Check each one against the approved changes. Any deletion that was not approved is a bug in the edit and must be fixed before showing the PDF.
   latexdiff does not mark removed `\todo` boxes (or other removed commands such as figures); they simply disappear from the PDF. For such removals, the deleted-text list is the evidence, so show it to the user.
5. **Look at the pages.** Open the changed pages of `changes.pdf` and check that the changes look as intended: nothing missing, tables not broken, no text in the margin.
6. **Give the PDFs to the user.** Copy `changes.pdf` (marked) and the clean PDF to a folder the user can see (ask once where, for example Downloads), open the marked one, and say which pages contain the changes. In a wide table, the markup can push the table past the margin, so say whether the clean PDF has the same problem.

If no LaTeX toolchain can be used, say that no PDF could be made, show the word-level diff (`git diff --word-diff`) and the deleted-text list instead, and ask whether to proceed.

## 5. Editing rules that keep the source safe

- Never insert a line break followed by a `%` comment in the middle of a line. Everything after `%` on that line becomes a comment and disappears from the PDF. Put source comments on their own line after the end of the source line.
- In section titles, captions and other moving arguments, wrap commands such as `\nolinkurl`, `\url` or custom macros in `\texorpdfstring{<tex>}{<plain text>}` when hyperref is loaded.
