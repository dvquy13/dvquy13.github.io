# Architecture

> Personal blog built with Quarto, deployed to GitHub Pages via CI.

## Structure

```
_quarto.yml         — site config (theme, fonts, grid, output-dir)
custom.scss         — all custom CSS overrides (Bootstrap/Quarto)
styles.css          — minimal extra styles
posts/              — blog posts (*.qmd)
projects/           — project write-ups (*.qmd)
_freeze/            — pre-computed notebook outputs (committed)
.github/workflows/  — CI publish workflow
```

## Publish Architecture

**Source branch:** `main` (`.qmd` source files, `custom.scss`, config)
**Published branch:** `gh-pages` (rendered HTML, managed entirely by CI)
**GitHub Pages setting:** `gh-pages` branch, root `/`

### CI Workflow (`.github/workflows/publish.yml`)

On every push to `main`:
1. `scripts/check-quarto-version.sh` — asserts local and CI Quarto versions match (pinned to `1.6.40`)
2. `quarto render` — renders all `.qmd` files to `docs/` (output-dir); triggers post-render hook automatically
3. `scripts/validate-rss.sh` — POSTs `docs/index.xml` to W3C Feed Validation API; fails build on errors or blocking warnings
4. `peaceiris/actions-gh-pages@v4` — pushes `docs/` contents to root of `gh-pages` branch

`docs/` is gitignored on `main`. Never commit it.

### RSS Post-Processing

`scripts/postprocess-feed.sh` is registered as a Quarto **post-render hook** in `_quarto.yml`:

```yaml
project:
  post-render: scripts/postprocess-feed.sh
```

This strips `color: null` and `background-color: null` from `docs/index.xml` after every render — including `quarto preview` auto-rebuilds. See the Gotchas section for why this exists.

### RSS Validation

`scripts/validate-rss.sh` validates `docs/index.xml` against the W3C Feed Validation Service API (`POST rawdata`). Run locally with `make validate`.

**Blocking** (fail the build): URI errors (spaces in filenames), `DangerousStyleAttr` (style=null).
**Allowed** (intentional): `ContainsRelRef` (relative img URLs in descriptions), `SecurityRisk` (YouTube iframes), `SelfDoesntMatchLocation` (expected when POSTing local feed — atom:link points to live URL).

## Gotchas

### `quarto publish` is incompatible with `output-dir: docs`

**Do not use `quarto publish gh-pages` in CI.** Quarto's publish render step expects intermediate HTML to land at the source file's directory (e.g. `posts/foo/index.html`), then moves it to `output-dir`. With `output-dir: docs`, rendered HTML goes directly to `docs/` — the intermediate path never exists, causing a fatal rename error.

The correct approach for this repo is always: `quarto render` → deploy `docs/` separately.

### Bootstrap hash accumulation (historical)

Before the CI migration, `docs/` was committed to `main`. Every `custom.scss` change regenerated a new hash-named bootstrap CSS file (`bootstrap-<hash>.min.css`). Old files accumulated as untracked git artifacts because Quarto doesn't clean orphaned assets. This is fully resolved — `docs/` is no longer tracked.

### Quarto version

Pinned to `1.6.40` in CI (`.github/workflows/publish.yml`) to match local. `scripts/check-quarto-version.sh` enforces this at build time. Upgrade both together.

### `color: null` / `background-color: null` in RSS feed

Quarto's `github` highlight theme emits `color: null;` and `background-color: null;` as literal CSS in the RSS feed's inline-styled code blocks. This is a Quarto bug in `src/core/pandoc/css.ts` (no null guard before string interpolation) — unfixed as of v1.9.36 (March 2026), present since at least v1.1 (2022).

**Why it only affects RSS:** HTML pages use CSS classes for syntax highlighting (external stylesheet), but RSS `<description>` content uses inline styles — which is where the null values surface.

**Why postprocess instead of a custom theme:** A custom theme file (copying `github-light.theme` with nulls replaced) would need to be maintained across Quarto upgrades, offers no visual benefit (null only affects RSS, not the rendered site), and couples us to Pandoc's theme format. The postprocess script is targeted and upgrade-proof.

**Why not upgrade Quarto:** The bug is not fixed in any version. Upgrading would not help.

### `quarto preview` overwrites the postprocessed feed

`quarto preview` auto-rebuilds `docs/index.xml` on file changes, bypassing `make build`. Before adding the post-render hook, this would wipe the postprocess script's work, causing `make validate` to fail even after a clean `make build`. The post-render hook in `_quarto.yml` resolves this — postprocess runs after every render, including preview rebuilds.
