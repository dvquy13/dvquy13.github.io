This is personal blog site.

Refer to README.md for information on how to use this repository.

Refer to posts/ and project/ *.qmd files for my blog posts and especially for my writing style.

In general I admire and want to follow Paul Graham's writing style in his essays and Tim Urban's style in his blog Wait But Why.

See `ARCHITECTURE.md` for CI/publish architecture and gotchas.

## Analytics

Metrics pipeline lives in `analytics/`. Run `make analytics` to fetch and display the dashboard locally. See `~/.claude/skills/metric-extractor/SKILL.md` for full pipeline docs.

**All analytics scripts must be run from the `analytics/` directory** (the Makefile does `cd analytics` before invoking them). Credential paths in configs are relative to `analytics/`, not the project root.

Two metrics tracked:
- **GA4 30d visitors** (`analytics/configs/ga4_total_users.json`) — service account key at `analytics/credentials/ga4-service-account.json`; property ID `464728949`
- **Giscus total reactions** (`analytics/scripts/fetch-giscus-reactions.py`) — falls back to `gh auth token` if `GITHUB_TOKEN` not set

Dashboard at `dvquys.com/dashboard` (→ `dashboard.dvquys.com` via Cloudflare redirect). Rebuilt daily by `fetch-metrics.yml` CI workflow at 08:00 GMT+7.

**Quarto resources gotcha**: static files must be listed under `project.resources` in `_quarto.yml` (not top-level `resource:`). Top-level `resource:` is silently ignored.

## Conventions

- **Never use spaces in static asset filenames** (images, GIFs, PDFs in `*/static/`). Use hyphens. Spaces cause W3C RSS validation errors — Quarto URL-encodes them (`%20`) in qmd references, which the validator rejects as invalid URI characters.
