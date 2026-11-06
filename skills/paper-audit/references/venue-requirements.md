# Venue Requirements

Used by paper-audit (Step 1 and check I) and by add-results (Steps 1 and 6).

## 1. Detect the venue

Look for evidence, in this order, and record each piece you find (readme files in the paper folder often link to the guidelines):
- The document class and style files (`jmlr2e.sty`, `neurips_2026.sty`, `IEEEtran.cls`, `llncs.cls`, `acmart.cls`, `elsarticle.cls`) and their options (`review`, `anonymous`, `final`).
- Venue macros and comments in the main file (`\jmlrheading`, `\editor`, `% submitted to ...`).
- Cover letters, README files and submission notes in the paper folder.
- The paper's own text ("software paper", "track", "workshop").

A style file often covers a whole family of venues (for example `jmlr2e` is used by JMLR, the MLOSS track and TMLR-like venues). **Tell the user which venue and track you detected, with the evidence, and ask them to confirm.** Ask directly when the evidence is weak.

## 2. Fetch the requirements

Fetch the official author guidelines for the confirmed venue and track (web search for the venue's call for papers or author instructions, then fetch the page). Index pages often only link to the rules: follow the links until you reach the page that states them (for example a track index, then its submission page, then the general formatting page). Use only the venue's own pages, not blogs or templates from third parties. Record every URL and the date fetched.

Extract:
- **Length.** Page or word limit, what counts (references, appendix, supplementary), and the limit for the camera-ready version if different.
- **Format.** Required template, font size, margins, columns, line numbers, and whether the template may be modified.
- **Anonymity.** Double-blind or not, rules for self-citation, links to repositories and acknowledgements.
- **Required content.** Sections or statements the venue requires (for example license, repository URL, comparison with existing software, checklists, ethics or LLM-use statements, data and code availability).
- **References.** Citation style and any rules on preprints.
- **Supplementary material.** What may go there and how it is submitted.
- **Requirements on the software or artifact**, for venues that review code (for example a license notice in every source file, a public repository, no version-control files in the archive, test coverage). These are checked against the code, not the paper.

If the guidelines cannot be fetched, say so and ask the user for the link or the text. Never fill in requirements from memory.

Ask the user whether to save the extracted requirements to a file in the paper folder (suggest `venue-requirements.md`) so later runs can reuse them, with the URL and date.

## 3. Check the paper

For each requirement, give a status: **meets**, **violates** (with the evidence), or **cannot check** (with what is needed).

**Length.** Count pages from the compiled PDF, not from the source, built with todo notes disabled (`\usepackage[disable]{todonotes}` in a build copy), because todo boxes inflate the length. On macOS, `mdls -name kMDItemNumberOfPages paper.pdf`; elsewhere `pdfinfo paper.pdf`. Apply the venue's rule about what counts. If there is no PDF, see [latex-setup.md](latex-setup.md), or ask the user for the PDF downloaded from Overleaf. Without a PDF, estimate from the word count and say it is an estimate.

**Format.** Check that the required class and style are used unmodified: no changes to `\textheight`, `\textwidth`, margins or font size, no `\vspace` with negative values to squeeze space, no `\small` applied to the body text.

**Anonymity.** For double-blind venues, search for author names, affiliations, grant numbers, acknowledgements, non-anonymous repository URLs and "our previous work [X]" phrasing.

**Required content.** Check that each required section or statement exists.
