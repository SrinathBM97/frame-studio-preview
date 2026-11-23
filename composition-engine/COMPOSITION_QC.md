# FRAME Composition Architecture v4 — executed QC

Date: 2026-11-23. Independent three-role gate: **CTO conditional PASS, CAD FAIL, CEO NO-GO**.

## Measured results

- Original 19-page Nykaa PDF was parsed; 1036px L'Oréal reference correctly verified on **page 6** (not page 4), Nykaa Stay All Day 741px open-with-cap on page 3, and COSRX 1340 / Dot & Key 781 on page 11.
- OCR detected **43 packaging text regions** across four actual user-supplied transparent skincare packshots, using Tesseract. This is automatic region detection, **not OCR perfection or independently verified SKU recognition**.
- 4-source test: all three actual 2000×2000 PNG renders passed the internal geometry/label gate (0 hard failures each), using alpha tight bounds and real detected OCR regions. Source images remained unchanged.
- 3-source test: all three candidate directions passed geometry; no unrequested wide-product role assigned. The older v3 plan erroneously created such a role.
- Exact COSRX/Dot & Key height ratio in each layout: 781/1340 = 0.5828358209. Two other products have estimated or unknown evidence; this set is NOT fully scale verified.
- Browser render uses no CDN or network. All three outputs have alpha=0 at (0,0), size 2000×2000, and no runtime errors.
- Shadow test: first scene with shadows vs off differs at **430,556 pixels**, with **95,510 pixels** above alpha=20 outside the object-only silhouette. Contact and overlap settings are genuinely operative.
- Manual qualitative review of exports: **FAIL**. Grouping and shadows are improved, but front-facing packshots still lack the editorial tension, overlap depth and art direction seen in professional reference compositions.

## Blockers not represented as solved

- No production backend / live online dimension search in this code; trusted adapter is tested, not connected.
- PDF index exposes page values, but full image/SKU-column interpretation is not automatic.
- OCR is word bounding boxes, not professional human-validated precise text polygons; some brands are missed on difficult packaging.
- Creative QC requires professional full-resolution approval on both makeup and skincare sets; makeup source alpha assets were not available for this v4 regression.
- No live app changes; this is an isolated research branch artifact.

## Verdict

CEO: no release. CTO: isolated functionality substantially improved but requires backend integration and stronger correctness tests. CAD: no production approval until actual compositions are visually accepted. Never use automated geometry scores to override creative rejection.