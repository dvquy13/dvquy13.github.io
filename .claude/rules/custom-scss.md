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

## Verify in Browser

After any CSS change, confirm the effect via computed styles or screenshot before marking the task done. A rule compiling without error does not mean it rendered correctly.
