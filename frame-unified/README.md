# FRAME — Unified development codebase

**Status: engineering integration, not commercial release.** This is the next development line for FRAME, not another independent v7/v8 demo. The `main` branch and existing GitHub Pages beta remain unchanged.

## How this is assembled

- `web/index.html` is carried forward from the existing FRAME professional editor, preserving source uploads, browser cutout review, scale lab, guideline PDF check, controls, project JSON and export.
- `web/core-bridge.js` connects that existing editor to the **same-origin Python engine** when available. It transfers an approved source image and **its alpha mask separately**; never reconstructs product packaging. Shows all three composition options, status, QC and shadows, with final publication blocked.
- `frame_core/server.py` serves the existing interface and mounts the pre-existing v6 FastAPI engine under `/api` rather than replacing the browser interface.
- `frame_core/{assets,evidence,planner,shadows,mask_edit,pdf_index,online,creative_qc}.py` are retained from FRAME v6, with targeted fixes to mask semantics, persistent plans and ratio/quality gating.
- `quality/` contains reusable gold-mask evaluation and release-gate logic from the quality benchmark.
- `tests/` provides synthetic source-image and HTTP-level integration regressions (not customer photography).

## Actual fixes in this integration

1. **Project persistence:** `plan.json` survives API session reset and is invalidated on product/mask changes.
2. **Correct alpha semantics:** transparent PNG masks use alpha, opaque grayscale masks use luminance; saved mask is exactly the applied matte. Original uploaded bytes are SHA-256 checked.
3. **One-origin UI and API:** `/` serves existing editor; `/api` serves backend; no cross-origin/manual API configuration in the interface.
4. **No arbitrary product role by upload index:** browser adapter does not force third image to a wide-product role.
5. **Shadows connected:** existing shadow color, opacity and blur controls feed the backend preview renderer.
6. **Shared release decision:** `/api/projects/{id}/quality` reports known geometry, ratio, creative and cutout blockers. **NO-GO** is mandatory until real cutout and visual benchmarks pass.
7. **Data handling notice:** user-visible warning: syncing uploads products to a backend, and this research backend has no account authentication. Do **not** expose it publicly for client images.

## Research tests

Run `python -m pytest -q tests/test_integration.py tests/test_public_ci.py quality/test_public_synthetic.py` in the engineering environment. `tests/browser_mock_smoke.py` is an optional Chromium UI smoke with a **mocked API**, while `tests/test_integration.py` tests the **real API** via TestClient. A direct Chromium-to-local-HTTP test was blocked by the evaluation environment; do not count the mocked test as real deployed/browser E2E.

## Deployment and sensitive information

The existing Pages site is static and **cannot run Python**. A production backend deployment requires secure persistent storage, authentication, file lifecycle policies, commercial model licensing, job queue/compute, observability and visual release acceptance. No passwords, raw uploaded customer images, Nykaa chart PDF or private test fixtures are committed to this **public** GitHub research branch.

For authorized backend operators, environment variables are `FRAME_NYKAA_PDF` (licensed PDF on private persistent storage) and `FRAME_DATA_DIR` (private persistent asset storage). **This is not an instruction for the user to configure Python.**

**Next priority:** verified cutout-model evaluation against expert-reviewed original-resolution masks; real online same-SKU dimension lookup; reference-guided creative optimization; secure backend deployment. Do not merge to `main` until CEO/CTO/Chief Creative Director QC passes.
