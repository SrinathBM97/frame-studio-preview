"""Transparent physically motivated contact/ambient and product-on-product occlusion shadows."""
from __future__ import annotations
from dataclasses import dataclass
from PIL import Image,ImageFilter,ImageDraw
import numpy as np

@dataclass
class ShadowControls:
 ground_color:str='#2C003B'
 overlap_color:str='#000000'
 contact_opacity:float=.42
 ambient_opacity:float=.19
 overlap_opacity:float=.34
 contact_blur:int=11
 ambient_blur:int=36
 overlap_blur:int=14
 offset_x:int=11
 offset_y:int=15

def tint(mask:Image.Image,hex_color:str,opacity:float):
 c=hex_color.lstrip('#');color=tuple(int(c[i:i+2],16) for i in (0,2,4))
 a=mask.point(lambda x:int(x*max(0,min(1,opacity))))
 r=Image.new('RGBA',mask.size,color+(0,));r.putalpha(a);return r

def footprint(product:Image.Image):
 # The actual visible bottom silhouette, not the rectangle bounding-box width.
 a=np.array(product.getchannel('A'))
 h,w=a.shape;rows=a[max(0,h-int(h*.12)):,:]
 xs=np.where(np.max(rows,axis=0)>60)[0]
 if len(xs)<2: xs=np.where(np.max(a,axis=0)>60)[0]
 if len(xs)<2:return (.5,max(4,w*.25))
 return ((xs[0]+xs[-1])/(2*w), max(3,(xs[-1]-xs[0])/2))

def elliptical(canvas_size,x,y,rx,ry,blur):
 m=Image.new('L',canvas_size,0);d=ImageDraw.Draw(m)
 d.ellipse((x-rx,y-ry,x+rx,y+ry),fill=255)
 return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m

def render(layers,images,canvas_size=(2000,2000),settings:ShadowControls|None=None,shadows=True):
 """Each layer: {id,x,y,w,h,z}; x/y are top-left; all original RGB remains from source image."""
 opt=settings or ShadowControls();W,H=canvas_size
 out=Image.new('RGBA',(W,H),(0,0,0,0))
 layers=sorted(layers,key=lambda l:l['z'])
 prepared=[]
 for l in layers:
  src=images[l['id']].crop()
  scaled=src.resize((int(round(l['w'])),int(round(l['h']))),Image.Resampling.LANCZOS)
  x=int(round(l['x']));y=int(round(l['y']))
  prepared.append((l,scaled,x,y))
 if shadows:
  for l,im,x,y in prepared:
   cx,rx=footprint(im);rx=max(5,rx)
   foot=y+im.height
   for opacity,blur,ratio,ry in [(opt.ambient_opacity,opt.ambient_blur,1.8,max(9,rx*.2)),(opt.contact_opacity,opt.contact_blur,1.1,max(3,rx*.075))]:
    mask=elliptical((W,H),x+im.width*cx+opt.offset_x*.5,foot-3,rx*ratio,ry,blur)
    out.alpha_composite(tint(mask,opt.ground_color,opacity))
 # Foreground silhouette only casts onto product pixels already behind it.
 already=Image.new('RGBA',(W,H),(0,0,0,0))
 for idx,(l,im,x,y) in enumerate(prepared):
  if shadows and idx and opt.overlap_opacity>0:
   fg=Image.new('L',(W,H),0);fg.paste(im.getchannel('A'),(x+opt.offset_x,y+opt.offset_y))
   fg=fg.filter(ImageFilter.GaussianBlur(opt.overlap_blur))
   rear=np.asarray(already.getchannel('A'),dtype=np.float32)/255
   cut=(np.asarray(fg,dtype=np.float32)*rear).astype('uint8')
   out.alpha_composite(tint(Image.fromarray(cut,'L'),opt.overlap_color,opt.overlap_opacity))
  out.alpha_composite(im,(x,y));already.alpha_composite(im,(x,y))
 return out
