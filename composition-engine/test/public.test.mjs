import assert from 'node:assert/strict';
import {compileReferenceGrammar,deriveCompositionTerritories} from '../src/reference_grammar.mjs';
import {planReferenceCompositions} from '../src/reference_planner.mjs';
const ref={id:'synthetic-layout',source:'human_reference_study',boxes:{
 hero:{bbox:[.31,.16,.24,.76],z:1},wide:{bbox:[.59,.31,.27,.59],z:0},
 secondary:{bbox:[.10,.36,.17,.53],z:2},accent:{bbox:[.50,.64,.19,.28],z:3}
}};
const gram=compileReferenceGrammar(ref);
assert.equal(gram.roles.length,4);
assert.ok(gram.pairs.length>0);
assert.equal(deriveCompositionTerritories(gram,['hero','wide','accent','secondary']).length,3);
assert.throws(()=>compileReferenceGrammar({...ref,source:'unverified_model_guess'}),/provenance/);
assert.throws(()=>compileReferenceGrammar({...ref,boxes:{...ref.boxes,hero:{bbox:[.9,.1,.3,.5],z:1}}}),/Invalid reference geometry/);
const shape=Uint8Array.from({length:48*48},(_,i)=>{let x=i%48,y=Math.floor(i/48);return x>4&&x<44&&y>2&&y<47?255:0});
const p=(id,role,w,h,px)=>({id,role,width:w,height:h,maskGrid:shape,labels:[{x:.30,y:.37,w:.4,h:.18,priority:'brand',source:'manual'}],evidence:px?{status:'pdf_exact',referenceHeightPx:px,referenceFrame:'forever52_60ml_1200px'}:{status:'unknown'},estimatedReferenceHeightPx:px?null:920});
const products=[p('a','hero',240,800,1340),p('b','accent',210,460,781),p('c','wide',610,690,null),p('d','secondary',180,650,null)];
const full=planReferenceCompositions(products,ref,{trials:300,seed:9});
assert.equal(full.options.length,3);assert.equal(full.scaleVerified,false);
for(const opt of full.options){
 const a=opt.layers.find(x=>x.id==='a'),b=opt.layers.find(x=>x.id==='b');
 assert.ok(Math.abs(b.h/a.h-781/1340)<1e-9);
 assert.notEqual(opt.approval,'PRODUCTION_APPROVED');
}
const tri=planReferenceCompositions(products.filter(x=>x.role!=='wide'),ref,{trials:200,seed:7});
assert.ok(tri.options.every(x=>x.layers.length===3));
console.log('PASS: verified provenance, three reference territories, constrained ratio, honest approval gates, 3–4 products');
