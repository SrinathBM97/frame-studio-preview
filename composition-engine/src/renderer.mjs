/** FRAME transparent compositor. This renders shadows to RGBA, never a podium/background. */
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const DEFAULT_SHADOWS=Object.freeze({ground:'#2C003B',overlap:'#000000',contactOpacity:.36,ambientOpacity:.19,overlapOpacity:.19,contactBlur:15,ambientBlur:38,offsetX:11,offsetY:13});
function shadowEllipse(ctx,x,y,rx,ry,color,opacity,blur){
  ctx.save();ctx.filter=`blur(${blur}px)`;ctx.globalAlpha=opacity;
  ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fill();ctx.restore();
}
/** `sources` Maps product IDs to HTMLImageElement/ImageBitmap/Canvas, contains raw cutouts. */
export function renderTransparentComposition(canvas,scene,sources,shadowSettings={}){
  if(!canvas?.getContext)throw new Error('Canvas with 2D context required');
  const shadow={...DEFAULT_SHADOWS,...shadowSettings};
  const ctx=canvas.getContext('2d');canvas.width=scene.canvas.width;canvas.height=scene.canvas.height;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const layers=[...scene.layers].sort((a,b)=>a.z-b.z);
  // Plane lighting: shadow pass beneath products, but no opaque ground plane.
  for(const p of layers){
    shadowEllipse(ctx,p.x+shadow.offsetX,p.foot+3,p.w*.53,Math.max(11,p.w*.085),shadow.ground,clamp(shadow.ambientOpacity,0,1),shadow.ambientBlur);
    shadowEllipse(ctx,p.x,p.foot,p.w*.37,Math.max(8,p.w*.056),shadow.ground,clamp(shadow.contactOpacity,0,1),shadow.contactBlur);
  }
  for(const p of layers){
    const image=sources.get?.(p.id)??sources[p.id];
    if(!image)throw new Error('Missing original product alpha asset: '+p.id);
    // An independently rendered overlap shadow may fall on a rear object.
    ctx.save();ctx.filter='blur(8px)';ctx.globalAlpha=clamp(shadow.overlapOpacity,0,1);
    // Browser canvas temporary layers should use source-in to produce a BLACK silhouette.
    const temp=document.createElement('canvas');
    temp.width=Math.max(1,Math.ceil(p.w));temp.height=Math.max(1,Math.ceil(p.h));
    const tc=temp.getContext('2d');tc.drawImage(image,0,0,temp.width,temp.height);
    tc.globalCompositeOperation='source-in';tc.fillStyle=shadow.overlap;tc.fillRect(0,0,temp.width,temp.height);
    ctx.translate(p.x+shadow.offsetX,p.top+p.h/2+shadow.offsetY);
    ctx.rotate((p.rotation||0)*Math.PI/180);
    ctx.drawImage(temp,-p.w/2,-p.h/2,p.w,p.h);
    ctx.restore();
    ctx.save();ctx.translate(p.x,p.top+p.h/2);ctx.rotate((p.rotation||0)*Math.PI/180);
    ctx.drawImage(image,-p.w/2,-p.h/2,p.w,p.h);ctx.restore();
  }
  return canvas;
}
