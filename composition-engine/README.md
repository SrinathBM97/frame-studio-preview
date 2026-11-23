# FRAME Composition Engine — isolated architecture v3

**Status: Research branch / no-go for commercial output.** This folder is independent of the existing FRAME interface. It does not replace the live GitHub Pages app.

## Implementation

- `src/evidence.mjs`: strict SKU-and-pose PDF evidence matching; trusted `onlineLookup` backend interface; prevents mixing PDF reference pixels with physical millimeters without a same-SKU calibration bridge. A pack's volume is never used to infer its physical dimensions.
- `src/planner.mjs`: scene graph for 3–4 products, three intentionally named structures, single evidence-compatible height scale, alpha-silhouette overlap measurement, protected printed-label rectangles, 2D layer ordering and constrained object rotation. It ranks candidate layouts but **does not claim art-direction approval**.
- `src/renderer.mjs`: separate contact, ambient-ground and overlap shadow passes behind unchanged alpha-cutout product assets, with transparent RGBA export (no podiums, backgrounds, fabricated packages or retouching).
- `test/core.test.mjs`: executable unit tests for evidence resolution, unknown/estimated cases, valid ratios, deterministic options, label collisions, and prevention of mixed-unit comparisons.

## Interface contract (future integration)

```js
const product = {
  id: 'immutable-file-checksum',
  sku: 'verified exact SKU', pose: 'upright_closed',
  width: 300, height: 850, // tight ALPHA silhouette bounds, not JPG dimensions
  maskGrid: Uint8Array /* 48x48 downsampled original ALPHA for scoring */,
  labels: [{x:.2,y:.36,w:.6,h:.3,confirmed:true}], // OCR + human QA input
  role: 'hero', // or wide, secondary, accent
  evidence: {
    status: 'pdf_exact', referenceHeightPx: 1200,
    referenceFrame: 'forever52_60ml_1200px',
    source: { type:'pdf', page:7, sku:'...', pose:'upright_closed' }
  }
};
const draft = planCompositions([product, ...]);
// options[].approval never indicates Photoshop-grade approval.
renderTransparentComposition(canvas, {
  ...draft, layers:draft.options[0].layers
}, imageSources, shadowSettings);
```

The source file and raw alpha are never edited by these composition modules. RGB pixels are only sampled by the browser's standard image scaling/rotation operation. Shadows are independent transparent layers.

## Evidence and scale rules

1. Exact PDF match requires **verified SKU + pose + page + reference frame**. Current embedded catalog is a manually curated seed, not complete PDF ingestion.
2. If missing from the PDF, the intended `onlineLookup` is a **trusted server-side adapter** that must provide SKU, pose, measured millimeters, source URL, and check date. The adapter is tested with mock responses; there is no live Google/product search in this isolated branch.
3. Reference pixels and millimeters are incompatible unless an **identical SKU / pose appears in both systems** for calibration.
4. Unknowns are **never silently converted from 30ml/100ml into height**; an explicitly labelled visual draft may use source pixels/proxy, but must not be approved for ratio-accurate production.

## Visual architecture principles

A professional result requires more than non-overlapping rectangles. Each candidate therefore carries a scene graph with actual alpha silhouettes, optical content annotations, relative size evidence, z-order, constrained rotation, plane depth and editable shadows. The geometry solver is not itself an art director. Its output must be evaluated as a rendered 2000×2000 transparent PNG under visual QC.

**The missing critical dependency:** robust automatic OCR/logo/printed-content polygons with confidence; the current `labels[]` rectangles are manually annotated QA fixtures. Without reliable detection, the algorithm can misjudge visual importance and automatically generated layouts cannot be certified for arbitrary products.

## How tests were run

```
node test/core.test.mjs
```

The private QA harness loaded four already existing transparent skincare images into a browser from in-memory data URLs (not GitHub assets). It produced three full 2000×2000 transparent PNGs, compared shadows enabled/disabled, and checked output diagnostics. Source images and private PDFs are excluded from the public research branch.

## No-go gate and integration policy

- CTO: all uploaded 3–4 products retained, reference ratios within 1% for exact matches, source files immutable, no unsupported unit conversions, no clipped geometry, transparency and independent shadow passes tested.
- Chief Creative Director: actual 2000px output accepted for hierarchy, negative space, label legibility, depth, shadows and meaningful differentiation, against the provided Nykaa reference examples. **No scores override human creative rejection.**
- CEO: existing cutout/edge editor, PDF evidence, guideline checking, regeneration, project persistence, layer editability and transparent export remain intact. Never replace the full FRAME tool with a standalone composition toy.

Current verdict: **not approved**. Do not merge into `main` or overwrite `/lab/`.