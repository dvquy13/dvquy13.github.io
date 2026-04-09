---
paths:
  - custom.scss
---

# custom.scss Rules

## CSS Cascade — Always Use `!important` for Quarto/Bootstrap Overrides

`custom.scss` is compiled into the site CSS **before** Bootstrap and Quarto's generated stylesheets. Any rule targeting Quarto-generated elements (navbar, listing, search, etc.) will be overridden unless marked `!important`.

**Always use `!important` when overriding:**
- Quarto layout elements (`.navbar-container`, `#quarto-search`, `#navbarCollapse`, etc.)
- Bootstrap utilities (`ms-auto`, `mx-auto`, `flex-grow`, `order`, etc.)
- Any property that doesn't take effect after a first attempt — check computed styles first, then add `!important`.

## Flex Layout — Audit Before Reordering

Before changing `order` on any navbar/flex child, inspect the parent's full flex context:
```js
getComputedStyle(parent).justifyContent  // often space-between — kills order changes visually
getComputedStyle(child).flexGrow         // flex-grow: 1 on a sibling absorbs all remaining space
```
Changing `order` alone is not enough if the parent uses `justify-content: space-between` or a sibling has `flex-grow: 1`. Fix those too.

## Quarto `compact` Class Behavior

Quarto adds `class="nav-item compact"` to navbar items **only when they have an icon and no text**. Adding `text:` to a social icon item in `_quarto.yml` silently removes the `compact` class.

**Consequence:** CSS selectors like `.nav-item.compact` will match nothing after text is added.
**Correct selector for icon nav items:** `.nav-item:has(i)` — this targets by icon presence regardless of `compact`.

Use `:has(i)` for any styling that should apply to icon-based nav items.

## Mobile Navbar — Alignment Formula

On mobile (390px viewport):
- `nav.navbar` has `padding-left: 1rem` (Bootstrap default = 15.33px at root font-size)
- `body-content-start` is at `1.5rem` from viewport left
- Therefore `.navbar-container` needs `padding-left: 0.5rem` to land the first item at `body-content-start`

## Navbar Brand Alignment — SCSS Variable Coupling

The navbar brand is aligned to `body-content-start` via a padding formula driven by `$body-width` in `custom.scss`:

```scss
$body-width: 600px;  // keep in sync with grid.body-width in _quarto.yml
$navbar-brand-padding: 119.5px + (500.5px - $body-width) / 2;
```

**If `grid.body-width` changes in `_quarto.yml`, update `$body-width` in `custom.scss` too.** The formula recalculates automatically; only the variable needs updating.

**Derivation:** brand padding = `3em + 70px + (885px - 6em - 285px - body-width) / 2`, which simplifies to `119.5px + (500.5px - body-width) / 2` at 16.5px font-size.

## CSS Grid fr Units — Cannot Mirror page-columns in Navbar

A CSS Grid `5fr` column resolves to a different pixel value in different containers because fr is computed from **all remaining space after fixed AND auto-sized columns**. Applying the same `grid-template-columns` structure to the navbar as `.page-columns` does NOT produce the same `body-content-start` pixel position, because the navbar's auto columns (brand + nav items) have a different combined width than the page body column (600px).

**Do not attempt to align the navbar by replicating the page-columns grid.** Use the `$body-width` SCSS variable approach instead.

## Known Quarto-Generated CSS Conflicts on Navbar Elements

Before overriding navbar element properties, check for these Quarto/Bootstrap rules that are hard to discover:

- `nav.navbar { padding-left: 1rem; padding-right: 1rem }` — Bootstrap applies horizontal padding to the nav element itself. If making the navbar container full-width, zero this out too.
- `.navbar-brand-container { max-width: calc(100% - 115px) }` — Quarto limits brand width. In a CSS Grid `auto` column, `100%` resolves near-zero, collapsing the brand to ~5px. Override with `max-width: none !important` if using grid layout.

## Verify in Browser

After any CSS change, confirm the effect via computed styles or screenshot before marking the task done. A rule compiling without error does not mean it rendered correctly.

Use `getBoundingClientRect().left` to numerically verify alignment between navbar brand and page content:
```js
const brandLeft = document.querySelector('.navbar-brand-container').getBoundingClientRect().left;
const contentLeft = document.querySelector('.quarto-post .listing-title').getBoundingClientRect().left;
console.log(Math.abs(brandLeft - contentLeft)); // should be < 2px
```
