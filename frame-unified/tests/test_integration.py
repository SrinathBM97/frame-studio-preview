"""Real HTTP-level tests for unified editor + Python API; synthetic assets only."""
import hashlib
import io
from pathlib import Path
import fitz
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from frame_core.server import app
import frame_core.api as core


def png(size=(160,360), color=(110,40,165,255), no_alpha=False):
    image=Image.new('RGBA',size, (25, 75, 118,255) if no_alpha else (0,0,0,0))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((18, 20, size[0]-18,size[1]-12),radius=12,fill=color)
    buffer=io.BytesIO();image.save(buffer,format='PNG');return buffer.getvalue()


def alpha_png(size=(160,360), fg=(20,20,130,255)):
    source=png(size,fg)
    im=Image.open(io.BytesIO(source)).convert('RGBA')
    # Intentionally misleading RGB values in transparent regions: alpha is authoritative.
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()


def test_unified_frontend_and_routes():
    c=TestClient(app)
    ui=c.get('/')
    assert ui.status_code==200
    assert b'screen-compose' in ui.content and b'screen-guidelines' in ui.content
    assert b'/core-bridge.js' in ui.content
    js=c.get('/core-bridge.js')
    assert js.status_code==200
    assert b'Generate with professional core' in js.content
    health=c.get('/api/health')
    assert health.status_code==200
    assert health.json()['automatic_cutout']=='not_approved'


def test_persisted_plan_and_non_destructive_alpha_mask(monkeypatch,tmp_path):
    monkeypatch.setattr(core,'ROOT',tmp_path)
    monkeypatch.setattr(core,'CATALOG',None)
    core.sessions.clear()
    c=TestClient(app)
    response=c.post('/api/projects',params={'name':'Integration'},timeout=45)
    assert response.status_code==200
    pid=response.json()['id'];source_hashes=[]
    case=[('hero',(150,380),'hero'),('wide',(260,250),'wide'),('accent',(100,280),'accent')]
    for index,(name,size,role) in enumerate(case):
        raw=png(size, no_alpha=True)
        sha=hashlib.sha256(raw).hexdigest()
        up=c.post(f'/api/projects/{pid}/products',params={'sku':name,'role':role},files={'file':(f'{name}.png',raw,'image/png')},timeout=45)
        assert up.status_code==200,up.text
        data=up.json();assert data['source_sha256']==sha
        source_hashes.append(sha)
        alpha=alpha_png(size)
        revised=c.post(f'/api/projects/{pid}/products/{data["id"]}/mask',files={'file':('alpha.png',alpha,'image/png')})
        assert revised.status_code==200,revised.text
        approved=c.post(f'/api/projects/{pid}/products/{data["id"]}/approve-mask')
        assert approved.status_code==200,approved.text
        assert approved.json()['source_sha256_unchanged'] is True
        saved_mask=Image.open(tmp_path/pid/f'{data["id"]}_mask.png')
        assert saved_mask.getpixel((0,0))==0
        assert saved_mask.getpixel((size[0]//2,size[1]//2))==255
    before=c.get(f'/api/projects/{pid}').json()
    assert [p['source_sha256'] for p in before['products']]==source_hashes
    comp=c.post(f'/api/projects/{pid}/compose',params={'seed':23},timeout=120)
    assert comp.status_code==200,comp.text[:600]
    data=comp.json();assert len(data['directions'])==3 and data['ratio_verified'] is False
    assert (tmp_path/pid/'plan.json').is_file()
    core.sessions.clear()
    after=c.get(f'/api/projects/{pid}').json()
    assert after['has_plan'] is True
    assert [p['source_sha256'] for p in after['products']]==source_hashes
    for p in after['products']:
        assert p['mask_status']=='approved_by_reviewer'
    for index,d in enumerate(data['directions']):
        r=c.get(f'/api/projects/{pid}/preview/{index}',timeout=120)
        if d['qa']['pass']:
            assert r.status_code==200,r.text[:150] if r.status_code!=200 else ''
            im=Image.open(io.BytesIO(r.content));assert im.size==(2000,2000) and im.mode=='RGBA'
            break
        assert r.status_code==409
    assert c.get(f'/api/projects/{pid}/export/0').status_code==409
    for sha in source_hashes:
        assert sha in [hashlib.sha256(f.read_bytes()).hexdigest() for f in (tmp_path/pid).glob('*_*.png')]


def test_brand_pdf_has_no_false_certification(monkeypatch,tmp_path):
    monkeypatch.setattr(core,'ROOT',tmp_path)
    core.sessions.clear()
    c=TestClient(app)
    pid=c.post('/api/projects').json()['id']
    doc=fitz.open();page=doc.new_page();page.insert_text((40,40),'Brand palette #123456 and do not change packaging')
    pdf=doc.tobytes();doc.close()
    response=c.post(f'/api/projects/{pid}/brand-guidelines',files={'file':('brand.pdf',pdf,'application/pdf')})
    assert response.status_code==200
    info=response.json();assert '#123456' in info['hex_colors_found']
    assert info['compliance']=='manual_review_required'
