#!/usr/bin/env python3
"""Non-destructive OCR annotation; never retouches the user-supplied RGBA pixels.

Usage: python scripts_extract_labels.py image1.png image2.png --output annotations.json
Requires Pillow + pytesseract + installed Tesseract. A backend-only helper;
no user Python setup required in a future hosted deployment.
"""
import argparse, json, re, pathlib, sys
from PIL import Image
import pytesseract

KEYWORDS = {'biodance','cosrx','dot','key','face','shop','rice','water','bright','snail','96','niacinamide','strawberry', 'serum','mucin','radiant','vita','mask'}

def analyze(path):
    original=Image.open(path).convert('RGBA')
    bbox=original.getchannel('A').getbbox() or (0,0,*original.size)
    src=original.crop(bbox)
    w,h=src.size
    # OCR on a *temporary* neutral composite only, never replace source pixels.
    flat=Image.new('RGBA',(w,h),(246,246,246,255));flat.alpha_composite(src)
    data=pytesseract.image_to_data(flat.convert('RGB'),output_type=pytesseract.Output.DICT,config='--psm 11')
    found=[]; words=[]
    for i, raw in enumerate(data['text']):
        txt=str(raw).strip()
        try: conf=float(data['conf'][i])
        except (ValueError, TypeError):continue
        if conf<55 or len(re.sub(r'[^A-Za-z0-9]','',txt))<2:continue
        x,y,ww,hh=[int(data[k][i]) for k in ('left','top','width','height')]
        if ww<2 or hh<3:continue
        word=re.sub(r'[^a-z0-9]','',txt.lower())
        priority='brand' if word in {'biodance','cosrx'} else 'product' if word in KEYWORDS else 'standard'
        # Smaller typography remains protected, but larger front-panel claims are highest priority.
        if hh/h>.032 or ww/w>.42: priority='critical' if priority in ('brand','product') else 'product'
        # Small padding keeps nearby products from touching typography.
        pad=max(2,round(min(w,h)*.009))
        rx=max(0,x-pad);ry=max(0,y-pad)
        found.append({'x':round(rx/w,6),'y':round(ry/h,6),'w':round((min(w,x+ww+pad)-rx)/w,6),
         'h':round((min(h,y+hh+pad)-ry)/h,6),'text':txt,'confidence':round(conf/100,3),
         'source':'ocr','priority':priority})
        words.append(txt)
    # If OCR is unreliable, do not invent safe/known label locations.
    status='ocr_detected' if len(found)>=3 else 'needs_manual_review'
    return {'name':path.name,'width':w,'height':h,'sourceRect':{'x':bbox[0],'y':bbox[1],'w':w,'h':h},'labels':found,'text':' '.join(words),'status':status,
       'version':'frame-ocr/1','limitations':'OCR text boxes are not exact printed-label polygons; needs confidence-aware human QC for dense packs'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('images',nargs='+',type=pathlib.Path);p.add_argument('--output',required=True)
    args=p.parse_args();out={p.stem:analyze(p) for p in args.images}
    pathlib.Path(args.output).write_text(json.dumps(out,indent=2),encoding='utf8')
    print('OCR',len(out),'images;',sum(len(v['labels']) for v in out.values()),'regions')
