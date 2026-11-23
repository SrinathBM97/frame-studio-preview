# FRAME Composition v5 — independent QC decision

**Date:** 2026-11-23. **Release: NO-GO.** Main GitHub Pages unchanged.

## CEO
**FAIL**: Designers still cannot rely on automatic output as Photoshop-grade. One of three layouts is too wide; all look predominantly like upright packshot groupings. Customer-facing release is withheld.

## CTO
**CONDITIONAL PASS for isolated architecture**, with the following verified evidence:

| Gate | Test | Verdict |
| --- | --- | --- |
| Reference provenance | Rejects missing/invalid reference bounds and unsupported provenance | PASS |
| Multiple directions | Three named intent structures derived from one annotated reference | PASS as code, not as artistic quality |
| Ratio logic | COSRX 1340 px and Dot & Key 781 px, 781/1340=0.582835821 in every generated option | PASS |
| Unverified dimensions | Face Shop and Biodance remain explicitly estimated or unverified | BLOCKED for final size QC |
| Layer silhouettes | Uses original supplied alpha masks and original RGB source file bytes | PASS in tested code path |
| Label collision | OCR-region and silhouette planner: 0 geometry hard failures in each of 3 actual product scenes | PASS in sampled scenes; not universal |
| Browser export | Three 2000 × 2000 RGBA renders; transparent alpha at top-left | PASS |
| Cast shadows | Foreground cast shadow restricted to products behind it | PASS in browser render |
| Shadow delta | 13,634 changed pixels on already present product pixels, 87,127 nonzero shadow-only pixels outside product-only rendering | PASS functionality, not aesthetic QC |
| Actual reference understanding | Current guide uses human estimated role rectangles from fallback inspiration; no automatic object detector | NOT IMPLEMENTED |
| Full SKU ratio research | No authenticated backend web lookup or verified physical dimensions for every SKU | NOT IMPLEMENTED |

## Chief Art Director
**FAIL** based on actual 3-up 2000×2000 render contact sheet. All three lack strong three-dimensional visual hierarchy. Reference Echo resembles a left-to-right row with the wide pack on the right; it also exceeds group-width target and is automatically marked `BLOCKED_AUTOMATED_VISUAL_QA`. The remaining two are more compact but still look like frontal packshot clusters, not polished commercial art direction. Cannot approve solely based on a geometry score.

The fallback reference includes a sculptural shoe plus fragrance bottles and a colored decorative stage. Neither the stage nor those products can be copied into FRAME; category mismatch limits visual transfer. No AI-generated or retouched products were used in testing.

## Next production blockers

1. **Reference interpretation:** reliable automatic detection of role/object masks, depth graph, and composition grammar from arbitrary client-approved references with confidence; otherwise clearly flag manual/human-reviewed annotations.
2. **Creative optimizer:** should compare final rendered pixels against actual art-direction concepts and reject packshot rows; geometry-only scoring is insufficient. Needs stronger depth, but must not invent 3D angles unsupported by supplied packshots.
3. **Grounding:** confirm realistic physical support and category-aware contacts at full resolution, especially slanted products, pouches, boxes, and upright containers.
4. **Size research:** reliable online product dimensions/pose confirmation for missing chart SKUs through a permitted backend, without treating estimates as facts.
5. **End-to-end:** restore engine only within unified FRAME after all three-role QC gates pass. Do not drop cutout, guideline PDF, sizing, project save, or export features.
