/** FRAME composition planner v4. Separate geometric/optical planning from user asset pixels. */
import {EVIDENCE,validateScaleEvidence} from './evidence.mjs';
import {applyReferenceToStyles} from './reference.mjs';
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const GRID=48;
const STYLE_SPECS=[
 {id:'sculpted-depth',name:'Sculpted Depth', positions:{hero:[.43,.795],wide:[.62,.738],secondary:[.25,.786],accent:[.63,.828]}, rotations:{hero:0,wide:0,secondary:-1,accent:0}, targetOverlap:.045},
 {id:'editorial-diagonal',name:'Editorial Diagonal',positions:{hero:[.71,.786],wide:[.46,.728],secondary:[.22,.79],accent:[.62,.832]},rotations:{hero:0,wide:0,secondary:0,accent:1},targetOverlap:.048},
 {id:'asymmetric-balance',name:'Asymmetric Balance',positions:{hero:[.34,.8],wide:[.52,.733],secondary:[.72,.79],accent:[.59,.831]},rotations:{hero:0,wide:0,secondary:1,accent:0},targetOverlap:.038},
];
export const COMPOSITION_DIRECTIONS=STYLE_SPECS.map(({id,name})=>({id,name}));
function seeded(n){let x=(n^0x9e3779b9)>>>0;x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296}
function val(p,u,v){if(u<0||u>=1||v<0||v>=1)return 0;const m=p.maskGrid;if(!m||m.length!==GRID*GRID)return 255;return m[Math.floor(v*GRID)*GRID+Math.floor(u*GRID)]??0}
export function localToWorld(u,v,l){const a=(l.rotation||0)*Math.PI/180,c=Math.cos(a),s=Math.sin(a);const dx=(u-.5)*l.w,dy=(v-.5)*l.h;return {x:l.x+dx*c-dy*s,y:l.top+l.h/2+dx*s+dy*c}}
export function worldToLocal(x,y,l){const a=-(l.rotation||0)*Math.PI/180,c=Math.cos(a),s=Math.sin(a),dx=x-l.x,dy=y-l.top-l.h/2;return {u:(dx*c-dy*s)/l.w+.5,v:(dx*s+dy*c)/l.h+.5}}
function maskAtWorld(p,l,x,y){const o=worldToLocal(x,y,l);return val(p,o.u,o.v)>128}
function roles(products){
 const chosen=new Set();
 const explicit=(role)=>{const p=products.find(p=>p.role===role&&!chosen.has(p.id))||null;if(p)chosen.add(p.id);return p};
 let hero=explicit('hero');
 if(!hero){hero=[...products].sort((a,b)=>b.height-a.height)[0];chosen.add(hero.id)}
 let wide=explicit('wide');
 if(!wide){wide=products.filter(p=>!chosen.has(p.id)&&(!p.role||p.role==='wide')&&p.width/p.height>.72).sort((a,b)=>b.width/b.height-a.width/a.height)[0]||null;if(wide)chosen.add(wide.id)}
 let accent=explicit('accent');
 if(!accent){accent=products.filter(p=>!chosen.has(p.id)&&(!p.role||p.role==='accent')).sort((a,b)=>a.height-b.height)[0]||null;if(accent)chosen.add(accent.id)}
 let secondary=explicit('secondary')||products.find(p=>!chosen.has(p.id))||null;
 if(secondary)chosen.add(secondary.id);
 if(!accent&&products.length===3){accent=secondary;secondary=null}
 return {hero,wide,accent,secondary};
}
/** A draft with noncomparable products is explicit and never reported as dimensionally correct. */
function makeCandidate(products,basis,style,trial,seed,canvas){
 const r=roles(products),byRole=['wide','secondary','hero','accent'];const sorted=byRole.map(role=>({role,product:r[role]})).filter(k=>k.product);const C=canvas.width,H=canvas.height;
 const maxHeight=Math.max(...products.map(p=>basis.heights.get(p.id).value));const scale=(H*.53)/maxHeight;
 const layers=[];
 for(const [i,{role,product:p}] of sorted.entries()){
   let base=style.positions[role];
   if(!r.wide){const three={hero:style.id==='editorial-diagonal'?[.61,.79]:style.id==='asymmetric-balance'?[.38,.79]:[.51,.79], secondary:style.id==='editorial-diagonal'?[.25,.81]:[.27,.80], accent:style.id==='asymmetric-balance'?[.73,.83]:[.70,.83]};base=three[role]||base}
   const random=(salt)=>seeded((seed*7919 + trial*2647 + i*1013 + salt*491)>>>0)-.5;
   const h=basis.heights.get(p.id).value*scale,w=h*p.width/p.height;
   // Jitter is search within a considered composition territory; not a random creative direction.
   const x=clamp((base[0]+random(2)*.105)*C, C*.073+w/2,C*.927-w/2);
   const foot=H*(base[1]+random(9)*.046);
   const rotation=style.rotations[role];
   layers.push({id:p.id,role,x,top:foot-h,w,h,z:i,foot,rotation,scaleEvidence:p.evidence?.status??EVIDENCE.UNKNOWN,depthPlane:role==='wide'?'rear':role==='accent'?'front':'middle',sourceRect:p.sourceRect||null});
 }
 return layers;
}
function layerAABB(l){const corners=[[0,0],[1,0],[0,1],[1,1]].map(([u,v])=>localToWorld(u,v,l));return {left:Math.min(...corners.map(x=>x.x)),right:Math.max(...corners.map(x=>x.x)),top:Math.min(...corners.map(x=>x.y)),bottom:Math.max(...corners.map(x=>x.y))}}
const containsRect=(x,y,rect)=>x>=rect.x&&x<=rect.x+rect.w&&y>=rect.y&&y<=rect.y+rect.h;
export function assessScene(layers,products,canvas={width:2000,height:2000},{style=null}={}){
 const look=new Map(products.map(p=>[p.id,p]));let penalty=0,hard=0;const diagnostics=[],visibility=[];let overlapUnits=0,coveredArea=0;
 const positions=layers.map(l=>({layer:l,rect:layerAABB(l)}));
 for(const {layer:l,rect} of positions){
   if(rect.left<canvas.width*.055||rect.right>canvas.width*.945||rect.top<canvas.height*.07||rect.bottom>canvas.height*.91){hard++;penalty+=1800;diagnostics.push({id:l.id,type:'product-out-of-safe-area',bounds:rect})}
   if(!look.has(l.id))throw new Error('Unknown product layer '+l.id);
   const p=look.get(l.id);const front=layers.filter(k=>k.z>l.z),S=38;let visible=0,total=0,hidden=0;
   let safeText=0,coveredText=0,majorText=0,majorCovered=0;
   const labels=(p.labels||[]).filter(t=>t.confirmed===true||t.source==='ocr'||t.source==='manual').filter(t=>Number.isFinite(t.x)&&Number.isFinite(t.w)&&t.w>0&&t.h>0);
   const major=labels.filter(t=>t.priority==='critical'||t.priority==='brand'||t.priority==='product');
   for(let iy=0;iy<S;iy++)for(let ix=0;ix<S;ix++){
     const u=(ix+.5)/S,v=(iy+.5)/S,alpha=val(p,u,v);
     if(alpha<128)continue;
     total++;
     const pt=localToWorld(u,v,l);
     const isHidden=front.some(k=>maskAtWorld(look.get(k.id),k,pt.x,pt.y));
     if(isHidden){hidden++;coveredArea++}else visible++;
     for(const t of labels){if(!containsRect(u,v,t))continue;safeText++;if(isHidden)coveredText++;if(t.priority==='critical'||t.priority==='brand'||t.priority==='product'){majorText++;if(isHidden)majorCovered++}}
   }
   const occlusion=hidden/Math.max(1,total),labelLoss=coveredText/Math.max(1,safeText),majorLoss=majorCovered/Math.max(1,majorText);
   const criticalLimit=major.length?.008:.013;
   if(majorLoss>criticalLimit){hard++;penalty+=6000*majorLoss+600;diagnostics.push({id:l.id,type:'key-label-obscured',fraction:majorLoss})}
   if(labelLoss>.025){hard++;penalty+=3500*labelLoss+500;diagnostics.push({id:l.id,type:'printed-label-obscured',fraction:labelLoss})}
   if(occlusion>.26){hard++;penalty+=600*occlusion+500;diagnostics.push({id:l.id,type:'product-silhouette-hidden',fraction:occlusion})}
   if(!labels.length){penalty+=15;diagnostics.push({id:l.id,type:'label-detection-missing',meaning:'automatic OCR or user annotation required'})}
   penalty+=occlusion*90;
   visibility.push({id:l.id,occlusion,labelLoss,majorLoss,visibleFraction:visible/Math.max(1,total),ocrRegions:labels.length});
   overlapUnits+=hidden;
 }
 const isCompact=(layers.some(l=>l.role==='wide')&&layers.some(l=>l.role==='accent'));
 if(overlapUnits===0&&isCompact){penalty+=125;diagnostics.push({type:'flat-no-occlusion'})}
 const wsum=layers.reduce((a,l)=>a+l.w*l.h,0), centroid=layers.reduce((a,l)=>a+l.x*l.w*l.h,0)/Math.max(1,wsum);
 const imbalance=Math.abs(centroid-canvas.width*.5)/canvas.width;
 penalty+=imbalance*265;
 // Strategic visual roles must remain distinct; large distances lose visual grouping.
 const hero=layers.find(l=>l.role==='hero'),wide=layers.find(l=>l.role==='wide'),accent=layers.find(l=>l.role==='accent');
 if(hero&&wide){const distance=Math.abs(hero.x-wide.x)/canvas.width;penalty+=Math.abs(distance-.24)*150}
 if(hero&&accent){const distance=Math.abs(hero.x-accent.x)/canvas.width;penalty+=Math.abs(distance-.18)*150}
 const widthCoverage=(Math.max(...positions.map(x=>x.rect.right))-Math.min(...positions.map(x=>x.rect.left)))/canvas.width;
 penalty+=Math.abs(widthCoverage-.68)*290;
 if(style){const rough=style.targetOverlap;const ratio=coveredArea/(layers.length*38*38);penalty+=Math.abs(ratio-rough)*700;}
 return {validGeometry:hard===0,hardFailures:hard,score:-penalty,diagnostics,metrics:{occludedGridPixels:overlapUnits,balanceOffset:(centroid-canvas.width*.5)/canvas.width,widthCoverage,labelVisibility:visibility,shadowEligible:layers.every(l=>Math.abs(l.top+l.h-l.foot)<.1)}};
}
function distinctEnough(a,b,canvas){const ids=a.layers.map(l=>l.id);let sum=0;for(const id of ids){const x=a.layers.find(l=>l.id===id),y=b.layers.find(l=>l.id===id);sum+=Math.abs(x.x-y.x)/canvas.width+Math.abs(x.foot-y.foot)/canvas.height}
 return sum/ids.length>.11 || a.direction!==b.direction&&a.layers.some(l=>b.layers.find(v=>v.id===l.id)?.z!==l.z);}
export function planCompositions(products,{width=2000,height=2000,seed=17,trials=75,referenceGuide=null}={}){
 const input=validateScaleEvidence(products),canvas={width,height};
 const options=applyReferenceToStyles(STYLE_SPECS,referenceGuide).map((style,index)=>{
   let best=null;
   for(let n=0;n<Math.max(1,trials);n++){
     const layers=makeCandidate(products,input.basis,style,n,seed+index*1009,canvas);
     const qa=assessScene(layers,products,canvas,{style});
     if(!best||qa.hardFailures<best.qa.hardFailures||qa.hardFailures===best.qa.hardFailures&&qa.score>best.qa.score)best={layers,qa};
   }
   return {direction:style.id,title:style.name,layers:best.layers,qa:best.qa,approval:best.qa.hardFailures?'blocked_by_geometry_or_labels':'human_art_director_required',scaleVerified:input.scaleVerified,scaleWarnings:input.warnings,referenceSource:style.referenceSource||null};
 });
 const tooSimilar=[];for(let i=0;i<options.length;i++)for(let j=i+1;j<options.length;j++)if(!distinctEnough(options[i],options[j],canvas))tooSimilar.push([i,j]);
 return {schema:'frame-composition-architecture/4',canvas,options,tooSimilar,warnings:input.warnings,previewEligible:options.every(o=>o.qa.hardFailures===0)&&tooSimilar.length===0,approval:'NOT_PRODUCTION_APPROVED',notes:['Original product pixels immutable','OCR source regions protected but require QA','Unknown physical dimensions prevent verified scale','Human creative QC remains mandatory']};
}
