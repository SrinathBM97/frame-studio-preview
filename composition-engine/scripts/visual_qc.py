#!/usr/bin/env python3
"""FRAME transparent-render QC. Consumes local render outputs; never uploads client assets.

Usage: python scripts/visual_qc.py --plan qa/plan.json --render-dir qa --output qa/visual_qc.json
Only reports measurable image properties; never grants art-director approval.
"""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image

def evaluate(plan_path,render_dir,output):
 plan=json.loads(Path(plan_path).read_text())
 results=[]
 for ix,opt in enumerate(plan['options'],1):
  img=Image.open(Path(render_dir)/f'visual_{ix}.png').convert('RGBA');a=np.asarray(img)
  mask=a[:,:,3]>180
  if not mask.any():raise RuntimeError('Blank composition: '+opt['id'])
  ys,xs=np.nonzero(mask)
  optical=float(xs.mean())/img.width
  footprint=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  structure=opt['qa']['structure'];warnings=[]
  if img.size!=(2000,2000):warnings.append('invalid-export-resolution')
  if int(a[0,0,3])!=0:warnings.append('nontransparent-corner')
  if structure['occlusionCount']<2:warnings.append('weak-layer-interaction')
  if structure['coverage']>.81:warnings.append('group-too-wide')
  if sum(abs(l.get('rotation',0))<3 for l in opt['layers'])>=3:warnings.append('predominantly-frontal-packshots')
  if opt['qa']['hardFailures']:warnings.append('geometry-or-text-occlusion-failure')
  results.append({'direction':opt['id'],'rgba':True,'dimensions':list(img.size),'bbox':footprint,'opticalMassX':round(optical,4),'warnings':warnings,'automaticPass':not any(x in warnings for x in ['invalid-export-resolution','nontransparent-corner','group-too-wide','geometry-or-text-occlusion-failure']),'creativeApproval':'REQUIRES_INDEPENDENT_HUMAN_REVIEW'})
 off=Path(render_dir)/'visual_no_shadows.png'
 if off.exists():
  a=np.asarray(Image.open(Path(render_dir)/'visual_1.png').convert('RGBA'),dtype=np.int16)
  b=np.asarray(Image.open(off).convert('RGBA'),dtype=np.int16)
  diff=(np.max(np.abs(a-b),axis=2)>1)
  results[0]['shadowChangedPixels']=int(diff.sum())
  results[0]['castShadowOnExistingProductsPixels']=int(np.logical_and(diff,b[:,:,3]>230).sum())
  results[0]['visibleShadowOutsideProductsPixels']=int(np.logical_and(a[:,:,3]>20,b[:,:,3]<=20).sum())
 report={'schema':'frame-visual-qc/5','noAutomaticCreativeApproval':True,'options':results,'releaseRecommendation':'NO_PRODUCTION_RELEASE_WITHOUT_ART_DIRECTOR_APPROVAL'}
 Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(report,indent=2))
 return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--plan',required=True);ap.add_argument('--render-dir',required=True);ap.add_argument('--output',required=True)
 args=ap.parse_args();result=evaluate(args.plan,args.render_dir,args.output)
 print(json.dumps({'results':len(result['options']),'flags':[p['warnings'] for p in result['options']]},indent=2))
