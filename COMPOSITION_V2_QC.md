# FRAME — Composition Planner v2 research branch

**Date:** 23 November 2026  
**Product status:** **RESEARCH / NO-GO** for production or root GitHub Pages.

## Scope implemented

- Replaced three jittered arrangement templates with three deliberately different structured composition directions: **Hero Cascade**, **Diagonal Depth**, and **Editorial Offset**.
- Candidates preserve one **common scale multiplier** across every source image. No SKU height is independently increased to fill space.
- Uses alpha silhouettes plus a **heuristic local-contrast content-protection map**. Important caveat: this is *not* OCR, verified logo detection, or professional visual understanding; an image with unusual label placement may still have occlusion.
- Prevents category fallback from incorrectly making a serum a wide backing item when a set contains only upright products.
- Supports alternative serum/concealer focal placement in the diagonal direction, when appropriate.
- Replaces generic tiny ground gradients with alpha-footprint-aware, independently adjustable ground/contact shadows. No podium or background added to exports.
- Preserves existing cutout editor, mask approval, guideline PDF inspection, size evidence UI, precision layers/Undo, save/reopen, and PNG exporting.

## Actual regression evidence

**Browser:** headless Chromium, 23 Nov 2026. **Assets:** four previously supplied transparent skincare packshots; also a three-product subset. Tests are repeatable using an internal Playwright script and do not depend on generating new product pixels.

| Verification | Observed |
|---|---|
| Four original assets upload/approve | PASS (transparent inputs only; AI cutout not tested) |
| Three distinct structural style directions | PASS algorithmically; aesthetic quality still FAIL |
| Four unique product IDs per 4-SKU layout | PASS |
| Three unique product IDs per 3-SKU layout | PASS |
| COSRX 1340 : Dot & Key 781 reference ratio | PASS, numerical error <1e-9 |
| Regenerate selected layout changes placement | PASS |
| Original source pixel samples after layer edit | PASS (sample hashes only) |
| 2000 × 2000 RGBA PNG, transparent corners | PASS (all six outputs) |
| JavaScript runtime errors during this regression | 0 |
| Accurate auto-identification of generic packshots | **NOT VERIFIED**; the test files were only estimated/unknown |
| Current AI background removal, difficult edges | **NOT VERIFIED** |
| Brand PDF visual compliance | **NOT VERIFIED** |
| Photoshop-quality art direction | **FAIL** |

## Independent production verdicts

- **CTO: CONDITIONAL PASS** for structure, source pixel preservation, arithmetic, render and browser behavior. A static geometric engine cannot yet understand arbitrary brand labels, reference layouts, viewpoint or photography quality.
- **Chief Creative Director: FAIL.** While the samples improved grouping and hierarchy relative to a flat row, all three can still resemble a studio packshot lineup rather than a confidently art-directed Nykaa grouping. In some candidates too much of the rear multi-element mask-set artwork is covered. Do not market these as commercial art.
- **CEO: NO-GO.** Do not replace the main site, do not merge this branch, do not present another public release as fixed.

## Engineering gates for future iteration

1. Detect **actual printed label/logo regions** from products, not only contrast heuristics. Preserve them in overlap planning.
2. Add reference-driven semantic composition analysis: product roles, camera pose, multi-element SKU components, illumination and spatial style.
3. Search and rank a diverse candidate pool with calibrated negative-space/depth/contact-shadow/brand-hierarchy scores, then art-review **actual 2000px exports**, not canvas bounding boxes.
4. Test with the original makeup four-pack, transparent skincare, difficult white/black packshots; quantify human art-direction acceptance. Existing source masks are a separate quality gate.
5. When physical heights are unknown, keep proportions explicitly **estimated or unknown**; a PDF category proxy is not a verified package dimension.

**Source preservation:** This branch contains application code only. No customer image files or private guideline PDFs are committed. No live root Pages deployment is changed.