"""UI bridge browser smoke, with explicitly mocked API; not an end-to-end server test.
The real API is tested separately using FastAPI TestClient.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
html=(root/'web'/'index.html').read_text().replace('<script src="/core-bridge.js" defer></script>','<script>\n'+(root/'web'/'core-bridge.js').read_text().replace('</script','<\\/script')+'\n</script>')
mock='''() => {
 window.__fetchRequests=[]; const original=window.fetch.bind(window);
 window.fetch=async (url,opts={}) => {
  const str=String(url);
  if(!str.startsWith('/api')) return original(url,opts);
  window.__fetchRequests.push({url:str,method:opts.method||'GET'});
  const reply=payload=>new Response(JSON.stringify(payload),{status:200,headers:{'content-type':'application/json'}});
  if(str==='/api/health')return reply({api:'frame-core',status:'research'});
  if(str.startsWith('/api/projects?'))return reply({id:'test-project'});
  if(str.includes('/products?'))return reply({id:'asset-'+window.__fetchRequests.length});
  if(str.endsWith('/quality'))return reply({decision:'NO_GO',reasons:['No art approval']});
  if(str.includes('/compose?'))return reply({ratio_verified:false,directions:[0,1,2].map(i=>({style:['cluster','diagonal','offset'][i],qa:{pass:false,hard:[{type:'synthetic_geometry_gate'}]},creative_qc:{creative_approved:false}}))});
  return reply({status:'ok'});
 };
}'''
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1280,'height':780})
 errs=[];page.on('pageerror',lambda e: errs.append(str(e)))
 page.goto('about:blank')
 page.evaluate(mock)
 page.set_content(html,wait_until='domcontentloaded',timeout=30000)
 page.wait_for_timeout(500)
 assert page.locator('#coreIntegration').count()==1
 assert page.locator('#coreGenerate').is_enabled()
 assert page.locator('#coreConnection').inner_text().startswith('● Core connected')
 for i,(w,h) in enumerate([(150,330),(250,220),(90,270)],1):
  from PIL import Image,ImageDraw
  from io import BytesIO
  img=Image.new('RGBA',(w,h),(0,0,0,0));ImageDraw.Draw(img).rectangle((14,12,w-15,h-15),fill=(120,45*i,155,255));b=BytesIO();img.save(b,format='PNG')
  page.locator('#uploadInput').set_input_files({'name':f'fixture_{i}.png','mimeType':'image/png','buffer':b.getvalue()})
  page.wait_for_function(f'state.items.length === {i}',timeout=12000)
 page.evaluate('''() => {state.items.forEach(i=>{i.approved=true;i.processed=true});renderProducts();renderSizes()}''')
 page.locator('[data-tab="compose"]').click()
 page.locator('#coreGenerate').click()
 page.wait_for_function("document.querySelector('#coreProgress').textContent.includes('Three research options')",timeout=30000)
 result={'rendered_cards':page.locator('#coreResults > div').count(), 'request_count':page.evaluate('window.__fetchRequests.length'), 'methods':page.evaluate('window.__fetchRequests.map(x=>x.method)'), 'page_errors':errs,'status':page.locator('#coreProgress').inner_text()}
 page.screenshot(path=str(root/'browser_mock_qa.png'),full_page=True)
 print(json.dumps(result,indent=2))
 assert result['rendered_cards']==3
 assert result['request_count']>=12
 assert not errs
 browser.close()
