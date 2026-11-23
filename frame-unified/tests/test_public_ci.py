"""Safe synthetic CI regressions; no private user assets or PDFs."""
from pathlib import Path
import io
from PIL import Image,ImageDraw
import numpy as np
from frame_core.evidence import resolve_scale,validate_online_dimension
from frame_core.mask_edit import MaskEditor
from frame_core.planner import plan
from frame_core.shadows import render
from frame_core.creative_qc import judge_draft
from frame_core.online import parse_height_from_product_schema

def sample(name,size,role,ref=None):
 im=Image.new('RGBA',size,(0,0,0,0))
 d=ImageDraw.Draw(im)
 d.rounded_rectangle((8,8,size[0]-8,size[1]-8),radius=10,fill={'hero':'#C33679','secondary':'#99BBDD','accent':'#EBB14B','wide':'#7E65A7'}[role])
 labels=[{'x':.26,'y':.40,'w':.46,'h':.2,'priority':'critical'}]
 class Source:
  def __init__(self,im):self.im=im
  def crop(self):return self.im
 src=Source(im)
 e={'status':'pdf_exact','height_ref_px':ref,'reference_frame':'chart-reference'} if ref else {'status':'unknown'}
 return {'id':name,'role':role,'size':size,'image':src,'labels':labels,'evidence':e,'draft_height':1000}

def test_plan_shadow_and_output_on_synthetic():
 items=[sample('hero',(100,460),'hero',1200),sample('accent',(90,240),'accent',700),sample('secondary',(140,350),'secondary'),sample('wide',(330,300),'wide')]
 result=plan(items,trials=40)
 assert len(result['directions'])==3 and not result['ratio_verified']
 for candidate in result['directions']:
  layer={x['id']:x for x in candidate['layers']}
  assert abs(layer['accent']['h']/layer['hero']['h']-700/1200)<1e-6
  assert judge_draft(candidate)['creative_approved'] is False
  if candidate['qa']['pass']:
   sources={x['id']:x['image'] for x in items}
   a=render(candidate['layers'],sources,shadows=False)
   b=render(candidate['layers'],sources,shadows=True)
   assert a.size==(2000,2000)
   assert np.any(np.asarray(a)!=np.asarray(b))
   break
 else:
  assert all(c['status']=='blocked_by_geometry' for c in result['directions'])

def test_mask_zero_and_online_safeguard():
 im=Image.new('L',(48,48),0);ImageDraw.Draw(im).rectangle((10,10,35,35),fill=255)
 editor=MaskEditor(im)
 assert editor.get().tobytes()==im.tobytes()
 editor.settings.feather_px=2
 assert editor.get().tobytes()!=im.tobytes()
 editor.reset()
 assert editor.get().tobytes()==im.tobytes()
 wrong=validate_online_dimension({'sku':'product','pose':'upright_closed','height_mm':150,'dimension_type':'shipping','url':'https://example.com'},'product','upright_closed')
 assert wrong.status=='unknown'
 schema='{"@type":"Product","name":"Example Brand Serum","height":{"value":17,"unitCode":"CMT"}}'
 match=parse_height_from_product_schema(schema,'Example Brand Serum','upright_closed','https://brand.example/serum')
 assert match.status=='online_verified' and match.height_mm==170
