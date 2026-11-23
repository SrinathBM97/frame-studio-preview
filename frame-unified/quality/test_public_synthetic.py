"""Safe public regression: synthetic imagery only, no customer assets."""
import numpy as np
from PIL import Image
from pathlib import Path
from quality.quality_benchmark import normalize_silhouette, mask_metrics
from quality.gold_mask_evaluator import compute_metrics
from quality.release_gate import evaluate

def test_gold_metrics_detect_missing_rim():
    gold=np.zeros((80,90),dtype=np.uint8)
    gold[10:70,20:71]=255
    pred=gold.copy();pred[45:65,20:30]=0
    x=compute_metrics(gold,pred)
    assert x['lost_gold_pixels']==200
    assert x['foreground_recall']<1
    assert x['iou']<1
    assert x['boundary_f1_at_tolerance']<1

def test_rgb_fidelity_detects_changed_original_pixels():
    gold=np.ones((30,40),dtype='uint8')*255
    source=np.zeros((30,40,3),dtype='uint8')+120
    exported=source.copy();exported[3,4,0]+=1
    check=compute_metrics(gold,gold,source,exported)
    assert check['opaque_original_pixels_changed']==1
    assert not check['opaque_original_RGB_preserved']

def test_rejects_unverified_products_even_if_geometry_passes():
    mock={'assets':[],'neural_models_tested':[]}
    plan={'canvas':2000,'ratio_verified':False,'directions':[]}
    x=evaluate(mock,plan)
    assert x['decision']=='NO_GO'
    assert any('verified scale' in r for r in x['rejection_reasons'])

def test_matte_proxy_is_not_expert_gold():
    m=np.zeros((80,120),np.uint8);m[10:70,25:85]=255
    assert normalize_silhouette(m).sum()>0
    assert 'proxy_normalized_silhouette_iou' not in mask_metrics(m)
