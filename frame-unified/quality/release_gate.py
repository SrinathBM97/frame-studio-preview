"""FRAME research gate. Metrics are rejection tests, never a Photoshop-grade approval.

Requires explicitly reviewed gold masks for a release decision. Existing alpha masks
and normalized silhouette agreement are useful regression proxies but not ground truth.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def evaluate(report:dict, plan:dict, gold_mask_directory:Path|None=None)->dict:
    reject=[];checks=[]
    by_name={x['name']:x for x in report['assets']}
    # Conservative regression: a baseline that loses obvious product body pixels is unsafe.
    for a in report['assets']:
        base=a['methods']['grabcut']
        white=a['methods']['white_background_connectivity']
        for name,candidate in [('grabcut',base),('white_background_connectivity',white)]:
            iou=candidate.get('proxy_normalized_silhouette_iou',0)
            if iou<.90:
                reject.append(f'{a["name"]}: {name} disagrees with prior alpha silhouette ({iou:.3f} < 0.90 proxy threshold)')
            # Binary alpha has no antialiasing and may show stair-step edges: NOT an automatic pass.
            if candidate['alpha_transition_pixels_per_perimeter_pixel']<0.2:
                checks.append(f'{a["name"]}: {name} has no antialiasing; visually check jagged edges')
    if not gold_mask_directory or not gold_mask_directory.is_dir() or not any(gold_mask_directory.glob('*.png')):
        reject.append('No independently human-verified gold segmentation masks for original products')
    if not report['neural_models_tested']:
        reject.append('No neural segmentation weights were runnable in the evaluation environment')
    for scene in plan.get('directions',[]):
        name=scene.get('style','unnamed')
        if not scene['qa']['pass']:
            reject.append(f'{name}: failed geometry/label safety')
        metrics=scene['qa']['metrics']
        layers=scene['layers']
        from statistics import pstdev
        feet=[(l['y']+l['h'])/plan.get('canvas',2000) for l in layers]
        overlap=[x['occlusion'] for x in metrics['labels']]
        if pstdev(feet)<.045:
            reject.append(f'{name}: weak depth stagger; feet stdev {pstdev(feet):.3f} < 0.045')
        if sum(x>.015 for x in overlap)<2:
            reject.append(f'{name}: fewer than two meaningful layer interactions')
        if metrics['group_height']<.61:
            reject.append(f'{name}: insufficient vertical rhythm {metrics["group_height"]:.3f} < .61')
        if metrics['group_width']>.72:
            reject.append(f'{name}: spread too wide ({metrics["group_width"]:.3f})')
    if not plan.get('ratio_verified'):
        reject.append('Not all product heights have evidence-compatible verified scale')
    reject.append('Independent human art-direction acceptance of the actual exports has not been recorded')
    return {'decision':'NO_GO' if reject else 'REVIEW_REQUIRED',
            'rejection_reasons':reject,'manual_review_items':checks,
            'claim':'Automated checks can veto obvious errors, never certify Photoshop-level quality'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--benchmark',default='/mnt/data/FRAME_Quality_Benchmark/output/benchmark_results.json');p.add_argument('--plan',default='/mnt/data/FRAME_CORE_V6/proof/v6_plan.json');p.add_argument('--out',default='/mnt/data/FRAME_Quality_Benchmark/output/release_gate.json')
    a=p.parse_args();report=json.loads(Path(a.benchmark).read_text());plan=json.loads(Path(a.plan).read_text());r=evaluate(report,plan)
    Path(a.out).write_text(json.dumps(r,indent=2));print(r['decision']);print('\n'.join(' - '+x for x in r['rejection_reasons']))
