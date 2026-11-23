"""Non-destructive alpha mask operations with zero defaults and undoable brush strokes.
Never changes product RGB or its original file; operates on a separate grayscale matte.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from PIL import Image,ImageDraw,ImageFilter

@dataclass
class MaskSettings:
 feather_px:float=0
 smooth_px:float=0
 expand_px:int=0
 contract_px:int=0

@dataclass
class BrushStroke:
 x:int;y:int;radius:int;mode:str # 'restore' or 'erase'

class MaskEditor:
 def __init__(self,mask:Image.Image):
  self.base=mask.convert('L').copy()
  self.strokes:list[BrushStroke]=[]
  self.settings=MaskSettings()
 def stroke(self,x:int,y:int,radius:int,mode:str):
  if mode not in ('restore','erase'):raise ValueError('Brush mode must be restore/erase')
  if radius<1 or radius>400:raise ValueError('Invalid radius')
  self.strokes.append(BrushStroke(x,y,radius,mode))
 def undo(self):
  if self.strokes:self.strokes.pop()
 def reset(self):
  self.settings=MaskSettings();self.strokes.clear()
 def get(self):
  a=self.base.copy()
  if self.settings.expand_px>0:
   r=min(24,int(self.settings.expand_px));a=a.filter(ImageFilter.MaxFilter(2*r+1))
  if self.settings.contract_px>0:
   r=min(24,int(self.settings.contract_px));a=a.filter(ImageFilter.MinFilter(2*r+1))
  if self.settings.smooth_px>0:
   a=a.filter(ImageFilter.MedianFilter(2*min(10,int(self.settings.smooth_px))+1))
  if self.settings.feather_px>0:
   a=a.filter(ImageFilter.GaussianBlur(min(40,self.settings.feather_px)))
  # Brush restore reads original alpha from the unmodified base matte; no invented silhouette.
  for s in self.strokes:
   sel=Image.new('L',a.size,0);d=ImageDraw.Draw(sel)
   d.ellipse((s.x-s.radius,s.y-s.radius,s.x+s.radius,s.y+s.radius),fill=255)
   a.paste(self.base if s.mode=='restore' else Image.new('L',a.size,0),mask=sel)
  return a
