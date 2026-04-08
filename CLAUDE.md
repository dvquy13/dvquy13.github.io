This is personal blog site.

Refer to README.md for information on how to use this repository.

Refer to posts/ and project/ *.qmd files for my blog posts and especially for my writing style.

In general I admire and want to follow Paul Graham's writing style in his essays and Tim Urban's style in his blog Wait But Why.

## Writing Principles

These apply to any writing task in this repo.

**Write Simply** — Prose should be frictionless. The goal is *saltintesta*: ideas leap into the reader's head; they barely notice the words. Simple writing keeps you honest — if you have nothing to say, saying it simply makes that obvious. Cut fancy words, unnecessary complexity, and anything clumsy. If a sentence seems too complicated, it is.

**Write Like You Talk** — Every sentence should pass the friend test: "Is this the way I'd say this to a friend?" If not, say it out loud — and use that instead. Informal language is the athletic clothing of ideas. The harder the subject, the more important it is to keep the language simple.

**Write Like DvQ** — Conversational first-person. Specific and grounded in lived experience. Honest about failures — what didn't work always comes before what did. No hedges, no filler transitions, no advice from a distance. Read `.claude/agents/dvq.md` for the full voice profile.

See `notes/ARCHITECTURE.md` for CI/publish architecture and gotchas. See `notes/UTM_CONVENTION.md` for UTM tagging convention.

### Writing Conventions

Do not use emdash everywhere, and when you do, use emdash without any space before and after it.

## Analytics

Metrics pipeline lives in `analytics/`. See `~/.claude/skills/metric-extractor/SKILL.md` for full pipeline docs.

**All analytics scripts must be run from the `analytics/` directory** (the Makefile does `cd analytics` before invoking them). Credential paths in configs are relative to `analytics/`, not the project root.

Two metrics tracked:
- **GA4 30d visitors** (`analytics/configs/ga4_total_users.json`) — service account key at `analytics/credentials/ga4-service-account.json`; property ID `464728949`
- **Giscus total reactions** (`analytics/scripts/fetch-giscus-reactions.py`) — falls back to `gh auth token` if `GITHUB_TOKEN` not set

History stored in Supabase (`metrics_snapshots` table, project `dvquys-metrics`, ref `olssvguaeagsmkfmsvvo`). Dashboard fetches directly from Supabase REST API using the anon key embedded in `dashboard.html`. CI requires secrets `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`.

Supabase has migrated to new-style API keys (`sb_publishable_...` / `sb_secret_...`). Scripts prefer `SUPABASE_SECRET_KEY` with fallback to `SUPABASE_SERVICE_ROLE_KEY`. Edge Functions still receive the old key auto-injected by Supabase's runtime — no change needed there.

Dashboard at `dvquys.com/dashboard` (→ `dashboard.dvquys.com` via Cloudflare redirect). Updated daily by `fetch-metrics.yml` CI at 03:13 GMT+7 (20:13 UTC prev day) — early so GitHub Actions queue delays still land before wake-up.

**Local dashboard preview**: `dashboard.html` fetches from Supabase (CORS-open), so it works directly from `file://` or via `python3 -m http.server 8080`.

**alerts.yaml** lives at `analytics/alerts.yaml` (not `analytics/configs/`).

**Quarto resources gotcha**: static files must be listed under `project.resources` in `_quarto.yml` (not top-level `resource:`). Top-level `resource:` is silently ignored.

## Newsletter

Subscribers stored in Supabase (`newsletter_subscribers` table). Edge Functions at `supabase/functions/subscribe` and `supabase/functions/unsubscribe` handle signups/removals. Send script: `analytics/scripts/send-newsletter.py`. Sending domain `dvquys.com` verified in Resend; From address is `hello@dvquys.com` (mailbox doesn't need to exist — Resend only needs the domain verified).

`make newsletter-send POST=posts/my-post/index.qmd [DRYRUN=--dry-run]`

## Conventions

- **Never use spaces in static asset filenames** (images, GIFs, PDFs in `*/static/`). Use hyphens. Spaces cause W3C RSS validation errors — Quarto URL-encodes them (`%20`) in qmd references, which the validator rejects as invalid URI characters.
- **Never set `toc: false` in page frontmatter** — it adds the `fullcontent` CSS class which breaks column alignment with the rest of the site. Instead, omit `toc:` and let pages inherit `toc: true` from `_quarto.yml`; pages with no headings render without a visible TOC anyway.
