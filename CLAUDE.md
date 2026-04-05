This is personal blog site.

Refer to README.md for information on how to use this repository.

Refer to posts/ and project/ *.qmd files for my blog posts and especially for my writing style.

In general I admire and want to follow Paul Graham's writing style in his essays and Tim Urban's style in his blog Wait But Why.

See `ARCHITECTURE.md` for CI/publish architecture and gotchas.

## Analytics

Metrics pipeline lives in `analytics/`. Run `make analytics` to fetch and display the dashboard locally. See `~/.claude/skills/metric-extractor/SKILL.md` for full pipeline docs.

Two metrics tracked:
- **GA4 total visitors** (`analytics/configs/ga4_total_users.json`) — requires service account key at `analytics/credentials/ga4-service-account.json` and correct property ID in the config URL
- **Giscus total reactions** (`analytics/scripts/fetch-giscus-reactions.py`) — requires `GITHUB_TOKEN` env var

## Conventions

- **Never use spaces in static asset filenames** (images, GIFs, PDFs in `*/static/`). Use hyphens. Spaces cause W3C RSS validation errors — Quarto URL-encodes them (`%20`) in qmd references, which the validator rejects as invalid URI characters.
