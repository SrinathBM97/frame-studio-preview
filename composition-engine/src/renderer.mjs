/** FRAME v4 transparent composition renderer. No source RGB mutation and no fake background/podium. */
export const DEFAULT_SHADOWS=Object.freeze({ground:'#2C003B',overlap:'#000000',contactOpacity:.55,ambientOpacity:.21,overlapOpacity:.3,contactBlur:10,ambientBlur:34,overlapBlur:15,offsetX:13,offsetY:17});
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function softContact(ctx,x,y,rx,ry,color,opacity,blur){
 ctx.save();ctx.filter=`blur(${Math.max(0,blur)}px)`;ctx.fillStyle=color;ctx.globalAlpha=clamp(opacity,0,1);ctx.beginPath();ctx.ellipse(x,y,Math.max(3,rx),Math.max(2,ry),0,0,Math.PI*2);ctx.fill();ctx.restore();
}
function shadowMask(ctx,img,l,settings){
 // Shadow cast by an original product alpha silhouette, not its original color or an invented shape.
 const temp=document.createElement('canvas');temp.width=Math.max(1,Math.ceil(l.w));temp.height=Math.max(1,Math.ceil(l.h));
 const tc=temp.getContext('2d',{willReadFrequently:false});
 const src=l.sourceRect;
 if(src)tc.drawImage(img,src.x,src.y,src.w,src.h,0,0,temp.width,temp.height);else tc.drawImage(img,0,0,temp.width,temp.height);
 tc.globalCompositeOperation='source-in';tc.fillStyle=settings.overlap;tc.fillRect(0,0,temp.width,temp.height);
 ctx.save();ctx.globalAlpha=clamp(settings.overlapOpacity,0,1);ctx.filter=`blur(${Math.max(0,settings.overlapBlur)}px)`;
 ctx.translate(l.x+settings.offsetX,l.top+l.h/2+settings.offsetY);ctx.rotate((l.rotation||0)*Math.PI/180);
 ctx.drawImage(temp,-l.w/2,-l.h/2,l.w,l.h);ctx.restore();
}
export function renderTransparentComposition(canvas,scene,sources,shadowSettings={}){
 if(!canvas?.getContext)throw new Error('Canvas 2D context required');
 const opts={...DEFAULT_SHADOWS,...shadowSettings};
 canvas.width=scene.canvas.width;canvas.height=scene.canvas.height;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,canvas.width,canvas.height);
 const layers=[...scene.layers].sort((a,b)=>a.z-b.z);
 // Transparent ground-plane lighting: only shadows, never a filled background.
 for(const l of layers){
   if(opts.ambientOpacity>0)softContact(ctx,l.x+opts.offsetX,l.foot+4,l.w*.55,Math.max(9,l.w*.07),opts.ground,opts.ambientOpacity,opts.ambientBlur);
   if(opts.contactOpacity>0)softContact(ctx,l.x,l.foot-1,l.w*.40,Math.max(5,l.w*.037),opts.ground,opts.contactOpacity,opts.contactBlur);
 }
 for(const l of layers){
   const img=sources.get?.(l.id)??sources[l.id];if(!img)throw new Error('Missing immutable RGBA source '+l.id);
   // Real alpha silhouette shadow appears on lower products, then source is drawn unchanged.
   if(opts.overlapOpacity>0)shadowMask(ctx,img,l,opts);
   ctx.save();ctx.translate(l.x,l.top+l.h/2);ctx.rotate((l.rotation||0)*Math.PI/180);
   if(l.sourceRect){const r=l.sourceRect;ctx.drawImage(img,r.x,r.y,r.w,r.h,-l.w/2,-l.h/2,l.w,l.h)}
   else ctx.drawImage(img,-l.w/2,-l.h/2,l.w,l.h);ctx.restore();
 }
 return canvas;
}
