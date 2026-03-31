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
1. `quarto render` — renders all `.qmd` files to `docs/` (output-dir)
2. `peaceiris/actions-gh-pages@v4` — pushes `docs/` contents to root of `gh-pages` branch

`docs/` is gitignored on `main`. Never commit it.

## Gotchas

### `quarto publish` is incompatible with `output-dir: docs`

**Do not use `quarto publish gh-pages` in CI.** Quarto's publish render step expects intermediate HTML to land at the source file's directory (e.g. `posts/foo/index.html`), then moves it to `output-dir`. With `output-dir: docs`, rendered HTML goes directly to `docs/` — the intermediate path never exists, causing a fatal rename error.

The correct approach for this repo is always: `quarto render` → deploy `docs/` separately.

### Bootstrap hash accumulation (historical)

Before the CI migration, `docs/` was committed to `main`. Every `custom.scss` change regenerated a new hash-named bootstrap CSS file (`bootstrap-<hash>.min.css`). Old files accumulated as untracked git artifacts because Quarto doesn't clean orphaned assets. This is fully resolved — `docs/` is no longer tracked.

### Quarto version

Pinned to `1.6.40` in CI (`.github/workflows/publish.yml`) to match local. Upgrade both together.
