/** An art-director-approved reference can guide role positions without copying source imagery.
 * This is a structured adapter, not automatic understanding of a reference image.
 */
export const REFERENCE_ROLES=['hero','wide','accent','secondary'];
const finite=v=>Number.isFinite(v)&&v>=0&&v<=1;
export function validateReferenceGuide(guide){
 if(!guide||guide.source!=='approved_reference'||!guide.anchors)throw new Error('A reference needs approved_reference provenance and role anchors');
 const out={};
 for(const role of REFERENCE_ROLES){
  const v=guide.anchors[role];if(!v)continue;
  if(!finite(v.x)||!finite(v.foot))throw new Error('Invalid normalized reference anchor for '+role);
  out[role]=[v.x,v.foot];
 }
 if(!out.hero||!out.wide||!out.accent)throw new Error('Reference guide needs hero, wide, accent placements');
 return {id:guide.id||'approved-reference',source:guide.source,anchors:out,notes:guide.notes||null};
}
export function applyReferenceToStyles(styles,guide){
 if(!guide)return styles;
 const ref=validateReferenceGuide(guide);
 return styles.map((style,i)=>{
   // Apply to first proposal only; other two remain independent creative directions.
   if(i!==0)return style;
   const positions={...style.positions,...ref.anchors};
   return {...style,id:`reference-${ref.id}`,name:'Reference-led Composition',positions,targetOverlap:.055,referenceSource:ref.source};
 });
}
