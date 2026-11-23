import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from quality_benchmark import ASSETS,normalize_silhouette,mask_metrics
from release_gate import evaluate

BENCH=Path(__file__).resolve().parents[1]

def test_normalization_preserves_silhouette_and_ratios():
    m=np.zeros((400,300),dtype=np.uint8);m[50:350,100:200]=255
    n=normalize_silhouette(m)
    assert n.sum()>1000
    assert normalize_silhouette(np.zeros((4,4),dtype=np.uint8)).sum()==0

def test_evaluation_does_not_mislabel_proxy_as_gold():
    r=json.loads((BENCH/'output/benchmark_results.json').read_text())
    p=json.loads(Path('/mnt/data/FRAME_CORE_V6/proof/v6_plan.json').read_text())
    q=evaluate(r,p)
    assert q['decision']=='NO_GO'
    assert any('gold segmentation' in x for x in q['rejection_reasons'])
    assert any('COSRX' in x for x in q['rejection_reasons'])
    assert any('verified scale' in x for x in q['rejection_reasons'])

def test_originals_not_overwritten():
    # Benchmark scripts never write to the incoming originals folder.
    from quality_benchmark import hash_file
    r=json.loads((BENCH/'output/benchmark_results.json').read_text())
    for a in r['assets']:
        raw=next(p for p in Path('/mnt/data').glob('*.jpg') if hash_file(p)==a['source_sha256'])
        assert raw.exists()

def test_actual_composition_exports_are_transparent():
    r=json.loads((BENCH/'output/benchmark_results.json').read_text())
    assert len(r['composition'])==3
    for a in r['composition'].values():
        assert a['rgba_dimensions']==[2000,2000]
        assert a['transparent'] and not a['edge_touch']
