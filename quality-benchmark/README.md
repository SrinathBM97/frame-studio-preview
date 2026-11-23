# FRAME — Quality Benchmark (research-only)

Private company assets are not stored here or committed to GitHub.

- `benchmarks/quality_benchmark.py`: operates on four locally mounted source photos and previously generated cutouts. Runs two simple CPU methods to establish failure modes and outputs comparison previews and quantitative *proxy* agreement. Does not benchmark AI models unless provided externally.
- `benchmarks/gold_mask_evaluator.py`: independent gold-mask pixel geometry; computes foreground recall, IoU, boundary F1 at a 2px radius, and original RGB-change count when source and output are pixel-aligned.
- `benchmarks/release_gate.py`: reject-only evaluation of original v6 draft placement, missing gold/weights and product-scale uncertainty.
- `benchmarks/test_public_synthetic.py`: fixtures that can run in public GitHub Actions with no user images or licensed chart assets.
- `BENCHMARK_FINDINGS.md`: measured research results, shortcomings, and commercially conservative no-go recommendation.

## Local test commands

`pytest -q benchmarks/test_public_synthetic.py`

Private asset-dependent, only in an approved confidential working directory:

`python benchmarks/quality_benchmark.py --assets /path/to/private-assets --proofs /path/to/v6/exports --output /path/to/private-benchmark-output`

`python benchmarks/gold_mask_evaluator.py --gold gold-alpha.png --prediction model-output.png --source original-source.jpg`

## Honest constraints

No deep-learning model weights or verified expert gold masks were available in the test environment. The thresholds and proxy IoUs do **not** certify product cutout quality or creative quality. Pixel-aligned original-source RGB verification is not possible on previously cropped/replaced assets; it must be measured at ingestion in the rebuilt backend.
