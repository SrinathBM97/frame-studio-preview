"""FRAME pixel-level evaluator for independently approved gold segmentation masks.

Requires *same pixel coordinate frame* for source, prediction, and gold, not
centered/normalized silhouettes. It produces scientific metrics, not an art approval.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def compute_metrics(gold_alpha:np.ndarray,pred_alpha:np.ndarray,
                    rgb_source:np.ndarray|None=None,rgb_export:np.ndarray|None=None,
                    tolerance_px:int=2):
    if gold_alpha.shape!=pred_alpha.shape:raise ValueError('Prediction and gold must share original source pixel geometry')
    if gold_alpha.ndim!=2:raise ValueError('Grayscale alpha channel required')
    g=np.asarray(gold_alpha)>=128;p=np.asarray(pred_alpha)>=128
    tp=int((g&p).sum());fp=int((~g&p).sum());fn=int((g&~p).sum())
    iou=tp/max(1,tp+fp+fn)
    precision=tp/max(1,tp+fp);recall=tp/max(1,tp+fn)
    gc=cv2.Canny((g.astype('uint8')*255),80,150)>0
    pc=cv2.Canny((p.astype('uint8')*255),80,150)>0
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(tolerance_px*2+1,)*2)
    expanded_g=cv2.dilate(gc.astype('uint8'),k)>0
    expanded_p=cv2.dilate(pc.astype('uint8'),k)>0
    bp=float((pc&expanded_g).sum())/max(1,int(pc.sum()))
    br=float((gc&expanded_p).sum())/max(1,int(gc.sum()))
    bf1=2*bp*br/max(bp+br,1e-12)
    soft=((pred_alpha>8)&(pred_alpha<247)).sum()
    metric={'iou':round(float(iou),5),'foreground_recall':round(float(recall),5),
            'foreground_precision':round(float(precision),5),
            'lost_gold_pixels':fn,'false_background_removed_pixels':fp,
            'boundary_f1_at_tolerance':round(float(bf1),5),
            'boundary_tolerance_px':tolerance_px,
            'partial_alpha_pixels':int(soft)}
    if (rgb_source is None) != (rgb_export is None):raise ValueError('Provide both source and exported RGB for original-color check')
    if rgb_source is not None:
        if rgb_source.shape!=rgb_export.shape or rgb_source.shape[:2]!=g.shape:
            raise ValueError('RGB compare requires source-aligned pixel geometry')
        opaque=pred_alpha==255
        diff=(rgb_source.astype('int16')-rgb_export.astype('int16'))
        changed=int(np.any(diff!=0,axis=2)[opaque].sum())
        metric.update({'opaque_original_pixels_changed':changed,
                       'opaque_original_pixels_compared':int(opaque.sum()),
                       'opaque_original_RGB_preserved':changed==0})
    return metric

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gold',required=True);ap.add_argument('--prediction',required=True);ap.add_argument('--source');ap.add_argument('--output');ap.add_argument('--tolerance',type=int,default=2)
    a=ap.parse_args()
    gold=np.asarray(Image.open(a.gold).convert('L'))
    pred_im=Image.open(a.prediction).convert('RGBA');alpha=np.asarray(pred_im.getchannel('A'))
    src=np.asarray(Image.open(a.source).convert('RGB')) if a.source else None
    dst=np.asarray(pred_im.convert('RGB')) if a.source else None
    result=compute_metrics(gold,alpha,src,dst,tolerance_px=a.tolerance)
    report=json.dumps(result,indent=2)
    if a.output:Path(a.output).write_text(report)
    print(report)
