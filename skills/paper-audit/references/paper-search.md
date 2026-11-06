# Paper Search Setup

The citation check (check E) of paper-audit uses the `paper-search` command-line tool from https://github.com/fcakyon/paper-search-cli.

## Check

Run `paper-search --help`. If it works, skip the rest.

## Install

Ask the user before installing. Then:

```
uv tool install --python 3.12 'git+https://github.com/fcakyon/paper-search-cli'
```

If `uv` is missing, install it first (`brew install uv` on macOS, or see https://docs.astral.sh/uv/).

## Networks with their own certificates

On company networks that inspect TLS traffic, requests fail with certificate errors. Then:
- Use Python 3.12. Newer Python versions are stricter about such certificates and may reject them.
- Point `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` to a PEM file that contains the company's root certificate (ask the user where it is, or export it from the system keychain). Set them in the shell profile so they apply to every session.

## Sources

Use them in this order and record which one confirmed each entry:
1. **Crossref** (`paper-search tool get_crossref_paper_by_doi <doi>`) for journal and conference papers with a Crossref DOI.
2. **DataCite** (`https://api.datacite.org/dois/<doi>`) for datasets, software and reports with a DataCite DOI (Zenodo, CaltechDATA, arXiv DOIs). A DataCite record can be a later deposit: its year may differ from the original publication, so cite the original (for example the technical report) and do not copy a mismatched DOI.
3. **The publisher's or proceedings page** (PMLR, NeurIPS, ACL Anthology, OpenReview) for conference versions and page numbers.
4. **arXiv** for preprints, and its comment field for "published at".
5. **The software's official repository** for citation files (`CITATION.cff`, README citation).

Semantic Scholar may be rate-limited, and DBLP may be blocked completely (a bot challenge on dblp.org). Do not rely on either.

## Checking cited claims

For every cited claim with a number or a strong verb ("showed", "found", "most"), download and read the cited paper (`paper-search download <source> <id>`, then `paper-search read <source> <id>`) and quote the passage that supports or contradicts the claim. Never judge a cited claim from memory. If the paper cannot be obtained, say so and mark the claim as not verified.
