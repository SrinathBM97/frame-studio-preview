"""FRAME ratio evidence: never turn source pixels or mL into verified product height."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re
from pathlib import Path
import fitz

FRAME_NAME='nykaa-chart/Forever52-60ml-reference'
REFERENCE = (
 # Exact matches require SKU, variant and pose. Page content is checked on startup.
 ('daily life forever52 pro artist ultra definition liquid foundation 60 ml','upright_closed',1200,7),
 ('cosrx advanced snail 96 mucin power essence 100 ml','upright_closed',1340,11),
 ('dot & key strawberry bright niacinamide face serum 30 ml','upright_closed',781,11),
 ('loreal paris infallible full wear concealer 10 ml','upright_closed',1036,6),
 ('nykaa stay all day lipstick 3.5 g','opened_with_cap',741,3),
)
ALIASES = {
 'l oreal paris infallible full wear concealer 10 ml': REFERENCE[3][0],
 'loreal paris infallible full wear 10 ml': REFERENCE[3][0],
 'dot key strawberry bright 10 niacinamide face serum 30 ml': REFERENCE[2][0],
 'dot key strawberry bright niacinamide face serum 30 ml': REFERENCE[2][0],
}
def norm(x: str) -> str:
 return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9]+',' ',(x or '').lower())).strip()

def strict_name(x: str) -> str:
 n=norm(x)
 return ALIASES.get(n,n)

@dataclass(frozen=True)
class Evidence:
 status: str
 source_type: str | None = None
 height_ref_px: int | None = None
 height_mm: float | None = None
 pose: str | None = None
 sku: str | None = None
 page: int | None = None
 url: str | None = None
 reference_frame: str | None = None
 warning: str | None = None
 def to_dict(self): return asdict(self)

class NykaaCatalog:
 def __init__(self,pdf:Path):
  if not pdf.exists():raise FileNotFoundError(pdf)
  self.pdf=pdf
  with fitz.open(pdf) as doc:
   self.pages=[p.get_text().lower() for p in doc]
  for sku,pose,height,page in REFERENCE:
   if page>len(self.pages) or not re.search(r'\b'+str(height)+r'\s+pixels\b',self.pages[page-1]):
    raise ValueError(f'Unsupported chart mapping: {sku}, page {page}, {height}')
 def lookup(self,sku:str,pose:str):
  for name,p,h,page in REFERENCE:
   if strict_name(sku)==strict_name(name) and p==pose:
    return Evidence(status='pdf_exact',source_type='nykaa_pdf',height_ref_px=h,pose=p,sku=name,page=page,reference_frame=FRAME_NAME)
  return Evidence(status='unknown',warning='Exact SKU+pose not present in checked Nykaa catalog')

def validate_online_dimension(candidate:dict,sku:str,pose:str)->Evidence:
 """Only accept physical *product* height from verifiable source; package ml/weight cannot substitute."""
 try: h=float(candidate.get('height_mm'))
 except (TypeError,ValueError):h=0
 url=candidate.get('url','')
 if not (5<=h<=1000 and url.startswith('https://') and candidate.get('dimension_type')=='product'
         and strict_name(candidate.get('sku',''))==strict_name(sku) and candidate.get('pose')==pose):
  return Evidence(status='unknown',warning='Online listing lacks verified same-SKU physical height/pose')
 return Evidence(status='online_verified',source_type='physical_measurement',height_mm=h,sku=sku,pose=pose,url=url)

def resolve_scale(items:list[dict]):
 """Generate draft heights and hard warnings; NEVER mix reference px and mm without same-SKU bridge."""
 ref=[i for i in items if i['evidence'].get('height_ref_px')]
 mm=[i for i in items if i['evidence'].get('height_mm')]
 bridge=next((i for i in items if i['evidence'].get('height_ref_px') and i['evidence'].get('height_mm')),None)
 if ref and mm and not bridge:
  incompatible=True
 else:incompatible=False
 factor=(bridge['evidence']['height_ref_px']/bridge['evidence']['height_mm']) if bridge else 1.0
 result={};warnings=[]
 for item in items:
  ev=item['evidence'];i=item['id']
  if ev.get('height_ref_px'):
   v=ev['height_ref_px'];verified=True
  elif ev.get('height_mm') and not incompatible:
   v=ev['height_mm']*factor;verified=True
  else:
   v=float(item.get('draft_height',item.get('image_height',0)))
   verified=False
   warnings.append({'id':i,'warning':'Draft size only; dimensions are not verified and final export is blocked'})
  result[i]={'height':float(v),'verified':verified,'status':ev.get('status','unknown')}
 if incompatible:warnings.append({'warning':'Incompatible physical and chart units: same-SKU calibration is required'})
 return result,warnings,all(x['verified'] for x in result.values()) and not incompatible
