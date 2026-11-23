# FRAME — Cutout & Composition Quality Benchmark (23 November 2026)

**Decision: NO-GO. No changes to the live FRAME app.** This is a research baseline and rejection gate, not a replacement cutout or composition engine.

## Tested assets and algorithms

Four existing original source photographs (Dot & Key 30 ml serum, Biodance mask set, COSRX Snail 96, Face Shop cleanser), four previously exported RGBA cutouts, and the three actual 2000×2000 FRAME Core v6 drafts. These originals are **not** included in the publicly shared GitHub branch.

Available algorithms: (A) bright-background connected-region separation and (B) OpenCV GrabCut color segmentation. Compared each with a previous RGBA cutout using height-normalized silhouettes. This comparison is deliberately a **proxy**, because the previous cutout is not independent expert ground truth. It can detect dramatic missing silhouettes but cannot certify accuracy, high-quality transitions, clear glass, or label preservation. Each binary method produces zero alpha transition pixels, which does not guarantee desirable edge appearance.

| Product | White-background proxy IoU | GrabCut proxy IoU | Observation |
|---|---:|---:|---|
| Dot & Key serum | 0.912 | 0.961 | Visually close, but foot shadow/fringe and jagged binary edges need expert inspection |
| Biodance mask set | 0.993 | 0.997 | Visually close in outline; cannot conclude all mask/print details correct |
| COSRX Snail 96 | **0.651** | **0.528** | Both methods falsely treat portions of the pale bottle as background; **automatic reject** |
| Face Shop cleanser | 0.981 | 1.000 | Proxy looks close in silhouette; does not prove packaging RGB fidelity or absence of halos |

The input to this benchmark is an original JPEG, not the original earlier live AI model result. Consequently **these numbers must not be presented as model-quality scores for IS-Net, BiRefNet, or FRAME's current browser model**.

## Root technical problem

The product's low-contrast boundary and white/frosted material are confounded with a white photographic background. A pure background-distance or generic color clustering model can erase the object interior or foot. Changing feather/smooth controls cannot recover this missing content. A narrow hard contour is not always a clean contour: source JPEG background-contaminated edge RGB can still create fringe after alpha masking.

## Composition benchmark — actual v6 export

All three drafts are valid 2000×2000 transparent PNGs; product placement uses alpha masks and label rectangles. They are not commercially art-directed. Release gate results:

- Sculptural Cluster: foot-position standard deviation **0.030**, below the 0.045 diagnostic threshold; group-height fraction **0.565** (<0.61).
- Diagonal Interlock: fewer than two meaningful foreground/back interactions and limited vertical rhythm (**0.602**).
- Editorial Asymmetry: foot-position standard deviation **0.043** and fewer than two meaningful layer interactions.
- Two skincare products have no independently verified size evidence; the complete group is not ratio-approved.
- Human commercial art-direction review is unapproved. These heuristics **reject obvious problems only**; numerical scores do not imply Photoshop-level quality.

## Architecture decisions locked

1. **Segment first, audit second:** use a model-evaluation harness with native or aspect-preserving preprocessing, preserve original RGB, apply mask only to alpha. Require expert-reviewed gold masks for each hard material class (opaque black, light/frosted white, plastic, multi-part packaging, transparent glass).
2. **Reject instead of crop:** use source-position-aware full-silhouette comparison plus boundary uncertainty heatmaps to flag unexpectedly missing areas. No automatic erosion/feather defaults. Material and interior-hole tests are product-specific (the eye holes of a sheet mask are not an error).
3. **Benchmark multiple commercially usable models:** BiRefNet general-purpose (MIT-licensed editions require checking exact weights and dependency licenses), IS-Net general-use (check upstream model and weights rights); exclude unlicensed commercial use of BRIA RMBG-2.0 weights (noncommercial license without separate agreement). Model weights were not available to run in this environment.
4. **Pre-commercial gating:** original source hashes unchanged; expert gold-mask edge recall and contour accuracy; no unapproved package RGB modification; documented scale status; label visibility; group depth/shadow; real render comparison by Chief Creative Director.
5. **Fail closed:** if mask, ratio, rendering or art-direction evidence is insufficient, FRAME may show explicitly labeled draft/review but not call it production-ready.

## Not yet proven

No neural-model side-by-side results (blocked by unavailable model weights and network), no pixel-registered original-vs-cutout RGB benchmark, no gold masks annotated against the original photos, and no independent professional composition reference made with these **same** four packshots. The makeup compact/foundation screenshots are historical visual failures but their raw originals are not in this baseline set.

## Verification

- `python benchmarks/quality_benchmark.py` produces private QA images and metrics given the original assets. **Never publish those assets to a public GitHub repository.**
- `python benchmarks/release_gate.py` denies release on missing gold/model evidence, unverified scale, and flat composition diagnostic conditions.
- `pytest benchmarks/test_quality.py` uses the real private inputs and all tests pass locally; CI uses separate synthetic fixtures only.

**CEO: NO-GO. CTO: Benchmark harness and evidence-driven rejection pass, model performance not verified. Chief Creative Director: composition quality REJECTED.**
