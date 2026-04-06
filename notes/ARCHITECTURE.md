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
dashboard.html      — analytics dashboard (CI-generated, committed to main)
analytics/          — metrics pipeline (scripts, configs, fixtures)
.github/workflows/  — CI workflows (publish + fetch-metrics)
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

## Analytics Pipeline

**Dashboard:** `dvquys.com/dashboard` (served via Cloudflare redirect from `dashboard.dvquys.com`).

**Data flow:**
1. `.github/workflows/fetch-metrics.yml` runs daily at 08:00 GMT+7
2. Fetches GA4 30d visitors (service account auth) + Giscus reactions (GitHub GraphQL)
3. Regenerates `dashboard.html` via `analytics/scripts/generate-dashboard-html.py`
4. Commits `dashboard.html` to `main` if changed → triggers `publish.yml` → deploys

**Infrastructure:**
- GA4 property ID: `464728949`; service account: `dvquys-analytics@centered-flow-429008-d3.iam.gserviceaccount.com` (Viewer in GA4)
- Giscus repo: `dvquy13/icy-touch-comments` (GitHub GraphQL API, falls back to `gh auth token`)
- Cloudflare: proxied CNAME `dashboard.dvquys.com` + Page Rule redirect → `dvquys.com/dashboard`
- Secret `GA4_SERVICE_ACCOUNT_JSON` stored in GitHub repo secrets

**Local:** `make analytics` (display), `make analytics-push` (push to Supabase + Telegram alerts when configured).

## Newsletter

Subscribers stored in `newsletter_subscribers` (Supabase, same project as metrics). Two Edge Functions handle the public API:

- `supabase/functions/subscribe` — upserts email (idempotent, no duplicate leak)
- `supabase/functions/unsubscribe` — deletes by `unsubscribe_token` (idempotent)

Both deployed with `--no-verify-jwt` (public endpoints, no auth needed). CORS locked to `dvquys.com`.

Send flow: `analytics/scripts/send-newsletter.py <post.qmd> [--dry-run]`
1. Parses QMD frontmatter + body → converts to HTML via `markdown` lib
2. Rewrites relative image `src` to absolute URLs (post URL base) — required for email clients
3. Fetches all subscribers from Supabase REST API (service role key)
4. Sends via Resend batch API (100/batch); `hello@dvquys.com` sender (mailbox need not exist)

**Cloudflare / User-Agent gotcha**: Resend's API sits behind Cloudflare WAF, which blocks `Python-urllib/3.x`. The script sets `User-Agent: dvquys-newsletter/1.0` to pass through.

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

### Quarto listing pages: body content renders above the listing

In a listing page (`index.qmd`), any body content in the `.qmd` file renders **above** the listing, regardless of its position in the file. To place content below the listing (e.g. a newsletter signup section), render it hidden (`display: none`), then use JS on `DOMContentLoaded` to call `document.getElementById("listing-listing").after(section)`.

### Excluding `.md` files from rendering (`.quartoignore` does not work)

`.quartoignore` has no effect on preventing `.md` files from being rendered in a Quarto website project. Files like `README.md`, `CLAUDE.md`, and `notes/ARCHITECTURE.md` will still be rendered to HTML and published.

The correct approach is to restrict the `render:` list in `_quarto.yml` to only `.qmd` files:

```yaml
project:
  render:
    - "*.qmd"
    - "**/*.qmd"
```

**Pitfall:** Using only `!`-prefixed exclusions (e.g. `- "!README.md"`) in the `render:` list breaks the build entirely — no files are rendered, `docs/index.xml` is never created, and the post-render hook fails.

### Static files in `project.resources` (not top-level `resource:`)

To include a static file (e.g. `dashboard.html`) in the rendered output, it must be listed under `project.resources` in `_quarto.yml`:

```yaml
project:
  resources:
    - dashboard.html
```

Top-level `resource:` is **silently ignored** by Quarto — the file won't be copied to `docs/`. Verify by running `quarto render` locally and checking `docs/` before pushing.

### `quarto preview` overwrites the postprocessed feed

`quarto preview` auto-rebuilds `docs/index.xml` on file changes, bypassing `make build`. Before adding the post-render hook, this would wipe the postprocess script's work, causing `make validate` to fail even after a clean `make build`. The post-render hook in `_quarto.yml` resolves this — postprocess runs after every render, including preview rebuilds.
