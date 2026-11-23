# FRAME Composition Architecture v3 — QC record

Date: 23 November 2026. Status: engineering architecture proof, **NO-GO** for production.

## Actual evidence

- Browser: Chromium, local self-contained module test using in-memory data URLs (no network/CDN). No runtime JavaScript exceptions.
- Assets: four prior user-provided transparent skincare images — COSRX Snail 96, Dot & Key Strawberry Serum, Face Shop Rice Water Bright, Biodance mask set — used locally. Original files were not uploaded to GitHub.
- Exact source chart comparisons in this QA: COSRX 1340 px and Dot & Key 781 px (relative to Forever52 reference 1200 px). Other assets retain **estimated** scale flags; do not mistake visual proxies for verified package dimensions.
- Unit tests: exact SKU matching / nonmatching, unknown fallback, mock online adapter, prohibiting uncalibrated physical mm : PDF pixel mixing, exact known ratios, unique layers, three named directions, and deliberate label obscuration rejection — PASSED.
- Pixel output: 3 real RGBA PNGs at 2000 × 2000; transparent (0,0) corner. Shadows enabled/disabled comparison changed 423,599 pixels, including 134,523 pixels with alpha >15 outside shadowless object regions — evidence that shadows are actually rendered.
- Geometry/label acceptance: Sculpted Depth **0** hard failures; Editorial Diagonal **0**; Asymmetric Balance **2** hard failures (rejected). The first two nevertheless **FAIL human creative QC** for still looking like a conventional packshot arrangement.
- Automated OCR/local label detection: **NOT IMPLEMENTED**. QA used manually specified rectangles. Commercial automatic label protection cannot be claimed.
- Live PDF extraction and Google/brand-product dimension lookup: **NOT IMPLEMENTED HERE**. `onlineLookup` is a tested server-adapter contract only.
- Original product cutout quality: **OUT OF SCOPE / not re-evaluated** in this isolated architecture proof.

## CEO/CTO/Chief Art Director signoff

- CTO: **Conditional pass** for isolated scene and shadow architecture, output/ratio checks and unit tests; unverified SKU-attribute and online resolver remain open integration risks.
- Chief Creative Director: **FAIL** — still insufficient creative differentiation, layer tension and editorial depth; one option has hard alignment/label violations.
- CEO: **NO RELEASE**; retain existing FRAME live UI and all features unchanged. Research branch only.

## What must be proved before integration

1. Automatic SKU/pose identification and PDF ingestion with verifiable exact matches, plus trusted physical dimension lookup when chart missing.
2. Semantic label detection beyond a rough center rectangle; redline exact safe regions and protect logos / claims.
3. Intentional reference-guided art-direction planning rather than variations of the same scene template.
4. Stronger realistic depth cues via shadow calibration, layering and physical support, with no fake source/package edits.
5. Independent CAD approval of full-resolution PNG exports from both makeup and skincare test sets.

## Release control

`main` and the current public `/lab/` are intentionally unchanged. This research implementation is allowed to fail its quality gate and must not be called Photoshop-quality.