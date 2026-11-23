# FRAME unified integration quality record

Date: 23 November 2026. Decision: **ENGINEERING INTEGRATION PASS / CREATIVE NO-GO / RELEASE NO-GO**.

## Verified

- Tests: **9 passed** in real FastAPI/synthetic regression across `tests/test_integration.py`, `tests/test_public_ci.py`, `quality/test_public_synthetic.py`.
- Browser editor bridge: Chromium `set_content` + mocked API: 3 synthetic uploads, 13 request dispatches, three draft option cards, 0 JS page errors. This is UI-only, not an end-to-end real-server browser run.
- Real API TestClient: source file hash persists; transparent mask alpha semantics; approved mask round-trip; three composition options; persisted plan and mask state after backend session clear; 2000x2000 RGBA preview where geometry safe; final output blocked for unverified ratios.
- Brand-guideline PDF: parses sample color, truthfully leaves compliance `manual_review_required`.
- Existing FRAME browser workflows retained in the integrated HTML source; public main branch not updated.
- Cutout/scale/creative QC remains fail-closed.

## Failing or not verified

- Direct local Chrome-to-Python HTTP navigation was **blocked by environment policy** (`ERR_BLOCKED_BY_ADMINISTRATOR`). Do not misrepresent the browser mock as a full deployed browser acceptance test.
- High-quality automatic segmentation **not available or validated**, including cosmetic foundation and black compact failure cases.
- Real internet product dimension provider not connected; unknown values remain unknown.
- Visual art direction/realism **rejected** for the current planner; automated composition score is not expert approval.
- No tenant authentication, data isolation/retention policy, secure public hosting or validated commercial AI-model license. Do not use with confidential client imagery.
- No independent gold masks for benchmarked products. Quality gate is hard NO-GO.

## Roles

- CTO: codebase and integration tests **pass** for this controlled research scope.
- Chief Creative Director: visual compositions **rejected** until user-reference outputs pass.
- CEO: **no production/public backend deployment**, no main branch merge.
