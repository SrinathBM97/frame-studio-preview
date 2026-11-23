/* FRAME integrated dev client: existing browser editor remains intact.
 * This adapter only submits user-approved cutout masks to the same-origin Python
 * core; it does not pretend a standalone Pages preview can execute Python.
 */
(() => {
  'use strict';
  const host = document.getElementById('screen-compose');
  if (!host) return;
  const section = document.createElement('section');
  section.className = 'panel';
  section.id = 'coreIntegration';
  section.style.gridColumn = '1 / -1';
  section.innerHTML = `
    <div class="section"><div><h2>Professional Core · development connection</h2>
      <div class="sub">Same FRAME workspace, one Python composition engine. Existing browser compositions remain available.</div></div>
      <span id="coreConnection" class="sub" role="status">Checking engine…</span></div>
    <div class="note">Research-only: clicking Generate sends a copy of the original packshots and alpha masks to the development backend. Do not use confidential client assets until authentication is implemented. Source files stay unchanged. Final export remains blocked pending QC.</div>
    <div class="controls" style="margin:12px 0">
      <button id="coreGenerate" class="primary small" type="button" disabled>Generate with professional core</button>
      <button id="coreRefresh" class="small" type="button">Check connection</button>
      <span id="coreProgress" class="sub" role="status"></span>
    </div>
    <div id="coreResults" class="cardgrid" style="grid-template-columns:repeat(auto-fit,minmax(220px,1fr))"></div>`;
  host.appendChild(section);
  const $ = id => document.getElementById(id);
  let enabled = false, running = false, projectId = null;
  const show = msg => { $('coreProgress').textContent = msg; };
  async function request(path, options={}) {
    const r = await fetch('/api' + path, { ...options, cache:'no-store' });
    if (!r.ok) {
      let msg = 'HTTP ' + r.status;
      try { const j=await r.json(); msg = j.detail || msg; } catch {}
      throw new Error(typeof msg==='string' ? msg : JSON.stringify(msg));
    }
    return r;
  }
  async function connection() {
    try {
      const r=await request('/health'); const data=await r.json();
      enabled=data.api==='frame-core';
      $('coreConnection').textContent=enabled?'● Core connected · research':'Core API not recognized';
      show(enabled?'Ready for approved cutouts.':'Backend is not available.');
    } catch(e) {
      enabled=false;
      $('coreConnection').textContent='○ Browser-only site';
      show('Python core is not hosted here. Existing browser tools remain available.');
    }
    $('coreGenerate').disabled=!enabled;
  }
  async function canvasPng(canvas) {
    return new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('PNG encoding failed')),'image/png'));
  }
  async function mattePng(cutout) {
    const c=document.createElement('canvas');c.width=cutout.width;c.height=cutout.height;
    const source=cutout.getContext('2d',{willReadFrequently:true}).getImageData(0,0,c.width,c.height);
    const pixels=source.data;
    // Explicitly encode the alpha as grayscale to prevent RGB/alpha ambiguity on server.
    for(let p=0;p<pixels.length;p+=4){const a=pixels[p+3];pixels[p]=pixels[p+1]=pixels[p+2]=a;pixels[p+3]=255;}
    c.getContext('2d').putImageData(source,0,0);
    return canvasPng(c);
  }
  async function generate() {
    if(running||!enabled)return;
    if(typeof state==='undefined'||!Array.isArray(state.items)||![3,4].includes(state.items.length)){
      show('Please upload 3–4 products first.'); return;
    }
    if(!state.items.every(x=>x.approved)){
      show('Approve every cutout in Source assets before generating.'); return;
    }
    running=true;$('coreGenerate').disabled=true;$('coreResults').replaceChildren();
    try {
      const created=await (await request('/projects?name=FRAME%20Studio%20Research',{method:'POST'})).json();
      projectId=created.id;
      for(let i=0;i<state.items.length;i++){
        const item=state.items[i];show(`Syncing approved product ${i+1}/${state.items.length}…`);
        const original=await fetch(item.source).then(r=>r.blob());
        const fd=new FormData(); fd.append('file', original, item.filename || `product_${i+1}.png`);
        const name=(item.name || item.filename || `Product ${i+1}`).trim();
        // Let the planner infer roles from product silhouettes; do not force a wide role.
        // Exact PDF matches also require correct pose (an opened lipstick is not a closed one).
        const q=new URLSearchParams({sku:name,pose:'upright_closed'});
        const uploaded=await (await request(`/projects/${projectId}/products?${q}`,{method:'POST',body:fd})).json();
        const maskForm=new FormData();maskForm.append('file',await mattePng(item.mask),`${i+1}_alpha.png`);
        await request(`/projects/${projectId}/products/${uploaded.id}/mask`,{method:'POST',body:maskForm});
        await request(`/projects/${projectId}/products/${uploaded.id}/approve-mask`,{method:'POST'});
      }
      show('Generating 3 evidence-aware layouts…');
      const result=await (await request(`/projects/${projectId}/compose?seed=${state.seed||17}`,{method:'POST'})).json();
      const grid=$('coreResults');
      result.directions.forEach((option,i)=>{
        const card=document.createElement('div');card.className='panel';card.style.padding='10px';
        const head=document.createElement('strong');head.textContent=(i+1)+'. '+option.style.replaceAll('_',' ');card.appendChild(head);
        const note=document.createElement('div');note.className='sub';
        const approved=option.qa.pass && option.creative_qc.creative_approved;
        note.textContent=(option.qa.pass?'Geometry safe':'Geometry rejected')+' · '+(approved?'Creative approved':'Creative unapproved')+' · '+(result.ratio_verified?'Ratios verified':'Ratios unverified');card.appendChild(note);
        if(option.qa.pass){
          const img=document.createElement('img');
          img.alt='FRAME research draft '+(i+1);img.loading='lazy';
          img.style.cssText='width:100%;height:auto;aspect-ratio:1;object-fit:contain;background-color:#dedee4;background-image:linear-gradient(45deg,#bcbec5 25%,transparent 25%),linear-gradient(-45deg,#bcbec5 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#bcbec5 75%),linear-gradient(-45deg,transparent 75%,#bcbec5 75%);background-size:24px 24px;background-position:0 0,0 12px,12px -12px,-12px 0';
          const url=previewUrl(i);img.dataset.option=String(i);img.src=url;card.appendChild(img);
          const link=document.createElement('a');link.href=url;link.target='_blank';link.rel='noopener';link.download=`FRAME_DRAFT_${i+1}.png`;link.textContent='Open transparent research draft';card.appendChild(link);
        } else {
          const rejected=document.createElement('p');rejected.className='sub';rejected.textContent=option.qa.hard.map(x=>x.type).join(' · ');card.appendChild(rejected);
        }
        grid.appendChild(card);
      });
      const qc=await (await request(`/projects/${projectId}/quality`)).json();
      const count=qc.reasons?.length||0;
      show(`Three research options prepared · ${count} release blockers · ${qc.decision}. ${result.ratio_verified?'Ratio evidence verified.':'Unverified ratios block final export.'}`);
    } catch(e){show('Core refused: '+e.message);} finally {running=false;$('coreGenerate').disabled=!enabled;}
  }
  function previewUrl(i) {
    const params=new URLSearchParams({ground:state.ground||'#2C003B',overlap:state.overlap||'#000000',
      contact_opacity:String(Math.min(1,Math.max(0,(state.opacity??42)/100))),
      overlap_opacity:String(Math.min(1,Math.max(0,(state.overlapAmt??34)/100))),
      ambient_blur:String(Math.max(0,Math.min(90,Number(state.blur??36))))});
    return `/api/projects/${projectId}/preview/${i}?${params}`;
  }
  for(const selector of ['groundColor','overlapColor','shadowOpacity','shadowBlur','overlapAmt']) {
    const control=$(selector);
    if(control)control.addEventListener('change',()=>{
      for(const img of $('coreResults').querySelectorAll('img[data-option]')){
        const i=Number(img.dataset.option); const url=previewUrl(i);
        img.src=url;const link=img.parentNode.querySelector('a');if(link)link.href=url;
      }
    });
  }
  $('coreGenerate').addEventListener('click',generate);
  $('coreRefresh').addEventListener('click',connection);
  connection();
})();
