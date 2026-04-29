This is personal blog site.

Refer to README.md for information on how to use this repository.

Refer to posts/ and project/ *.qmd files for my blog posts and especially for my writing style.

In general I admire and want to follow Paul Graham's writing style in his essays and Tim Urban's style in his blog Wait But Why.

## Deploy / Release

**Deploy = `git push origin main`.** The `publish.yml` CI workflow triggers on every push to `main`: it renders the Quarto site and deploys `docs/` to the `gh-pages` branch, which serves `dvquys.com`. There is no separate release step or `make release` target.

Local preview: `make run` (Quarto dev server on port 8183).
Local build + RSS validation: `make build`.

## Writing Principles

These apply to any writing task in this repo.

**Write Simply** — Prose should be frictionless. The goal is *saltintesta*: ideas leap into the reader's head; they barely notice the words. Simple writing keeps you honest — if you have nothing to say, saying it simply makes that obvious. Cut fancy words, unnecessary complexity, and anything clumsy. If a sentence seems too complicated, it is.

**Write Like You Talk** — Every sentence should pass the friend test: "Is this the way I'd say this to a friend?" If not, say it out loud — and use that instead. Informal language is the athletic clothing of ideas. The harder the subject, the more important it is to keep the language simple. The root failure mode of AI-generated prose is that it *performs* ideas—dramatic fragments, theatrical pauses, restatements for emphasis—instead of talking through them. DvQ talks through ideas. Each sentence assumes the previous one and sets up the next, the way a story actually comes out of your mouth.

**Write Like DvQ** — Conversational first-person. Specific and grounded in lived experience. Honest about failures — what didn't work always comes before what did. No hedges, no filler transitions, no advice from a distance.

### Anti-patterns (flag and reject these)

- **Short punchy fragments for dramatic effect** — `It worked.` / `Not archived. Deleted from disk.` / `So I built one.` These read as AI slop. Integrate them into the surrounding sentence.
- **Declarative thesis opener with a state-then-undercut beat** — `Every Claude Code session starts fresh. That's mostly fine at first.` Stating the problem in oracle-like sentences and immediately qualifying them is AI's default opening move. Open by talking through the problem instead.
- **Invented facts or names** — Never fabricate product names, project names, file paths, or statistics. If uncertain, omit or ask.
- **Redundant restatement** — Don't repeat what context already established. If the intro already introduces qrec, don't write "That's when I started building qrec."
- **Insider-y specifics that serve the author, not the reader** — Dropping a session count from one project to sound credible rather than to make a point the reader cares about.

### Positive patterns (do these)

- **Footnotes for asides** — Self-corrections and tangential facts go in `^[...]` footnotes, not inline. Keeps the main thread moving.
- **Flowing sentences** — Each sentence assumes the previous one and sets up the next. Prose reads as continuous thought, not a list of observations.

See `notes/ARCHITECTURE.md` for CI/publish architecture and gotchas. See `notes/UTM_CONVENTION.md` for UTM tagging convention.

### Writing Conventions

Do not use emdash everywhere, and when you do, use emdash without any space before and after it.

## Analytics

Metrics pipeline lives in `analytics/`. See `~/.claude/skills/metric-extractor/SKILL.md` for full pipeline docs.

**All analytics scripts must be run from the `analytics/` directory** (the Makefile does `cd analytics` before invoking them). Credential paths in configs are relative to `analytics/`, not the project root.

**GCP project for dvquys analytics:** `centered-flow-429008-d3` (service account: `dvquys-analytics@centered-flow-429008-d3.iam.gserviceaccount.com`). Used for GA4 service account auth and GSC `oauth_adc` quota project. Do not confuse with `calens-chrome-ext` (a different app).

Metrics tracked:
- **GA4 30d visitors** — `fetch-metrics.py` + `analytics/configs/ga4_total_users.json`; service account at `analytics/credentials/ga4-service-account.json`; property ID `464728949`
- **GSC search impressions (28d)** — `fetch-metrics.py` + `analytics/configs/gsc_impressions_28d.json`; `oauth_adc`, quota project `centered-flow-429008-d3`
- **GSC search clicks (28d)** — `fetch-metrics.py` + `analytics/configs/gsc_clicks_28d.json`; same auth
- **Giscus reactions** — `fetch-giscus-reactions.py`; falls back to `gh auth token` if `GITHUB_TOKEN` not set
- **Giscus comments** — `fetch-giscus-comments.py`
- **Posts published (28d)** — `fetch-posts-published.py`
- **GA4 top 5 sources** — `fetch-ga4-top-sources.py`
- **Newsletter subscribers** — `fetch-newsletter-subscribers.py`; queries `newsletter_subscribers` table via Supabase REST API

History stored in Supabase (`metrics_snapshots` table, project `dvquys-metrics`, ref `olssvguaeagsmkfmsvvo`). Dashboard fetches directly from Supabase REST API using the anon key embedded in `dashboard.html`. CI requires secrets `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`.

Supabase has migrated to new-style API keys (`sb_publishable_...` / `sb_secret_...`). Scripts prefer `SUPABASE_SECRET_KEY` with fallback to `SUPABASE_SERVICE_ROLE_KEY`. Edge Functions still receive the old key auto-injected by Supabase's runtime — no change needed there.

Dashboard at `dvquys.com/dashboard` (→ `dashboard.dvquys.com` via Cloudflare redirect). Updated daily by `fetch-metrics.yml` CI at 03:13 GMT+7 (20:13 UTC prev day) — early so GitHub Actions queue delays still land before wake-up.

**Stamp architecture:** `dashboard.html` in `main` is a pure template (placeholder `<noscript>` block). CI stamps only `gh-pages/dashboard.html` (the deploy artifact) via worktree — never commits to `main`. This keeps `main` clean and eliminates `git pull` friction. `make analytics-push` stamps your local `dashboard.html` for local inspection, but that change should not be committed to `main`.

**Local dashboard preview**: `dashboard.html` fetches from Supabase (CORS-open), so it works directly from `file://` or via `python3 -m http.server 8080`.

**alerts.yaml** lives at `analytics/alerts.yaml` (not `analytics/configs/`).

**`.env` is at the project root**, not `analytics/`. Makefile loads it via `-include .env`. When running scripts directly from `analytics/`, source it manually: `export $(grep -v '^#' ../.env | xargs)`.

**Discord daily digest field order** follows the `labels` key order in `alerts.yaml` — put the northstar metric first in `labels` to make it appear first in the embed.

**Dashboard card render order** follows `sections[].keys` order in the `dashboard.html` CONFIG block — rearrange keys there to reorder cards.

**Quarto resources gotcha**: static files must be listed under `project.resources` in `_quarto.yml` (not top-level `resource:`). Top-level `resource:` is silently ignored.

## Newsletter

Subscribers stored in Supabase (`newsletter_subscribers` table). Edge Functions at `supabase/functions/subscribe` and `supabase/functions/unsubscribe` handle signups/removals. Send script: `analytics/scripts/send-newsletter.py`. Sending domain `dvquys.com` verified in Resend; From address is `hello@dvquys.com` (mailbox doesn't need to exist — Resend only needs the domain verified).

`make newsletter-send POST=posts/my-post/index.qmd [DRYRUN=--dry-run]`

## Conventions

- **Never use spaces in static asset filenames** (images, GIFs, PDFs in `*/static/`). Use hyphens. Spaces cause W3C RSS validation errors — Quarto URL-encodes them (`%20`) in qmd references, which the validator rejects as invalid URI characters.
- **Never set `toc: false` in page frontmatter** — it adds the `fullcontent` CSS class which breaks column alignment with the rest of the site. Instead, omit `toc:` and let pages inherit `toc: true` from `_quarto.yml`; pages with no headings render without a visible TOC anyway.
