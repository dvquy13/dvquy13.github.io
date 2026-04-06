# UTM Tracking Convention

> Consistent UTM parameters for attributing traffic in GA4 across all distribution channels.

## Parameter Rules

- **`utm_source`** — lowercase platform identifier, no spaces (e.g. `devto`, `hackernews`)
- **`utm_medium`** — `crosspost` for syndication platforms; `social` for promotion-only; `email` for newsletter
- **`utm_campaign`** — post slug (hyphen-separated, matches the URL path, e.g. `deploy-ml-gcp`)

## Channel Reference

| Channel       | `utm_source` | `utm_medium` | `utm_campaign` |
|---------------|--------------|--------------|----------------|
| Dev.to        | `devto`      | `crosspost`  | post slug      |
| Hashnode      | `hashnode`   | `crosspost`  | post slug      |
| Reddit        | `reddit`     | `social`     | post slug      |
| Twitter / X   | `twitter`    | `social`     | post slug      |
| LinkedIn      | `linkedin`   | `social`     | post slug      |
| Newsletter    | `newsletter` | `email`      | post slug      |
| Hacker News   | `hackernews` | `social`     | post slug      |

## Example

Post: `dvquys.com/posts/deploy-ml-gcp/`

```
Dev.to footer link:
https://dvquys.com/posts/deploy-ml-gcp/?utm_source=devto&utm_medium=crosspost&utm_campaign=deploy-ml-gcp

Newsletter CTA:
https://dvquys.com/posts/deploy-ml-gcp/?utm_source=newsletter&utm_medium=email&utm_campaign=deploy-ml-gcp

Reddit share:
https://dvquys.com/posts/deploy-ml-gcp/?utm_source=reddit&utm_medium=social&utm_campaign=deploy-ml-gcp
```

## `utm_medium` Rationale

`crosspost` (not `social`) for Dev.to and Hashnode because the full article is syndicated there — GA4 traffic from those platforms represents readers who clicked through from the canonical link at the bottom, not from a standalone promotional post. This distinction lets you filter `utm_medium=crosspost` in GA4 to see pure syndication traffic separately from social promotion.

## GA4 Setup

**Traffic Acquisition report filter:**
- Dimension: `Session manual medium`
- Condition: `exactly matches` → `crosspost`

Save this as a report in GA4 Explorations for quick access.

**Verify a new UTM link:** paste it in GA4 → Realtime → check "Event: session_start" with the expected parameters before publishing.
