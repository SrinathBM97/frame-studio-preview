"""Ratio-locked, OCR-aware, alpha-silhouette composition search.

This is a working geometric candidate generator, NOT an autonomous art director.
It rejects unsafe candidates and makes the uncertainty inspectable.
"""
from __future__ import annotations
import random
from dataclasses import dataclass,asdict
import numpy as np
from PIL import Image
from .evidence import resolve_scale

# Positions are intentionally distinct visual directions, not random full-canvas scatter.
# Each role contains (center x, foot y, z). Foot y is a 2D support-plane projection.
DIRECTIONS={
 'sculptural_cluster': {'wide':(.63,.765,0),'secondary':(.28,.807,1),'hero':(.465,.815,2),'accent':(.64,.842,3)},
 'diagonal_interlock': {'wide':(.39,.740,0),'secondary':(.23,.824,1),'hero':(.665,.814,2),'accent':(.53,.849,3)},
 'editorial_asymmetry':{'wide':(.62,.735,0),'secondary':(.705,.816,1),'hero':(.37,.805,2),'accent':(.55,.851,3)}
}

def choose_roles(items):
 roles={};used=set()
 for role in ('hero','wide','secondary','accent'):
  i=next((x for x in items if x.get('role')==role and x['id'] not in used),None)
  if i:roles[role]=i;used.add(i['id'])
 if 'hero' not in roles:
  i=max((x for x in items if x['id'] not in used),key=lambda x:x['size'][1]);roles['hero']=i;used.add(i['id'])
 if 'wide' not in roles:
  opts=[i for i in items if i['id'] not in used and i['size'][0]/i['size'][1]>.7]
  if opts:
   i=max(opts,key=lambda x:x['size'][0]/x['size'][1]);roles['wide']=i;used.add(i['id'])
 for role in ('secondary','accent'):
  if role not in roles:
   opts=[i for i in items if i['id'] not in used]
   if opts:
    i= min(opts,key=lambda x:x['size'][1]) if role=='accent' else max(opts,key=lambda x:x['size'][1]);roles[role]=i;used.add(i['id'])
 if len(used)!=len(items):
  for i in items:
   if i['id'] not in used:
    roles['secondary' if 'secondary' not in roles else 'accent']=i;used.add(i['id'])
 return roles

def downsample(image,preview=240):
 a=image.getchannel('A')
 return np.asarray(a.resize((max(1,round(image.width/2000*preview)),max(1,round(image.height/2000*preview))),Image.Resampling.BILINEAR))

def paint_masks(layers,items,preview=280,canvas=2000):
 lookup={x['id']:x for x in items}
 maps=[]
 for layer in sorted(layers,key=lambda v:v['z']):
  item=lookup[layer['id']];im=item['image'].crop();w=max(1,round(layer['w']/canvas*preview));h=max(1,round(layer['h']/canvas*preview))
  m=np.asarray(im.getchannel('A').resize((w,h),Image.Resampling.NEAREST))>128
  full=np.zeros((preview,preview),dtype=bool)
  x=int(round(layer['x']/canvas*preview));y=int(round(layer['y']/canvas*preview))
  sx=max(0,x);sy=max(0,y);dx=min(preview,x+w);dy=min(preview,y+h)
  if dx>sx and dy>sy:full[sy:dy,sx:dx]=m[sy-y:dy-y,sx-x:dx-x]
  maps.append((layer,full,m))
 return maps

def scene_qa(layers,items,canvas=2000,style='sculptural_cluster',preview=260):
 lookup={x['id']:x for x in items};hard=[];warnings=[]
 for l in layers:
  if l['x']<canvas*.045 or l['y']<canvas*.05 or l['x']+l['w']>canvas*.955 or l['y']+l['h']>canvas*.93:
   hard.append({'type':'unsafe_canvas_bounds','product':l['id']})
 maps=paint_masks(layers,items,preview,canvas)
 # A foreground product may overlap silhouette but not meaningful printed label areas.
 occlusions=[];label_stats=[]
 for i,(l,mask,local) in enumerate(maps):
  front=np.zeros_like(mask)
  for _,mask2,_ in maps[i+1:]:front |= mask2
  product=mask.sum();occluded=int(np.count_nonzero(mask & front));ratio=occluded/max(1,product)
  occlusions.append(ratio)
  if ratio>.33:hard.append({'type':'product_overhidden','product':l['id'],'fraction':round(ratio,4)})
  item=lookup[l['id']];labels=item.get('labels',[])
  criticalLoss=[];standardLoss=[]
  for b in labels:
   x=int((l['x']+b['x']*l['w'])/canvas*preview);y=int((l['y']+b['y']*l['h'])/canvas*preview)
   w=max(1,int(b['w']*l['w']/canvas*preview));h=max(1,int(b['h']*l['h']/canvas*preview))
   xl=max(0,x);xr=min(preview,x+w);yt=max(0,y);yb=min(preview,y+h)
   if xl>=xr or yt>=yb:continue
   region=mask[yt:yb,xl:xr]
   coverage=int(region.sum())
   if coverage==0:continue
   loss=float(np.count_nonzero(region&front[yt:yb,xl:xr]))/coverage
   if b.get('priority')=='critical':criticalLoss.append(loss)
   else:standardLoss.append(loss)
  key=max(criticalLoss,default=0);other=max(standardLoss,default=0)
  if key>.015:hard.append({'type':'brand_or_product_text_covered','product':l['id'],'loss':round(key,4)})
  if other>.12:hard.append({'type':'printed_text_covered','product':l['id'],'loss':round(other,4)})
  if not labels:
   warnings.append({'type':'ocr_unreliable','product':l['id'],'warning':'No labels verified; human label review needed'})
  label_stats.append({'id':l['id'],'critical_loss':round(key,4),'other_loss':round(other,4),'occlusion':round(ratio,4)})
 bounds=[min(x['x'] for x in layers),max(x['x']+x['w'] for x in layers),min(x['y'] for x in layers),max(x['y']+x['h'] for x in layers)]
 width=(bounds[1]-bounds[0])/canvas
 height=(bounds[3]-bounds[2])/canvas
 centroid=sum((l['x']+l['w']/2)*l['w']*l['h'] for l in layers)/sum(l['w']*l['h'] for l in layers)/canvas
 overlap=sum(occlusions)/len(occlusions)
 ground_variation=np.std([(l['y']+l['h'])/canvas for l in layers])
 # Gradual score: grouping, focal balance and overlapping edges, not a synonym for art quality.
 score=120-abs(width-.65)*160-abs(centroid-.5)*160-abs(height-.70)*100
 score-=abs(overlap-.055)*390
 score-=max(0,.016-ground_variation)*250
 if overlap<.012:score-=25;warnings.append({'type':'flat_group','value':overlap})
 if width>.83:score-=70;warnings.append({'type':'too_wide','value':width})
 if any(l['w']*l['h']>canvas*canvas*.35 for l in layers):score-=15
 score-=len(hard)*120
 return {'pass':not hard,'hard':hard,'warnings':warnings,'score':round(score,2),
         'metrics':{'group_width':round(width,4),'group_height':round(height,4),'centroid':round(centroid,4),'mean_occlusion':round(overlap,4),'ground_variation':round(float(ground_variation),4),'labels':label_stats}}

def plan(items,canvas=2000,trials=260,seed=17):
 if len(items) not in (3,4):raise ValueError('Require 3 or 4 products')
 sizes,warnings,verified=resolve_scale(items)
 roles=choose_roles(items)
 highest=max(v['height'] for v in sizes.values())
 # A verified ratio is shared across the entire plan; no product is resized for visual convenience.
 factor=canvas*.54/highest
 out=[]
 for j,(name,structure) in enumerate(DIRECTIONS.items()):
  rng=random.Random(seed+j*2023)
  candidates=[]
  for trial in range(trials):
   layers=[]
   for role,item in roles.items():
    spec=structure.get(role) or (.68,.84,2)
    h=sizes[item['id']]['height']*factor;w=h*item['size'][0]/item['size'][1]
    xcenter=(spec[0]+rng.uniform(-.063,.063))*canvas
    foot=(spec[1]+rng.uniform(-.028,.028))*canvas
    layers.append({'id':item['id'],'role':role,'x':round(xcenter-w/2,2),'y':round(foot-h,2),'w':round(w,2),'h':round(h,2),'z':spec[2]})
   qa=scene_qa(layers,items,canvas,name)
   candidates.append((not qa['pass'], -qa['score'],layers,qa))
  candidates.sort(key=lambda x:(x[0],x[1]))
  bad,neg_score,layers,qa=candidates[0]
  out.append({'style':name,'layers':layers,'qa':qa,'status':'draft_requires_art_director' if not bad else 'blocked_by_geometry','ratio_verified':verified})
 return {'canvas':canvas,'directions':out,'ratio_warnings':warnings,'ratio_verified':verified,
         'release_status':'blocked_pending_cutout_scale_and_art_QC',
         'note':'Automated QA does not assert Photoshop-level visual quality'}
