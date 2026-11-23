/** FRAME reference-guided scene solver: immutable RGB, strict scale evidence, no invisible labels. */
import {validateScaleEvidence} from './evidence.mjs';
import {assessScene,localToWorld,worldToLocal} from './planner.mjs';
import {compileReferenceGrammar,deriveCompositionTerritories} from './reference_grammar.mjs';
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const GRID=48;
function noise(seed){let x=seed>>>0;x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296-.5}
function occupancy(p,u,v){if(u<0||v<0||u>=1||v>=1)return 0;const a=p.maskGrid;return !a?true:(a[Math.floor(v*GRID)*GRID+Math.floor(u*GRID)]??0)>128}
function pairOverlap(a,b,productMap){let n=0,ov=0;const pa=productMap.get(a.id),pb=productMap.get(b.id);
 for(let y=0;y<28;y++)for(let x=0;x<28;x++){
  const u=(x+.5)/28,v=(y+.5)/28;if(!occupancy(pa,u,v))continue;n++;
  const w=localToWorld(u,v,a),q=worldToLocal(w.x,w.y,b);if(occupancy(pb,q.u,q.v))ov++;
 }
 return ov/Math.max(1,n);
}
export function summarizeVisualStructure(layers,products,canvas){
 const pmap=new Map(products.map(p=>[p.id,p]));let pairCount=0,occlusionCount=0,depthPairs=[];
 const sorted=[...layers].sort((a,b)=>a.z-b.z);
 for(let i=0;i<sorted.length;i++)for(let j=i+1;j<sorted.length;j++){
   const rear=sorted[i],front=sorted[j];const ratio=pairOverlap(rear,front,pmap);
   if(ratio>.002){pairCount++;if(ratio>.018)occlusionCount++;depthPairs.push({back:rear.role,front:front.role,ratio:+ratio.toFixed(4)})}
 }
 const roleMap=Object.fromEntries(layers.map(l=>[l.role,l]));
 const xs=layers.map(l=>l.x),feet=layers.map(l=>l.foot);
 const minX=Math.min(...layers.map(l=>l.x-l.w/2)),maxX=Math.max(...layers.map(l=>l.x+l.w/2));
 const foreground=roleMap.accent,hero=roleMap.hero;
 const coverage=(maxX-minX)/canvas.width;
 const center=(maxX+minX)/2/canvas.width;
 const footVariance=(Math.max(...feet)-Math.min(...feet))/canvas.height;
 const accentInFront=!!(foreground&&hero&&foreground.z>hero.z&&foreground.foot>hero.foot+canvas.height*.015);
 return {pairCount,occlusionCount,depthPairs,coverage,center,footVariance,accentInFront};
}

/** Aesthetic scoring is a *diagnostic*; never equate it with creative director approval. */
export function assessReferenceCandidate(layers,products,canvas,territory){
 const geometry=assessScene(layers,products,canvas);
 const structure=summarizeVisualStructure(layers,products,canvas);
 let score=geometry.score, warnings=[];
 const slots=new Map(territory.roles.map(r=>[r.role,r]));
 for(const l of layers){const s=slots.get(l.role);if(!s)continue;
  score-=Math.abs(l.x/canvas.width-s.x)*175;
  score-=Math.abs(l.foot/canvas.height-s.foot)*155;
 }
 // Depth is induced through edge contacts, not covering logos.
 if(structure.occlusionCount<1){score-=145;warnings.push('No meaningful product occlusion; sticker-like lineup risk')}
 if(structure.footVariance<.035){score-=105;warnings.push('Insufficient front/rear depth separation')}
 if(!structure.accentInFront){score-=120;warnings.push('Accent is not clearly foregrounded')}
 score-=Math.abs(structure.coverage-.68)*300;
 score-=Math.abs(structure.center-.5)*245;
 if(structure.coverage>.81||structure.coverage<.45){score-=1500+5500*Math.max(0,structure.coverage-.81);warnings.push('Group occupies an unsuitable fraction of the canvas')}
 return {geometry,structure,score,hardFailures:geometry.hardFailures,warnings};
}

export function planReferenceCompositions(products,reference,{canvas={width:2000,height:2000},seed=31,trials=900,maxCanvasHeight=.59}={}){
 const input=validateScaleEvidence(products),grammar=compileReferenceGrammar(reference);
 const available=products.map(p=>p.role);
 if(new Set(available).size!==available.length)throw new Error('Every product must have a distinct role for the reference study');
 for(const r of available)if(!grammar.boxes[r])throw new Error('Missing reference role '+r);
 const heights=input.basis.heights;const max=Math.max(...products.map(p=>heights.get(p.id).value));
 const pxPerUnit=canvas.height*maxCanvasHeight/max;
 const roles=deriveCompositionTerritories(grammar,available);
 const options=[];
 for(const [idx,t] of roles.entries()){
  let best=null;
  for(let trial=0;trial<trials;trial++){
   const layers=[];
   for(const [j,s] of t.roles.entries()){
    const p=products.find(p=>p.role===s.role),h=heights.get(p.id).value*pxPerUnit,w=h*p.width/p.height;
    const nx=(trial===0?0:noise(seed+idx*100000+trial*2009+j*157))*.30;
    const ny=(trial===0?0:noise(seed+idx*450003+trial*491+j*137))*.11;
    const a=s.rotation*Math.PI/180;const rotatedWidth=Math.abs(w*Math.cos(a))+Math.abs(h*Math.sin(a));
    const x=clamp((s.x+nx)*canvas.width,canvas.width*.065+rotatedWidth/2,canvas.width*.935-rotatedWidth/2);
    const foot=clamp(canvas.height*(s.foot+ny),canvas.height*.72,canvas.height*.895);
    const rot=s.rotation;
    layers.push({id:p.id,role:s.role,x,w,h,top:foot-h,foot,rotation:rot,z:s.z,sourceRect:p.sourceRect||null,scaleEvidence:p.evidence?.status||'unknown',referenceId:grammar.id,depthPlane:s.z===0?'rear':s.z===3?'front':'middle'});
   }
   const qa=assessReferenceCandidate(layers,products,canvas,t);
   if(!best||qa.hardFailures<best.qa.hardFailures||(qa.hardFailures===best.qa.hardFailures&&qa.score>best.qa.score))best={layers,qa};
  }
  options.push({id:t.id,title:t.name,layers:best.layers,qa:best.qa,ratioVerified:input.scaleVerified,referenceId:grammar.id,approval:best.qa.hardFailures?'BLOCKED_GEOMETRY_OR_LABELS':best.qa.warnings.length?'BLOCKED_AUTOMATED_VISUAL_QA':'CREATIVE_DIRECTOR_REVIEW_REQUIRED'});
 }
 return {schema:'frame-reference-composition/5',canvas,reference:{id:grammar.id,source:grammar.source,roleCount:grammar.roles.length,sourcePixelTransfer:false},options,scaleWarnings:input.warnings,scaleVerified:input.scaleVerified,approval:'NOT_PRODUCTION_APPROVED'};
}
