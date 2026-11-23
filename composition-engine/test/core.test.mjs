import assert from 'node:assert/strict';
import {EVIDENCE,exactPdfMatch,resolveEvidence,compareEvidence,buildScaleBasis} from '../src/evidence.mjs';
import {planCompositions,assessScene} from '../src/planner.mjs';

const solid=()=>new Uint8Array(48*48).fill(255);
const src=(id,width,height,role,referenceHeightPx,labels=[{x:.3,y:.33,w:.38,h:.3,confirmed:true}])=>({
 id,width,height,role,maskGrid:solid(),labels,sku:id,pose:'upright_closed',
 evidence:referenceHeightPx?{status:EVIDENCE.PDF_EXACT,referenceHeightPx,referenceFrame:'forever52_60ml_1200px'}:{status:EVIDENCE.UNKNOWN}
});
const set=[
 src('hero',320,800,'hero',1200),
 src('compact',550,360,'wide',null,[{x:.21,y:.22,w:.6,h:.38,confirmed:true}]),
 src('concealer',170,670,'secondary',1036),
 src('lipstick',130,530,'accent',741),
];
assert.equal(exactPdfMatch('Daily Life Forever52 Pro Artist Ultra Definition Liquid Foundation 60 ml')?.referenceHeightPx,1200);
assert.equal(exactPdfMatch('random 100 ml bottle'),null,'volume must NEVER imply a reference height');
assert.equal((await resolveEvidence({sku:'generic file.jpg',pose:'upright_closed'})).status,EVIDENCE.UNKNOWN);
assert.deepEqual(compareEvidence({referenceHeightPx:741,referenceFrame:'r'},{referenceHeightPx:1200,referenceFrame:'r'}),{ratio:.6175,comparable:true,kind:'chart_relative'});
assert.equal(compareEvidence({referenceHeightPx:741,referenceFrame:'r'},{heightMm:120}).comparable,false);

const p=planCompositions(set,{seed:1,trials:12});
assert.equal(p.options.length,3);
assert.equal(new Set(p.options.map(x=>x.direction)).size,3);
assert.equal(p.approval,'NOT_PRODUCTION_APPROVED');
assert.equal(p.options.every(o=>o.layers.length===4),true);
for(const opt of p.options){
 assert.equal(new Set(opt.layers.map(l=>l.id)).size,4);
 const f=opt.layers.find(l=>l.id==='hero'),c=opt.layers.find(l=>l.id==='concealer');
 assert.ok(Math.abs((c.h/f.h)-(1036/1200))<1e-10,'height ratio must remain exactly equal to chart reference');
 assert.equal(opt.scaleVerified,false,'missing compact evidence must not be marked verified');
}
// Deliberate collision tests: a front rectangle over the hero printed region must be rejected.
const twoFront=[{id:'hero',x:1000,top:500,w:380,h:1000,z:0,foot:1500},{id:'compact',x:1000,top:640,w:360,h:710,z:3,foot:1350}];
const collision=assessScene(twoFront,set.slice(0,2));
assert.ok(collision.hardFailures>0);
assert.ok(collision.diagnostics.some(x=>x.type==='printed-label-obscured'));
// Incompatible PDF chart units and physical millimeters cannot silently mix.
const mix=[src('pdf',220,790,'hero',1200),src('web',180,600,'accent',null),src('more',280,800,'wide',890)];
mix[1].evidence={status:EVIDENCE.ONLINE_VERIFIED,heightMm:110};
const scaleMix=buildScaleBasis(mix);
assert.equal(scaleMix.scaleVerified,false);
assert.ok(scaleMix.warnings.some(x=>x.reason.includes('without same-SKU bridge')));
const match=await resolveEvidence({sku:'Brand Product 30 ml',pose:'upright_closed'},{onlineLookup:async ()=>({heightMm:92,url:'https://brand.example/product',pose:'upright_closed'})});
assert.equal(match.status,EVIDENCE.ONLINE_VERIFIED);
assert.equal(match.heightMm,92);
// Unknown SKU must stay unverified even if a successful visual draft exists.
assert.equal(p.warnings.some(x=>x.id==='compact'),true);
// Different scales only if backed by evidence. Never invent volume-to-pixel mappings.
console.log('PASS: exact PDF evidence, unknown fallback, ratio precision, 3 directions, label occlusion, source independence');
