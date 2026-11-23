# FRAME Composition Architecture v4 — isolated research build

**STATUS: Engineering improvements tested, Chief Art Director NO-GO; do not merge to live FRAME.**

This project improves the separate composition architecture, not the live interface, background-removal model, or customer-upload workflow. Original packshot image bytes are never modified. All visual outputs are 2000×2000 transparent RGBA PNGs and must remain subject to human creative approval.

## Fixed in code

- `src/evidence.mjs` — corrected Nykaa L'Oréal 1036-pixel source to **page 6**, preserved exact COSRX 1340 / Dot & Key 781 values, added Nykaa opened-with-cap lipstick at 741 px (page 3), introduced strict trusted online dimension contract (same SKU, same pose, `dimensionType=product`, explicit HTTPS source). Unknowns cannot be relabelled as exact or compared with reference pixels without an identical-SKU calibration bridge.
- `scripts_pdf_index.py` — extracts the actual PDF's 19-page height values into an audit index; cannot infer every SKU from chart screenshots without visual verification.
- `scripts_extract_labels.py` — Tesseract OCR on a temporary neutral composite, returns individual normalized text regions and confidence plus **tight original alpha crop**. Source RGB unchanged. Needs backend dependencies and manual confirmation on low-confidence packs.
- `src/planner.mjs` — role-aware 3–4 product planner, 48×48 silhouette scoring, text-occlusion rejection, ground plane, controlled search, three separate directions, invalid-candidate flag, strict dimensional ratio preservation, source-crop forwarding, and optional reference-guide support.
- `src/reference.mjs` — accepts manually/externally annotated approved-reference role anchors, not a claim of automatic reference-image interpretation.
- `src/renderer.mjs` — actual alpha-derived product-overlap shadows plus soft contact/ambient shadows behind unchanged original product imagery; editable default #2C003B ground and #000000 overlap.

## Tests

```
node test/core.test.mjs
node test/v4_public.test.mjs
```

Private QA runs additionally used four provided source packshots and OCR regions. They are not included in this source distribution nor uploaded to the public repository.

## API summary

```
const plan=planCompositions(products,{seed:17,trials:75,referenceGuide:null});
const chosen=plan.options.find(x=>x.qa.hardFailures===0);
// chosen must also pass creative review and scale verification before final export.
renderTransparentComposition(canvas,{canvas:plan.canvas,layers:chosen.layers},sourceMap,shadowOptions);
```

`referenceGuide` is optional, but requires `{source:'approved_reference',id,anchors:{hero:{x,foot},wide:{x,foot},accent:{x,foot},secondary:{x,foot}}}`. Coordinates are normalized 0..1.

## Explicit outstanding blockers

1. Browser-only GitHub Pages cannot securely run Tesseract or do unrestricted Google/brand research. These require a hosted backend; `onlineLookup` remains a strict contract, **not a live connector**.
2. Automated OCR boxes are not validated full label polygons or a guaranteed exact SKU identity. Their confidence and visual QA matter.
3. Even geometrically sound layouts remain too similar to frontal packshot arrangements. A higher-level reference understanding / artist evaluation layer is required before Photoshop-level claims.
4. Estimating unknown product sizes from source photograph pixels is **not physical dimension verification**; production ratio compliance remains blocked until corroborated.
5. No live production merge or release made in this research build.