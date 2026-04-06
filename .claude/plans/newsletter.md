# Newsletter Signup & Resend Delivery

> **Status: COMPLETED 2026-04-06** — end-to-end verified (subscribe form live, email delivered with images, unsubscribe page working).

## Context
Set up a self-hosted newsletter system on dvquys.com so visitors can subscribe and receive new post announcements. No third-party list management — we own the subscribers in our Supabase database, deliver via Resend, and wire unsubscribe through a Quarto-rendered page.

**Backend choice**: Supabase (already set up — new `newsletter_subscribers` table + Edge Functions for the API endpoints). PostgreSQL rather than SQLite, but avoids introducing any new infrastructure.

**Form placement**: Both a dedicated `/subscribe` page (linkable from posts) and a compact inline section on the homepage.

---

## Architecture Overview

```
Browser form  →  POST dvquys.com/subscribe JS  →  Supabase Edge Fn (subscribe)
                                                          │
                                                   newsletter_subscribers table

Email unsubscribe link  →  dvquys.com/unsubscribe?token=...  →  JS  →  Supabase Edge Fn (unsubscribe)

send-newsletter.py  →  Supabase REST API (read subscribers)  →  Resend API (send batch)
```

---

## Phase 0 — Manual Setup (pre-code, done once by you)

1. **Create Resend account** → verify `dvquys.com` as sender domain ✅
2. **Add DNS records** Resend prescribes (SPF/DKIM/DMARC) to Cloudflare ✅
3. **Create sending address** `hello@dvquys.com` ✅
4. **Copy Resend API key** → add to `.env` as `RESEND_API_KEY` ✅
5. **Run `supabase db push`** after schema migration is in place ✅

---

## Phase 1 — Supabase Schema ✅

**New file**: `supabase/migrations/20260406000000_create_newsletter_subscribers.sql`

```sql
CREATE TABLE newsletter_subscribers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT UNIQUE NOT NULL,
  subscribed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  unsubscribe_token UUID NOT NULL DEFAULT gen_random_uuid()
);
CREATE INDEX ON newsletter_subscribers (unsubscribe_token);
-- Block all public access; Edge Functions use service role key
ALTER TABLE newsletter_subscribers ENABLE ROW LEVEL SECURITY;
```

---

## Phase 2 — Supabase Edge Functions

### `supabase/functions/subscribe/index.ts`

- Accepts `POST` with JSON body `{ "email": "..." }`
- Validates email format (basic regex)
- Upsert-safe: returns 200 if already subscribed (don't leak whether email exists)
- Inserts row into `newsletter_subscribers` using service role key
- Returns `{ "ok": true }` on success, error JSON on failure
- CORS headers for `dvquys.com`

### `supabase/functions/unsubscribe/index.ts`

- Accepts `POST` with JSON body `{ "token": "..." }`
- Looks up `unsubscribe_token` in table
- Deletes matching row
- Returns `{ "ok": true }` (idempotent — token not found is still OK)
- CORS headers for `dvquys.com`

**Deploy commands** (add to Makefile):
```
supabase functions deploy subscribe --no-verify-jwt
supabase functions deploy unsubscribe --no-verify-jwt
```

Both use `--no-verify-jwt` because they're publicly accessible endpoints.

---

## Phase 3 — Signup Form Pages

### `subscribe.qmd` (new, dedicated page)

Full-page subscribe experience. Contains:
- Brief pitch (2–3 lines, blog voice)
- Email input + Submit button
- JavaScript: `fetch()` to Supabase Edge Function URL
- Inline success/error state (no page reload)

### `index.qmd` (modify)

Add a compact newsletter section at the bottom (below listing). Use a Quarto `:::` div to inject custom HTML/CSS inline. Same JS logic as subscribe.qmd but minimal layout.

### `_quarto.yml` (modify)

Add `Newsletter` navbar link pointing to `/subscribe.html`.

---

## Phase 4 — Unsubscribe Page

### `unsubscribe.qmd` (new)

- On page load: reads `?token=` from URL
- POSTs token to Supabase Edge Function `unsubscribe`
- Shows inline result: "You've been unsubscribed" or "Link is invalid or already used"
- No Quarto navbar clutter — minimal page

---

## Phase 5 — `send-newsletter.py`

**Path**: `analytics/scripts/send-newsletter.py`

Follows existing script conventions (PEP 723 inline metadata, `uv run`, reads from env vars).

**Dependencies**: `resend` (Resend SDK or plain `urllib.request`)

**CLI**:
```
uv run send-newsletter.py <path/to/post/index.qmd> [--dry-run]
```

**Logic**:
1. Parse `.qmd` file: extract YAML frontmatter (title, description, date) + body
2. Strip YAML header, convert Markdown body to HTML (using `markdown` lib or `mistune`)
3. Fetch all subscribers from Supabase REST API:
   `GET {SUPABASE_URL}/rest/v1/newsletter_subscribers?select=email,unsubscribe_token`
   (authenticated with `SUPABASE_SERVICE_ROLE_KEY`, same pattern as `push-and-notify.py`)
4. Build per-subscriber email:
   - Subject: post title
   - HTML: rendered post content with header + unsubscribe footer
   - `List-Unsubscribe` header: `<https://dvquys.com/unsubscribe?token=...>`
5. Send via Resend batch API (`POST https://api.resend.com/emails/batch`, up to 100/request)
6. Print per-subscriber send result (success/fail count)

**Email template** (inline HTML string in script):
```
From: DvQ <newsletter@dvquys.com>
Subject: {post_title}

[Post title + date]
[description]

→ Read on dvquys.com: {post_url}

[Optional: full post HTML]

───
Unsubscribe · dvquys.com · {location}
```

**Env vars required**:
- `SUPABASE_URL` (already in `.env`)
- `SUPABASE_SERVICE_ROLE_KEY` (already in `.env` or `analytics/secrets/`)
- `RESEND_API_KEY` (new, from Phase 0)

---

## Phase 6 — Makefile Targets (modify `Makefile`)

```makefile
newsletter-deploy:   # deploy both Edge Functions
newsletter-send:     # uv run analytics/scripts/send-newsletter.py
```

---

## Files Changed / Created

| Action   | Path |
|----------|------|
| New      | `supabase/migrations/20260406000000_create_newsletter_subscribers.sql` |
| New      | `supabase/functions/subscribe/index.ts` |
| New      | `supabase/functions/unsubscribe/index.ts` |
| New      | `subscribe.qmd` |
| New      | `unsubscribe.qmd` |
| New      | `analytics/scripts/send-newsletter.py` |
| Modify   | `index.qmd` — add inline newsletter section |
| Modify   | `_quarto.yml` — add Subscribe to navbar + resources |
| Modify   | `Makefile` — add newsletter targets |
| Modify   | `.env` — add `RESEND_API_KEY` placeholder |

---

## Verification

1. **Schema**: `supabase db push` → check table exists in Supabase dashboard
2. **Edge Functions**: deploy, then `curl -X POST .../subscribe -d '{"email":"test@example.com"}'` → row appears in table
3. **Subscribe form**: `make build` → open `docs/subscribe.html` in browser → submit form → row in Supabase
4. **Unsubscribe**: take `unsubscribe_token` from DB → open `dvquys.com/unsubscribe?token=...` → row deleted
5. **send-newsletter.py**: `--dry-run` flag → prints emails that would be sent without calling Resend
6. **End-to-end**: subscribe with real email → run send-newsletter.py → receive email → click unsubscribe link → confirm removed from DB
