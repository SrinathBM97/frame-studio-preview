# FRAME Core Engine — Research foundation (v6)

**Status: engineering research; NOT a finished product, NOT merged to the live FRAME app.**

This is the first independent Python/FastAPI implementation of the core subsystems. It is not a cosmetic HTML revision and does not replace the current FRAME editor, its PDF guideline upload, project save, mask editing, or output interface.

## Implemented and exercised

- `frame_core/evidence.py` — strict exact Nykaa SKU + pose catalog. Five manually verified entries are checked against actual PDF page text at backend start. Exact COSRX 1340 px / Dot & Key 781 px share the correct reference frame. Unknown dimensions remain **unknown**; draft height is labeled unverified, not passed off as mm.
- `frame_core/pdf_index.py` — reads all 19 pages and extracts measurements as *unattributed* category height entries. It does **not** assign measurements to unverified packshot identities based on nearby text.
- `frame_core/online.py` — verifies exact same-SKU physical Product.height from structured online product data. Requires a production search backend; no API is connected, and retail pack weights/volumes and shipping dimensions are rejected.
- `frame_core/assets.py` — immutable original image files, SHA-256 tracking, alpha import, approval gate, OCR-derived label regions; JPEGs without an alpha mask are blocked from composition.
- `frame_core/mask_edit.py` — reversible zero-default mask feather/smooth/expand/contract and restore/erase brush. No RGB alteration.
- `frame_core/planner.py` — evidence-locked sizes, 3 composition directions, alpha-mask overlap and OCR-label occlusion scoring, geometry safe-area rejection.
- `frame_core/shadows.py` — transparent PNG renderer with separate bottom silhouette contact shadows, soft ground shadows and product-on-product cast shadows; tunable HEX/opacity/blur/offset. Shadows never modify original uploaded packshot file.
- `frame_core/creative_qc.py` — **reject-only** automated visual heuristics; a numerical layout score never certifies commercial creative quality.
- `frame_core/api.py` — project/asset upload, mask import/approval, brand PDF text audit, evidence lookup, composition drafts, true PNG previews, persistent project metadata/reopen and fail-closed final export.

## Tests

- `pytest -q tests/test_public_ci.py`: synthetic public unit tests (run in GitHub Actions; no private assets).
- Full internal tests: source/reference-chart tests + 4 real skincare packshot API upload/compose/export and shadow-delta checks. These fixtures stay local/private and are **not committed**.

## Deployment

GitHub Pages cannot run this FastAPI/Python processing backend. The current GitHub Pages lab remains untouched. This research branch is not an accessible hosted app. A backend hosting provider with persistent storage/model execution must be provisioned later, after QC and authorization; do not ask a designer to run Python or configure APIs.

For service operators only (not an instruction to the end user): `FRAME_NYKAA_PDF` points to a licensed locally mounted copy of the supplied 19-page PDF; `FRAME_DATA_DIR` points to private persistent project storage. No private PDF/photos/model weights are committed to the public repository.

## Outstanding hard blockers

1. **Automatic cutout:** no production segmentation model loaded or validated against clipped compact/foundation test cases. Current API requires an approved supplied alpha mask or manually corrected mask. 0 processing is guaranteed in the mask editing path; original JPEG white fringing remains unsolved.
2. **Ratios:** 5 manually verified chart mappings; rest require automatic visual SKU association, verified online physical measurements or explicit uncertainty. Online search provider currently unavailable.
3. **Creative quality:** real four-product renders remain frontal/flat despite genuine ground and overlap shadows. `creative_qc` rejects weak arrangements and cannot autonomously establish visual excellence.
4. **Brand PDF check:** only extraction of text/colors, not full layout or brand policy verification.
5. **Commercial product:** no tenant authentication, security review, live backend deployment, completed composition quality benchmark, approved output or product billing.

**No commercial export should be permitted until mask, sizing, composition and three-role QC pass.**
