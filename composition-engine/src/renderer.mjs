/** FRAME v5 reference composition renderer: immutable source assets + separate lighting layers. */
export const DEFAULT_SHADOWS=Object.freeze({
 ground:'#2C003B', overlap:'#000000',
 contactOpacity:.48,ambientOpacity:.23,overlapOpacity:.42,
 contactBlur:14,ambientBlur:42,overlapBlur:11,offsetX:11,offsetY:17
});
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function surface(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c}
function ellipse(ctx,x,y,rx,ry,color,opacity,blur){
 if(opacity<=0)return;
 ctx.save();ctx.globalAlpha=clamp(opacity,0,1);ctx.fillStyle=color;
 ctx.filter=`blur(${Math.max(0,blur)}px)`;
 ctx.beginPath();ctx.ellipse(x,y,Math.max(2,rx),Math.max(2,ry),0,0,Math.PI*2);ctx.fill();ctx.restore();
}
function drawSource(ctx,img,l,dx=0,dy=0){
 ctx.save();ctx.translate(l.x+dx,l.top+l.h/2+dy);ctx.rotate((l.rotation||0)*Math.PI/180);
 const r=l.sourceRect;
 if(r)ctx.drawImage(img,r.x,r.y,r.w,r.h,-l.w/2,-l.h/2,l.w,l.h);
 else ctx.drawImage(img,-l.w/2,-l.h/2,l.w,l.h);
 ctx.restore();
}
function silhouette(img,l,color){
 const t=surface(Math.max(1,Math.ceil(l.w)),Math.max(1,Math.ceil(l.h)));
 const c=t.getContext('2d');const r=l.sourceRect;
 if(r)c.drawImage(img,r.x,r.y,r.w,r.h,0,0,t.width,t.height);
 else c.drawImage(img,0,0,t.width,t.height);
 c.globalCompositeOperation='source-in';c.fillStyle=color;c.fillRect(0,0,t.width,t.height);
 return t;
}
function castOntoAlreadyPresentProducts(ctx,rearAlpha,img,l,opts){
 const W=rearAlpha.width,H=rearAlpha.height;
 const shadow=surface(W,H),sx=shadow.getContext('2d');
 const temp=silhouette(img,l,opts.overlap);
 sx.save();sx.filter=`blur(${Math.max(0,opts.overlapBlur)}px)`;
 sx.globalAlpha=clamp(opts.overlapOpacity,0,1);
 sx.translate(l.x+opts.offsetX,l.top+l.h/2+opts.offsetY);sx.rotate((l.rotation||0)*Math.PI/180);
 sx.drawImage(temp,-l.w/2,-l.h/2,l.w,l.h);sx.restore();
 // Composite black shadow only onto already-drawn products. No sticker halo in empty air.
 sx.globalCompositeOperation='destination-in';sx.drawImage(rearAlpha,0,0);
 ctx.drawImage(shadow,0,0);
}
export function renderTransparentComposition(canvas,scene,sources,shadowSettings={}){
 if(!canvas?.getContext)throw new Error('Canvas 2D required');
 const opts={...DEFAULT_SHADOWS,...shadowSettings};const W=scene.canvas.width,H=scene.canvas.height;
 canvas.width=W;canvas.height=H;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,W,H);
 const layers=[...scene.layers].sort((a,b)=>a.z-b.z);
 // Invisible shared ground plane: independent contact/ambient penumbras, no podium or background.
 for(const l of layers){
  ellipse(ctx,l.x+opts.offsetX*.5,l.foot+4,l.w*.53,Math.max(8,l.w*.067),opts.ground,opts.ambientOpacity,opts.ambientBlur);
  ellipse(ctx,l.x,l.foot-2,l.w*.36,Math.max(4,l.w*.028),opts.ground,opts.contactOpacity,opts.contactBlur);
 }
 const rearAlpha=surface(W,H),rc=rearAlpha.getContext('2d');
 for(const [index,l] of layers.entries()){
  const img=sources.get?.(l.id)??sources[l.id];if(!img)throw new Error('Missing immutable source '+l.id);
  if(index>0&&opts.overlapOpacity>0)castOntoAlreadyPresentProducts(ctx,rearAlpha,img,l,opts);
  drawSource(ctx,img,l);drawSource(rc,img,l);
 }
 return canvas;
}
