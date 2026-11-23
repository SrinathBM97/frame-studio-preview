import assert from 'node:assert/strict';
import {resolveEvidence,exactPdfMatch,EVIDENCE} from '../src/evidence.mjs';
import {planCompositions} from '../src/planner.mjs';
import {validateReferenceGuide} from '../src/reference.mjs';
const MASK=Uint8Array.from({length:48*48},()=>255);
const product=(id,role,w,h,r)=>({id,role,width:w,height:h,maskGrid:MASK,labels:[{x:.29,y:.3,w:.39,h:.22,confirmed:true,priority:'brand'}],pose:'upright_closed',evidence:r?{status:EVIDENCE.PDF_EXACT,referenceHeightPx:r,referenceFrame:'forever52_60ml_1200px'}:{status:EVIDENCE.UNKNOWN}});
const four=[product('hero','hero',230,700,1200),product('box','wide',580,620,null),product('small','accent',195,400,741),product('side','secondary',190,600,1036)];
const result=planCompositions(four,{seed:4,trials:35});
assert.equal(result.options.length,3);
assert.equal(result.options.every(o=>o.layers.length===4),true);
assert.equal(result.options[0].scaleVerified,false);
assert.equal(result.approval,'NOT_PRODUCTION_APPROVED');
for(const option of result.options){
 const hero=option.layers.find(x=>x.id==='hero'),side=option.layers.find(x=>x.id==='side');
 assert.ok(Math.abs(side.h/hero.h-(1036/1200))<1e-9);
 assert.ok(option.qa.metrics.labelVisibility.length===4);
}
assert.equal(exactPdfMatch('L Oreal Paris Infallible Full Wear Concealer 10 ml').source.page,6);
assert.equal(exactPdfMatch('Nykaa Stay All Day Lipstick 3.5 g','upright_closed'),null);
assert.equal(exactPdfMatch('Nykaa Stay All Day Lipstick 3.5 g','opened_with_cap').referenceHeightPx,741);
assert.equal((await resolveEvidence({sku:'a product',pose:'upright_closed'},{onlineLookup:async()=>({sku:'a product',heightMm:80,pose:'upright_closed',dimensionType:'shipping_package',url:'https://brand.example/a'})})).status,EVIDENCE.UNKNOWN);
assert.throws(()=>validateReferenceGuide({source:'approved_reference',anchors:{hero:{x:1.2,foot:.8}}}));
const tri=[product('hero','hero',240,850,1340),product('serum','accent',165,350,781),product('tube','secondary',150,530,1040)];
const three=planCompositions(tri,{seed:1,trials:25});
assert.equal(three.options.every(x=>x.layers.every(l=>l.role!=='wide')),true,'no phantom wide product in 3-item set');
console.log('PASS v4 public synthetic tests');
