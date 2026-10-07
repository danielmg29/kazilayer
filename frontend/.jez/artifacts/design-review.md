# Design Review: KaziLayer component variant pages
**Date**: 2026-10-06
**URL**: http://localhost:3000/design-system/components/primitive-textarea

## Overall Impression
The component catalogue has a disciplined Swiss-technical layout, but its variant pages previously repeated one unchanged preview beneath different labels. The revised pages now expose state, tone, density, surface, availability, and progress differences in the rendered specimen itself.

## Findings

### High
- **Variant labels were disconnected from rendering** on every component detail page — the route expanded each label but passed only the base catalogue item to `ComponentPreview` → pass the active variant into the preview and apply it to native state, content, styling, and recipe presentation.

### Medium
- **Form states were visually indistinguishable** — default, focus, filled, error, over-limit, and disabled all showed the same populated field → render empty placeholders, visible focus treatment, validation feedback, limit counts, and native disabled/read-only states.
- **Non-form families lacked a shared variant vocabulary** — density, tone, surface, progress, and availability axes did not affect the specimen → add a shared variant presentation frame using semantic design tokens.
- **Boolean and date primitives used generic text controls** → render checkbox, switch, and calendar-specific specimens with distinct states.

### Low
- Long galleries remain intentionally dense; the current two-column desktop and single-column narrow layout is appropriate for comparison.

## What Looks Good
The typography hierarchy, strict grid, restrained borders, token-driven colour, and minimal motion already match the intended Swiss / Bento / Blueprint direction. The new state rail and recipe chips preserve that language.

## Top 3 Fixes
1. Connect every expanded variant to the rendered preview.
2. Render genuine semantic states for form and action primitives.
3. Apply shared tone, density, surface, progress, and availability treatments to all remaining component families.

## Evidence
- `textarea-variants-light.png`
- `button-variants-dark-mobile.png`
- `checkbox-variants-light.png`
