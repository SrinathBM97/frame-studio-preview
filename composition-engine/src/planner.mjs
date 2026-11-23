import {EVIDENCE,validateScaleEvidence} from './evidence.mjs';

// Pure computation: no DOM, no generative alteration of products, no network.
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const GRID=48;
const DIRECTIONS = [
  {id:'sculpted-depth',name:'Sculpted Depth',hero:0.43,side:-1,wide:0.73,accent:0.65,ground:0.79},
  {id:'editorial-diagonal',name:'Editorial Diagonal',hero:0.61,side:1,wide:0.31,accent:0.49,ground:0.79},
  {id:'asymmetric-balance',name:'Asymmetric Balance',hero:0.42,side:1,wide:0.66,accent:0.54,ground:0.77},
];
export const COMPOSITION_DIRECTIONS=DIRECTIONS.map(d=>({id:d.id,name:d.name}));
function hash(n){let x=(n^0x9e3779b9)>>>0;x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296}
const pxMask=(p,u,v)=>{
  const m=p.maskGrid;
  if(!m||m.length!==GRID*GRID)return (u>=0&&u<=1&&v>=0&&v<=1)?255:0;
  if(u<0||v<0||u>=1||v>=1)return 0;
  return m[clamp(Math.floor(v*GRID),0,GRID-1)*GRID+clamp(Math.floor(u*GRID),0,GRID-1)];
};
function fromWorld(x,y,l){
  const r=-(l.rotation||0)*Math.PI/180,c=Math.cos(r),s=Math.sin(r),cy=l.top+l.h/2;
  const dx=x-l.x,dy=y-cy;
  const ux=dx*c-dy*s+l.w/2,uy=dx*s+dy*c+l.h/2;
  return {u:ux/l.w,v:uy/l.h};
}
function toWorld(u,v,l){
  const r=(l.rotation||0)*Math.PI/180,c=Math.cos(r),s=Math.sin(r);
  const dx=(u-.5)*l.w,dy=(v-.5)*l.h;
  return {x:l.x+dx*c-dy*s,y:l.top+l.h/2+dx*s+dy*c};
}
function pointInLayer(x,y,layer,p){const uv=fromWorld(x,y,layer);return pxMask(p,uv.u,uv.v)>128}
function roleMap(products){
  const sorted=[...products].sort((a,b)=>{
    const pri=p=>p.role==='hero'?5:p.role==='wide'?4:p.role==='accent'?2:3;
    return pri(b)-pri(a);
  });
  const hero=sorted.find(p=>p.role==='hero')||sorted[0];
  const wide=sorted.find(p=>p.role==='wide'&&p.id!==hero.id)||[...sorted].filter(x=>x.id!==hero.id).sort((a,b)=>(b.width/b.height)-(a.width/a.height))[0];
  const accent=sorted.find(p=>p.role==='accent'&&p.id!==hero.id&&p.id!==wide?.id)||[...sorted].filter(x=>x.id!==hero.id&&x.id!==wide?.id).sort((a,b)=>a.height-b.height)[0];
  const other=sorted.filter(x=>![hero?.id,wide?.id,accent?.id].includes(x.id));
  return {hero,wide,accent,other};
}
function pickHeight(p,anchorMm,anchorRef,anchorPx){
  const e=p.evidence||{};
  if(e.referenceHeightPx>0&&e.referenceFrame===anchorRef)return e.referenceHeightPx*anchorPx;
  if(e.heightMm>0&&anchorMm>0)return e.heightMm/anchorMm*anchorPx;
  // Source-pixel fallback is for DIAGNOSTIC DRAFTS ONLY, labelled unknown/estimated.
  return (p.estimatedReferenceHeightPx||p.height)*anchorPx;
}
function generateLayers(products,design,trial,seed,canvas,scaleBasis){
  const roles=roleMap(products),C=canvas.width,ground=canvas.height*design.ground;
  const anchors={};const jitter=(i,s)=> (hash((seed*101+trial*997+i*1249)>>>0)-.5)*s;
  const hRef=Math.max(...products.map(p=>scaleBasis.heights.get(p.id).value));
  const scale=canvas.height*.62/hRef; // one shared multiplier for each same-evidence-class product
  const margin=C*.1;
  const wide=roles.wide,hero=roles.hero,accent=roles.accent;
  // Space is deliberately reserved for the focal subject and printed information.
  if(wide)anchors[wide.id]={x:C*design.wide,foot:ground-C*.125,z:0,rotation:0};
  if(hero)anchors[hero.id]={x:C*design.hero,foot:ground-C*.006,z:2,rotation:0};
  if(accent)anchors[accent.id]={x:C*design.accent,foot:ground+C*.05,z:3,rotation:design.id==='sculpted-depth'?-5:design.id==='editorial-diagonal'?6:-7};
  roles.other.forEach((p,i)=>{anchors[p.id]={x:C*(design.hero+(.20*design.side)*(i+1)),foot:ground+C*.012,z:1+i,rotation:design.id==='editorial-diagonal'?-6:design.id==='asymmetric-balance'?4:3};});
  if(design.id==='editorial-diagonal'){
    if(wide)anchors[wide.id].foot-=C*.035;
    if(accent)anchors[accent.id].foot+=C*.006;
  }
  if(design.id==='asymmetric-balance'){
    if(wide)anchors[wide.id].x+=C*.035;
    if(hero)anchors[hero.id].x-=C*.035;
  }
  const layers=products.map((p,i)=>{
    const a=anchors[p.id];
    if(!a)throw new Error('Planner role assignment omitted '+p.id);
    // IMPORTANT: no individual scaling to solve bad layouts. One evidence-compatible scale.
    const s=scaleBasis.heights.get(p.id).value*scale;
    const h=s,w=h*p.width/p.height;
    const actualFoot=a.foot+jitter(i+11,C*.023);
    return {id:p.id, x:clamp(a.x+jitter(i+1,C*.052),margin+w/2,C-margin-w/2),
      top:actualFoot-h,w,h,z:a.z,foot:actualFoot,rotation:a.rotation||0,scaleEvidence:p.evidence?.status||EVIDENCE.UNKNOWN};
  });
  return layers.sort((a,b)=>a.z-b.z);
}

/** Sample actual silhouette and ANNOTATED label rects; central heuristic is never called OCR. */
export function assessScene(layers,products,{width=2000,height=2000}={}){
  const lookup=new Map(products.map(p=>[p.id,p]));
  const margins={left:width*.065,right:width*.935,top:height*.07,bottom:height*.91};
  let hard=0,penalty=0;
  const diagnostics=[];
  for(const l of layers){
    const p=lookup.get(l.id),L=l.x-l.w/2,R=l.x+l.w/2,B=l.top+l.h;
    const corners=[toWorld(0,0,l),toWorld(1,0,l),toWorld(0,1,l),toWorld(1,1,l)];
    const outer={L:Math.min(...corners.map(x=>x.x)),R:Math.max(...corners.map(x=>x.x)),T:Math.min(...corners.map(x=>x.y)),B:Math.max(...corners.map(x=>x.y))};
    if(outer.L<margins.left||outer.R>margins.right||outer.T<margins.top||outer.B>margins.bottom){
      hard++;diagnostics.push({id:l.id,type:'clipping',bounds:[L,l.top,R,B]});
      penalty+=3000;
    }
    let hiddenBody=0,bodyCount=0;
    const front=layers.filter(k=>k.z>l.z), samples=20;
    for(let iy=0;iy<samples;iy++)for(let ix=0;ix<samples;ix++){
      const u=(ix+.5)/samples,v=(iy+.5)/samples;
      if(pxMask(p,u,v)<=128)continue;
      const world=toWorld(u,v,l),X=world.x,Y=world.y;
      bodyCount++;
      if(front.some(k=>pointInLayer(X,Y,k,lookup.get(k.id))))hiddenBody++;
    }
    const bodyCover=hiddenBody/Math.max(bodyCount,1);
    const labels=(p.labels||[]).filter(x=>x.confirmed);
    let labelCount=0,labelHidden=0;
    for(const rect of labels){
      for(let iy=0;iy<12;iy++)for(let ix=0;ix<18;ix++){
        const u=rect.x+(ix+.5)/18*rect.w,v=rect.y+(iy+.5)/12*rect.h;
        if(pxMask(p,u,v)<=128)continue;
        labelCount++;
        const world=toWorld(u,v,l),X=world.x,Y=world.y;
        if(front.some(k=>pointInLayer(X,Y,k,lookup.get(k.id))))labelHidden++;
      }
    }
    const labelCover=labelHidden/Math.max(1,labelCount);
    if(labelCover>.02 && labels.length){hard++;diagnostics.push({id:l.id,type:'printed-label-obscured',fraction:labelCover});penalty+=1500+labelCover*3500}
    if(!labels.length)diagnostics.push({id:l.id,type:'label-evidence-missing',meaning:'needs OCR or annotated QA'});
    if(bodyCover>.38){hard++;diagnostics.push({id:l.id,type:'product-hidden',fraction:bodyCover});penalty+=900}
    penalty+=bodyCover*140;
    // Geometric grounding: feet don't imply a physical plane in transparent compositions.
    if(Math.abs(B-l.foot)>1)penalty+=500;
  }
  let contactPairs=0;
  for(let i=0;i<layers.length;i++)for(let j=i+1;j<layers.length;j++){
    const a=layers[i],b=layers[j];
    const ix=Math.max(0,Math.min(a.x+a.w/2,b.x+b.w/2)-Math.max(a.x-a.w/2,b.x-b.w/2));
    const iy=Math.max(0,Math.min(a.top+a.h,b.top+b.h)-Math.max(a.top,b.top));
    if(ix>0&&iy>0)contactPairs++;
  }
  // Balance of occupied visual mass vs canvas; a weak proxy, never creative approval.
  const weighted=layers.reduce((s,l)=>s+l.x*l.w*l.h,0)/Math.max(1,layers.reduce((s,l)=>s+l.w*l.h,0));
  const centerPenalty=Math.abs(weighted-width*.5)/width*165;
  penalty+=centerPenalty+(contactPairs===0?160:0);
  return {validGeometry:hard===0,hardFailures:hard,score:-penalty,diagnostics,metrics:{contactPairs,balanceOffset:(weighted-width*.5)/width}};
}

export function planCompositions(products,{width=2000,height=2000,seed=17,trials=32}={}){
  const inputQA=validateScaleEvidence(products);
  const canvas={width,height};
  const options=DIRECTIONS.map((style,i)=>{
    const trialsFound=[];
    for(let n=0;n<trials;n++){
      const layers=generateLayers(products,style,n,seed+i*997,canvas,inputQA.basis);
      const qa=assessScene(layers,products,canvas);
      trialsFound.push({layers,qa});
    }
    trialsFound.sort((a,b)=>(a.qa.hardFailures-b.qa.hardFailures)||(b.qa.score-a.qa.score));
    const chosen=trialsFound[0];
    return {direction:style.id,title:style.name,layers:chosen.layers,qa:chosen.qa,
      approval:chosen.qa.hardFailures>0?'blocked_by_geometry_or_labels':'human_art_director_required',scaleVerified:inputQA.scaleVerified,scaleWarnings:inputQA.warnings};
  });
  return {schema:'frame-composition-architecture/3',canvas,options,warnings:inputQA.warnings,
    approval:'NOT_PRODUCTION_APPROVED',
    notes:['No product colors/labels regenerated','Label regions need OCR or human annotation','Unverified dimensions remain unverified']};
}
