/**
 * FRAME / experimental reference grammar v5.
 * A reference supplies spatial relationships, not source assets or product sizes.
 * Input boxes may originate from a human study or a future audited visual parser.
 */
export const ROLES=['hero','wide','secondary','accent'];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const isNum=x=>Number.isFinite(x);
export function compileReferenceGrammar(ref){
  if(!ref || !['human_reference_study','approved_reference','verified_visual_parser'].includes(ref.source))
    throw new Error('Reference provenance must be explicit');
  if(!ref.id || !ref.boxes || typeof ref.boxes!=='object')throw new Error('Reference requires id and role boxes');
  const anchors={},boxes={};
  for(const [role,entry] of Object.entries(ref.boxes)){
    if(!ROLES.includes(role)) throw new Error('Unknown role '+role);
    const b=entry?.bbox;
    if(!Array.isArray(b)||b.length!==4||b.some(v=>!isNum(v)||v<0||v>1)||b[2]<=0||b[3]<=0||b[0]+b[2]>1.001||b[1]+b[3]>1.001)
      throw new Error('Invalid reference geometry for '+role);
    if(!Number.isInteger(entry.z) || entry.z<0 || entry.z>5)throw new Error('Depth order missing for '+role);
    boxes[role]={x:b[0],y:b[1],w:b[2],h:b[3],cx:b[0]+b[2]/2,foot:b[1]+b[3],z:entry.z};
  }
  if(!boxes.hero||Object.keys(boxes).length<3) throw new Error('Reference must distinguish at least three roles including hero');
  const pairs=[];
  const roles=Object.keys(boxes);
  for(let i=0;i<roles.length;i++)for(let j=i+1;j<roles.length;j++){
    const a=boxes[roles[i]],b=boxes[roles[j]];
    const w=Math.max(0,Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x));
    const h=Math.max(0,Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y));
    const intersection=w*h;
    if(intersection>.001) pairs.push({a:roles[i],b:roles[j],boxOverlap:intersection/Math.max(.0001,Math.min(a.w*a.h,b.w*b.h)),front:a.z>b.z?roles[i]:roles[j]});
  }
  const minX=Math.min(...roles.map(r=>boxes[r].x)),maxX=Math.max(...roles.map(r=>boxes[r].x+boxes[r].w));
  const minY=Math.min(...roles.map(r=>boxes[r].y)),maxY=Math.max(...roles.map(r=>boxes[r].foot));
  return {id:ref.id,source:ref.source,roles,boxes,pairs,group:{x:minX,y:minY,w:maxX-minX,h:maxY-minY},provenance:ref.provenance||null};
}

/** All proposed variants inherit reference-relative role topology. Never copy source/reference pixels. */
export function deriveCompositionTerritories(grammar,productRoles){
 const roles=productRoles.filter(r=>grammar.boxes[r]);
 const central=grammar.boxes.hero.cx;
 const anchor=Object.fromEntries(roles.map(role=>[role,grammar.boxes[role].cx]));
 const mapA=(v)=>clamp(.5+(v-.51)*.77,.16,.84);
 const specs=[
  {id:'reference-echo',name:'Reference Echo',transform:r=>mapA(anchor[r]),foot:r=>({wide:.795,hero:.833,secondary:.863,accent:.886}[r]??.855),rotation:r=>r==='accent'?-4:0},
  {id:'directional-asymmetry',name:'Directional Asymmetry',transform:r=>clamp(1-mapA(anchor[r])+(r==='accent'?.045:0),.14,.86),foot:r=>({wide:.794,hero:.850,secondary:.885,accent:.896}[r]??.86),rotation:r=>r==='accent'?5:0},
  {id:'staggered-editorial',name:'Staggered Editorial',transform:r=>clamp(.5+(anchor[r]-central)*.65+(r==='hero'?-.10:r==='secondary'?.05:r==='wide'?.065:r==='accent'?.10:0),.17,.83),foot:r=>({wide:.806,hero:.852,secondary:.825,accent:.893}[r]??.865),rotation:r=>r==='accent'?-7:r==='secondary'?2:0},
 ];
 return specs.map(t=>({id:t.id,name:t.name,referenceId:grammar.id,source:grammar.source,roles:roles.map(r=>({role:r,x:t.transform(r),foot:t.foot(r),rotation:t.rotation(r),z:grammar.boxes[r].z}))}));
}
