/** FRAME composition architecture: scale evidence is not inferred from package volume. */
export const EVIDENCE = Object.freeze({
  PDF_EXACT: 'pdf_exact',
  ONLINE_VERIFIED: 'online_verified',
  ESTIMATED: 'estimated',
  UNKNOWN: 'unknown',
});

// Reference examples visually checked against the supplied 19-page Nykaa chart.
// Page and pose must match before an exact value may be assigned to a user's SKU.
// No automatic "category => exact dimension" fallback.
export const NYKAA_REFERENCE_CATALOG = Object.freeze([
  { sku:'daily life forever52 pro artist ultra definition liquid foundation 60 ml', pose:'upright_closed', height:1200, page:7, provenance:'nykaa-chart' },
  { sku:'cosrx advanced snail 96 mucin power essence 100 ml', pose:'upright_closed', height:1340, page:11, provenance:'nykaa-chart' },
  { sku:'dot & key strawberry bright niacinamide face serum 30 ml', pose:'upright_closed', height:781, page:11, provenance:'nykaa-chart' },
  { sku:'loreal paris infallible full wear concealer 10 ml', pose:'upright_closed', height:1036, page:6, provenance:'nykaa-chart-p6-visual-confirmed' },
  { sku:'nykaa stay all day lipstick 3.5 g', pose:'opened_with_cap', height:741, page:3, provenance:'nykaa-chart-p3-visual-confirmed-including-cap' },
]);

const clean=(str)=>String(str||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim().replace(/\s+/g,' ');
const ALIASES = new Map([
  ['l oreal paris infallible full wear concealer 10 ml','loreal paris infallible full wear concealer 10 ml'],
  ['loreal paris infallible full wear 10 ml','loreal paris infallible full wear concealer 10 ml'],
  ['dot key strawberry bright 10 niacinamide face serum 30ml','dot key strawberry bright niacinamide face serum 30 ml'],
  ['dot key strawberry bright 10 niacinamide face serum 30 ml','dot key strawberry bright niacinamide face serum 30 ml'],
  ['cosrx advanced snail 96 mucin power essence 100ml','cosrx advanced snail 96 mucin power essence 100 ml'],
  ['nykaa stay all day lipstick 3 5 g','nykaa stay all day lipstick 3 5 g']
]);
const canonical=(value)=>ALIASES.get(clean(value))||clean(value);
export function exactPdfMatch(name,pose='upright_closed',catalog=NYKAA_REFERENCE_CATALOG){
  const a=canonical(name);
  const entry=catalog.find(x=>canonical(x.sku)===a && x.pose===pose);
  if(!entry) return null;
  return {status:EVIDENCE.PDF_EXACT,referenceHeightPx:entry.height,referenceFrame:'forever52_60ml_1200px',source:{type:'pdf',page:entry.page,sku:entry.sku,pose:entry.pose,provenance:entry.provenance}};
}

/**
 * `onlineLookup` is a trusted SERVER adapter, not a promise that a static browser page
 * can Google autonomously. It may return measured physical height in mm and evidence URL.
 * Verified millimeter measurements can only be compared with other MM measurements,
 * never mixed with arbitrary PDF reference pixels without a documented anchor.
 */
export async function resolveEvidence(product,{catalog=NYKAA_REFERENCE_CATALOG,onlineLookup=null}={}){
  const exact=exactPdfMatch(product.sku,product.pose,catalog);
  if(exact)return exact;
  if(onlineLookup){
    const found=await onlineLookup({sku:product.sku,pose:product.pose});
    if(found && Number.isFinite(found.heightMm)&&found.heightMm>0 && /^https:\/\//.test(found.url||'') && found.pose===product.pose && found.dimensionType==='product' && clean(found.sku)===clean(product.sku))
      return {status:EVIDENCE.ONLINE_VERIFIED,heightMm:found.heightMm,source:{type:'online',url:found.url,checkedAt:found.checkedAt||null,sku:product.sku,pose:found.pose}};
  }
  return {status:EVIDENCE.UNKNOWN,source:null};
}

export function compareEvidence(a,b){
  if(a?.referenceHeightPx>0&&b?.referenceHeightPx>0&&a.referenceFrame===b.referenceFrame)
    return {ratio:a.referenceHeightPx/b.referenceHeightPx,comparable:true,kind:'chart_relative'};
  if(a?.heightMm>0&&b?.heightMm>0)
    return {ratio:a.heightMm/b.heightMm,comparable:true,kind:'physical_mm'};
  return {ratio:null,comparable:false,kind:'no_common_evidence'};
}

/**
 * Resolve comparable heights without silently mixing two measurement systems.
 * PDF heights are a reference coordinate system, not physical millimeters.
 * If both are present, a same-SKU bridge is required to map them.
 */
export function buildScaleBasis(products){
  const has=(p,k)=>Number.isFinite(p.evidence?.[k]) && p.evidence[k]>0;
  const frames=[...new Set(products.filter(p=>has(p,'referenceHeightPx')).map(p=>p.evidence.referenceFrame))];
  const bridge=products.find(p=>has(p,'referenceHeightPx')&&has(p,'heightMm'));
  const frame=frames[0]||null;
  const canBridge=!!(bridge && bridge.evidence.referenceFrame===frame && frames.length<=1);
  const mmToRef=canBridge?bridge.evidence.referenceHeightPx/bridge.evidence.heightMm:null;
  const heights=new Map(),warnings=[];
  for(const p of products){
    if(has(p,'referenceHeightPx') && p.evidence.referenceFrame===frame){
      heights.set(p.id,{value:p.evidence.referenceHeightPx,kind:'reference_px',confirmed:true});
    }else if(has(p,'heightMm') && (!frame || canBridge)){
      heights.set(p.id,{value:p.evidence.heightMm*(mmToRef||1),kind:frame?'calibrated_mm_to_reference':'millimeters',confirmed:true});
    }else if(p.estimatedReferenceHeightPx>0){
      heights.set(p.id,{value:p.estimatedReferenceHeightPx,kind:'draft_proxy',confirmed:false});
      warnings.push({id:p.id,reason:'Draft proxy is not an exact SKU measurement'});
    }else{
      heights.set(p.id,{value:p.height,kind:'source_pixels_only',confirmed:false});
      warnings.push({id:p.id,reason:'Source image pixels are NOT real product dimensions'});
    }
  }
  if(frames.length>1)warnings.push({reason:'Conflicting PDF reference frames without a calibrated transform'});
  if(frame && products.some(p=>has(p,'heightMm')&&!has(p,'referenceHeightPx'))&&!canBridge)
    warnings.push({reason:'Physical dimensions cannot be compared to PDF pixel references without same-SKU bridge'});
  return {heights,frame,bridged:canBridge,scaleVerified:warnings.length===0&&products.every(p=>heights.get(p.id).confirmed),warnings};
}

export function validateScaleEvidence(products){
  const ids=new Set(),warnings=[];
  if(products.length<3||products.length>4)throw new Error('Composition requires 3 or 4 products');
  for(const p of products){
    if(!p.id||ids.has(p.id))throw new Error('Every product needs a unique stable ID');
    ids.add(p.id);
    if(!(p.width>0&&p.height>0))throw new Error('Invalid source silhouette for '+p.id);
    if(!p.evidence || p.evidence.status===EVIDENCE.UNKNOWN)warnings.push({id:p.id,reason:'Scale unverified — do not label exact'});
    if(p.evidence?.status===EVIDENCE.ESTIMATED)warnings.push({id:p.id,reason:'Scale is an estimate, not a verified measurement'});
  }
  const basis=buildScaleBasis(products);
  return {warnings:[...warnings,...basis.warnings],scaleVerified:warnings.length===0&&basis.scaleVerified,basis};
}
