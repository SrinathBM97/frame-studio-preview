"""Non-destructive product intake and mask processing. No secret blur, no silhouette contraction."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass,asdict
import hashlib
import numpy as np
from PIL import Image
import pytesseract
from pytesseract import Output
import re

KEYWORDS={'cosrx','snail','mucin','biodance','rice','water','bright','strawberry','niacinamide','forever52','loreal','nykaa'}

@dataclass
class Label:
 x:float;y:float;w:float;h:float;confidence:float;text:str;priority:str
 def to_dict(self):return asdict(self)

class ProductImage:
 def __init__(self,path:Path):
  self.path=Path(path)
  self.source_hash=hashlib.sha256(self.path.read_bytes()).hexdigest()
  im=Image.open(path)
  if im.width>8000 or im.height>8000:raise ValueError('Image exceeds supported dimensions')
  self.source=im.convert('RGBA')
  original_alpha=np.asarray(self.source.getchannel('A'))
  if im.mode!='RGBA' or np.all(original_alpha==255):
   self.mask_approved=False
   self.mask_status='mask_required'
  else:
   self.mask_approved=False
   self.mask_status='requires_quality_review'
  self.labels=[]
 def set_mask(self,mask:Image.Image):
  if mask.size!=self.source.size:raise ValueError('Mask must match original image dimensions')
  a=mask.convert('L')
  rgb=self.source.convert('RGB')
  rgb.putalpha(a)
  self.source=rgb
  self.mask_status='requires_quality_review'
  self.mask_approved=False
 def approve_mask(self):
  if not self.source.getchannel('A').getbbox():raise ValueError('Empty product mask')
  self.mask_approved=True
  self.mask_status='approved_by_reviewer'
 def crop(self):
  bbox=self.source.getchannel('A').getbbox()
  return self.source.crop(bbox) if bbox else self.source.copy()
 def detect_labels(self):
  item=self.crop();w,h=item.size
  backdrop=Image.new('RGBA',(w,h),(245,245,245,255));backdrop.alpha_composite(item)
  data=pytesseract.image_to_data(backdrop.convert('RGB'),output_type=Output.DICT,config='--psm 11')
  labels=[]
  for k,text in enumerate(data['text']):
   text=text.strip()
   try:conf=float(data['conf'][k])/100
   except (ValueError,TypeError):continue
   if conf<.52 or len(re.sub(r'\W+','',text))<2:continue
   x,y,bw,bh=(int(data[key][k]) for key in ('left','top','width','height'))
   if bw<2 or bh<3:continue
   important=(re.sub(r'[^a-z0-9]','',text.lower()) in KEYWORDS or bw/w>.4)
   p=max(2,round(min(w,h)*.012))
   rx=max(0,x-p);ry=max(0,y-p)
   labels.append(Label(rx/w,ry/h,(min(w,x+bw+p)-rx)/w,(min(h,y+bh+p)-ry)/h,conf,text,'critical' if important else 'standard'))
  self.labels=labels
  return labels
 def safe_box(self):
  # Unknown printed regions -> conservative front-center default, explicitly not OCR-certified.
  return {'x':.18,'y':.24,'w':.64,'h':.58,'source':'fallback-unverified'}
 def hash_unchanged(self):return self.source_hash==hashlib.sha256(self.path.read_bytes()).hexdigest()
