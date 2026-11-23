"""FRAME Core research backend. Exposes real upload / evidence / compose / export actions.
Not a release-ready segmentation service: approved alpha cutouts are prerequisite.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4
import io, json, os
from fastapi import FastAPI,File,UploadFile,HTTPException,Query
from fastapi.responses import Response
from PIL import Image,UnidentifiedImageError
import fitz
from .assets import ProductImage
from .evidence import NykaaCatalog
from .planner import plan
from .shadows import render,ShadowControls
from .creative_qc import judge_draft
from .pdf_index import index_chart
from .quality_gate import assess

app=FastAPI(title='FRAME Professional Core — Integrated Research API',version='0.7-integration')
ROOT=Path(os.getenv('FRAME_DATA_DIR','/tmp/frame_core_projects'))
ROOT.mkdir(parents=True,exist_ok=True)
CHART=Path(os.getenv('FRAME_NYKAA_PDF','/nonexistent/reference.pdf'))
CATALOG=NykaaCatalog(CHART) if CHART.exists() else None
sessions={}

def get_session(pid):
 if pid not in sessions:
  record=ROOT/pid/'project.json'
  if not record.exists():raise HTTPException(404,'Unknown project')
  data=json.loads(record.read_text())
  rebuilt={'id':data['id'],'name':data['name'],'products':{},'plan':json.loads((ROOT/pid/'plan.json').read_text()) if (ROOT/pid/'plan.json').is_file() else None,'guidelines':data.get('guidelines')}
  for old in data['products']:
   image_file=ROOT/pid/old['source_file']
   if not image_file.exists():raise HTTPException(500,'Project source missing')
   product=ProductImage(image_file)
   mask_file=old.get('mask_file')
   if mask_file:
    product.set_mask(Image.open(ROOT/pid/mask_file))
   product.detect_labels()
   if old['mask_status']=='approved_by_reviewer':product.approve_mask()
   rebuilt['products'][old['id']]={'id':old['id'],'sku':old['sku'],'pose':old['pose'],
      'role':old['role'],'asset':product,'evidence':old['evidence'],'path':str(image_file),'mask_file':mask_file}
  sessions[pid]=rebuilt
 return sessions[pid]

def project_public(p):
 return {'id':p['id'],'name':p['name'],'product_count':len(p['products']),
         'products':[{'id':v['id'],'sku':v['sku'],'pose':v['pose'],'role':v['role'],
                      'source_sha256':v['asset'].source_hash,'mask_status':v['asset'].mask_status,
                      'labels_detected':len(v['asset'].labels),'evidence':v['evidence']} for v in p['products'].values()],
         'has_plan':bool(p.get('plan')),'has_guidelines':bool(p.get('guidelines'))}

def persist(p):
 data=project_public(p);data['guidelines']=p.get('guidelines')
 for original,current in zip(data['products'],p['products'].values()):
  original['source_file']=Path(current['path']).name
  original['mask_file']=current.get('mask_file')
 # Persist each accepted plan separately: source images and masks remain independent.
 project_dir=ROOT/p['id']
 (project_dir/'project.json').write_text(json.dumps(data,indent=2))
 plan_file=project_dir/'plan.json'
 if p.get('plan') is None:plan_file.unlink(missing_ok=True)
 else:plan_file.write_text(json.dumps(p['plan'],indent=2))

@app.get('/health')
def health():return {'api':'frame-core','status':'research','online_research':'adapter_not_connected','automatic_cutout':'not_approved',
                           'nykaa_pdf_loaded':CATALOG is not None}

@app.get('/reference/index')
def reference_index():
 if not CHART.exists():raise HTTPException(503,'Nykaa PDF not configured')
 return index_chart(CHART)

@app.post('/projects')
def create_project(name:str='Untitled'):
 pid=uuid4().hex[:14];(ROOT/pid).mkdir()
 p={'id':pid,'name':name,'products':{},'plan':None,'guidelines':None};sessions[pid]=p;persist(p)
 return project_public(p)

@app.get('/projects/{pid}')
def get_project(pid:str):return project_public(get_session(pid))

@app.post('/projects/{pid}/products')
async def add_product(pid:str,file:UploadFile=File(...),sku:str=Query(...),pose:str='upright_closed',role:str|None=None):
 p=get_session(pid)
 if len(p['products'])>=4:raise HTTPException(409,'FRAME accepts at most four products')
 if role not in (None,'hero','wide','secondary','accent'):raise HTTPException(422,'Invalid role')
 if not file.filename.lower().endswith(('.png','.jpg','.jpeg','.webp','.avif')):raise HTTPException(415,'Unsupported input file')
 data=await file.read(20*1024*1024+1)
 if len(data)>20*1024*1024:raise HTTPException(413,'Input exceeds 20 MB')
 idx=uuid4().hex[:10];path=ROOT/pid/f'{idx}_{Path(file.filename).name}'
 path.write_bytes(data)
 try:product=ProductImage(path)
 except (UnidentifiedImageError,OSError,ValueError) as ex:
  path.unlink(missing_ok=True);raise HTTPException(422,f'Invalid image: {ex}')
 product.detect_labels()
 ev=CATALOG.lookup(sku,pose).to_dict() if CATALOG else {'status':'unknown','warning':'Reference PDF is not configured'}
 p['products'][idx]={'id':idx,'sku':sku,'pose':pose,'role':role,'asset':product,'evidence':ev,'path':str(path),'mask_file':None}
 p['plan']=None;persist(p)
 return project_public(p)['products'][-1]

@app.post('/projects/{pid}/products/{product_id}/mask')
async def update_mask(pid:str,product_id:str,file:UploadFile=File(...)):
 p=get_session(pid);item=p['products'].get(product_id)
 if not item:raise HTTPException(404,'Unknown product')
 data=await file.read(20*1024*1024+1)
 try:mask=Image.open(io.BytesIO(data))
 except (UnidentifiedImageError,OSError):raise HTTPException(422,'Invalid mask')
 try:item['asset'].set_mask(mask)
 except ValueError as e:raise HTTPException(422,str(e))
 item['asset'].detect_labels();p['plan']=None
 mask_path=ROOT/pid/f'{product_id}_mask.png'
 item['asset'].source.getchannel('A').save(mask_path)
 item['mask_file']=mask_path.name
 persist(p)
 return {'mask_status':item['asset'].mask_status,'alpha_unchanged_original_source':item['asset'].hash_unchanged()}

@app.post('/projects/{pid}/products/{product_id}/approve-mask')
def approve_mask(pid:str,product_id:str):
 p=get_session(pid);item=p['products'].get(product_id)
 if not item:raise HTTPException(404,'Unknown product')
 try:item['asset'].approve_mask()
 except ValueError as e:raise HTTPException(422,str(e))
 persist(p);return {'status':item['asset'].mask_status,'source_sha256_unchanged':item['asset'].hash_unchanged()}

@app.post('/projects/{pid}/brand-guidelines')
async def brand_guidelines(pid:str,file:UploadFile=File(...)):
 p=get_session(pid)
 data=await file.read(16*1024*1024+1)
 if len(data)>16*1024*1024:raise HTTPException(413,'Brand PDF too large')
 try:
  with fitz.open(stream=data,filetype='pdf') as pdf:text=' '.join(page.get_text() for page in pdf)
 except Exception:raise HTTPException(422,'Unable to read PDF')
 import re
 hexes=list(dict.fromkeys(re.findall(r'#[A-Fa-f0-9]{6}\b',text)))
 record={'pages_read':len(fitz.open(stream=data,filetype='pdf')),'hex_colors_found':hexes,
         'text_available':bool(text.strip()),'compliance':'manual_review_required',
         'limitations':'Extracted colors are not proof of full brand-guideline compliance'}
 p['guidelines']=record;persist(p);return record

@app.get('/projects/{pid}/quality')
def project_quality(pid:str):
 return assess(get_session(pid))

@app.post('/projects/{pid}/compose')
def compose(pid:str,seed:int=17):
 p=get_session(pid);products=list(p['products'].values())
 if len(products)<3 or len(products)>4:raise HTTPException(409,'Upload 3 or 4 products')
 if not all(x['asset'].mask_approved for x in products):
  raise HTTPException(409,'Cutout approval gate: one or more masks require review')
 items=[]
 for i,x in enumerate(products):
  a=x['asset'];im=a.crop()
  labels=[v.to_dict() for v in a.labels]
  items.append({'id':x['id'],'name':x['sku'],'image':a,'size':im.size,
                'draft_height':{'hero':1300,'secondary':1080,'wide':1020,'accent':760}.get(x['role'],1000),
                'role':x['role'],'evidence':x['evidence'],'labels':labels})
 answer=plan(items,seed=seed)
 for draft in answer['directions']:
  draft['creative_qc']=judge_draft(draft)
 p['plan']=answer;persist(p)
 return {**answer,'notes':['Candidate rankings are geometric and OCR-based, not a substitute for human art-direction approval']}

@app.get('/projects/{pid}/preview/{option}')
def preview(pid:str,option:int,shadows:bool=True,ground:str='#2C003B',overlap:str='#000000',
            contact_opacity:float=Query(.42,ge=0,le=1),overlap_opacity:float=Query(.34,ge=0,le=1),
            ambient_blur:int=Query(36,ge=0,le=90)):

 p=get_session(pid)
 if not p.get('plan'):raise HTTPException(409,'Create composition first')
 if option<0 or option>=3:raise HTTPException(404,'Unknown option')
 selected=p['plan']['directions'][option]
 if not selected['qa']['pass']:raise HTTPException(409,'Layout failed safety gate')
 images={i:x['asset'] for i,x in p['products'].items()}
 try:im=render(selected['layers'],images,settings=ShadowControls(ground_color=ground,overlap_color=overlap,contact_opacity=contact_opacity,overlap_opacity=overlap_opacity,ambient_blur=ambient_blur),shadows=shadows)
 except (ValueError,KeyError,OSError) as e:raise HTTPException(422,f'Render failed: {e}')
 out=io.BytesIO();im.save(out,format='PNG')
 return Response(out.getvalue(),media_type='image/png',headers={'X-FRAME-RESEARCH-ONLY':'1','X-FRAME-RATIO-VERIFIED':str(bool(p['plan']['ratio_verified'])).lower()})

@app.get('/projects/{pid}/export/{option}')
def final_export(pid:str,option:int):
 p=get_session(pid)
 if not p.get('plan'):raise HTTPException(409,'No composition')
 if not p['plan']['ratio_verified']:raise HTTPException(409,'Product height evidence unverified; final export blocked')
 raise HTTPException(409,'Final export requires independent visual/creative approval; not available in research backend')
