"""Consolidated non-certifying checks for the single FRAME development workspace.

This gate is intentionally fail-closed. A test score cannot replace expert-reviewed
cutout ground truth or art-director acceptance of the final exported pixels.
"""
from __future__ import annotations


def assess(project: dict) -> dict:
    problems=[]
    items=list(project['products'].values())
    if len(items) not in (3,4):
        problems.append('A composition requires 3–4 products')
    for product in items:
        if not product['asset'].hash_unchanged():
            problems.append('Original product file has changed: '+product['id'])
        if not product['asset'].mask_approved:
            problems.append('Cutout mask requires approval: '+product['id'])
    plan=project.get('plan')
    if not plan:
        problems.append('No composition plan generated')
    else:
        if not plan.get('ratio_verified'):
            problems.append('One or more product ratios remain unverified')
        for i,d in enumerate(plan.get('directions',[]),1):
            if not d.get('qa',{}).get('pass'):
                problems.append(f'Option {i} failed geometry or label safety')
            if not d.get('creative_qc',{}).get('creative_approved',False):
                problems.append(f'Option {i} has no independent creative approval')
    if project.get('guidelines'):
        if project['guidelines'].get('compliance')!='verified':
            problems.append('Brand-guideline assessment is not certified')
    # Absolute blockers apply until a professionally reviewed benchmark is completed.
    problems.append('Human-approved segmentation gold-mask benchmark not completed')
    problems.append('Professional art-direction approval of actual exports not recorded')
    return {'decision':'NO_GO','reasons':problems,'claims':'Engineering research only; no production-ready claims',
            'originals_unchanged':all(x['asset'].hash_unchanged() for x in items),
            'product_count':len(items)}
