# FRAME Composition Engine v5 — reference-aware research proof

**Decision: engineering proof, NOT a production release.** Live FRAME Studio, cutout engine, PDF UI, project persistence, and public GitHub Pages website are unchanged.

## What was implemented

- `src/reference_grammar.mjs` — source/provenance-checked reference study with normalized subject bounding boxes, front/back order, approximate overlap topology, group bounds, and three derived art-direction territories. Rejects invalid reference geometry. **This is NOT automatic visual recognition of arbitrary references**; current test reference was annotated by an engineer from the fallback Nykaa style example in the user's skill ZIP. It is not presented as client-approved.
- `src/reference_planner.mjs` — source-pixel-preserving 3–4 product optimizer. Preserves exact reference ratios where evidence exists; respects product role, real alpha mask silhouettes, existing OCR-based label areas and safe margins; ranks candidate x/foot/rotation/occlusion relationships while refusing to approve creative quality automatically. Includes a hard visual-flag rejection when a group is oversized.
- `src/renderer.mjs` — creates genuinely separate ground contact/ambient shadows and **clips foreground overlap shadows to alpha silhouettes of products behind them**; eliminates the previous airbrushed halo outside overlap products. Original source RGBA files are never edited.
- `scripts/visual_qc.py` — post-rendered RGBA evaluator checks output pixel dimensions, transparent corner, optical ink mass, composition width, depth overlap and shadow delta compared with shadow-off. It never claims human creative approval.
- `test/public.test.mjs` — synthetic self-contained checks for reference provenance, ratio preservation, three distinct intent territories, and honest approval gates. Local private regression additionally runs real supplied skincare cutouts, OCR regions and the 2000px browser compositor.

## Reference provenance

`refs/nykaa_depth_study.json` represents human-estimated boxes of the fallback `nykaa-depth-composition-reference.png` provided inside the user's original skill. Only the reference image's **spatial relationships**, not any logos, background, arch, products or pixel colors, may influence planning. The referenced scene contains different categories (a sculptural shoe and fragrance bottles), so it is an *imperfect compositional analogy* for the four uploaded skincare packshots. This mismatch is precisely why v5 does not claim Photoshop-quality art direction.

## Verified results (2026-11-23)

- Synthetic Node tests: PASS; 4-packshot private Node test: PASS; 3-packshot regression: PASS.
- Actual Chromium browser: three 2000×2000 transparent PNG renders, PASS; no canvas runtime errors.
- OCR-region and geometry hard failures: zero per rendered option.
- COSRX/Dot & Key ratio: 781/1340 preserved exactly by dimension calculation. Face Shop and Biodance still **unverified/estimated**, so the four-product set is not scale compliant.
- Shadow comparison: 13,634 changed pixels on existing products, 87,127 visible alpha pixels outside the original no-shadow product silhouettes; this is a functionality test, not evidence of beautiful shadows.
- Automated visual QC: option 1 has an oversized 87% group width and weak layer interaction; other two pass geometry but remain predominantly frontal packshot clusters.
- Chief Art Director verdict: **FAIL** — the look still lacks the editorial depth and physicality of the reference. CEO: NO-GO.

## Non-negotiable constraints

Never use image generation to recreate product packaging. Never infer dimensions from ml/g or source pixel size. Never transfer podiums, backgrounds, design decorations or logos from a reference. The output is only the exact user-supplied products plus shadows on a genuine transparent PNG. Do not merge this branch into `main` until the final art-direction tests and missing scale evidence pass.

## Architecture usage

```js
import {planReferenceCompositions} from './src/reference_planner.mjs';
import {renderTransparentComposition} from './src/renderer.mjs';
const plan = planReferenceCompositions(products, approvedOrAnnotatedReference, {seed:23, trials:1200});
for (const option of plan.options) {
  // Not a substitute for human creative review.
  if (option.approval === 'CREATIVE_DIRECTOR_REVIEW_REQUIRED') {
    renderTransparentComposition(canvas, {canvas:plan.canvas,layers:option.layers}, immutableSources);
  }
}
```

## Not yet implemented

A full visual model that interprets arbitrary uploaded reference photos, reliable product pose classification / inferred 3D support, web research for missing physical dimensions, and a production integration. These cannot be represented as fixed by this isolated architecture proof.
