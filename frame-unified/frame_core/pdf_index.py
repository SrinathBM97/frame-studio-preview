"""Read ALL 19 Nykaa chart pages without guessing which image owns which height.

PDF extracted height labels alone don't reliably identify the SKU printed inside
product photography. Keep page-level dimensions as unattributed until visual
product matching is verified.
"""
from __future__ import annotations
import re
import fitz
from pathlib import Path

CATEGORIES={3:'Lipsticks',4:'Lipsticks and lip colors',5:'Powders and palettes',6:'Concealers',7:'Compacts and eyeliners',8:'Eyeliners and makeup',9:'Makeup and bodycare',10:'Moisturizers',11:'Serums',12:'Shampoos and cleansers',13:'Bodycare',14:'Skincare',15:'Conditioners',16:'Haircare',17:'Haircare and styling',18:'Skincare and face wash',19:'All-products comparison'}

def index_chart(path:str|Path):
 rows=[]
 with fitz.open(path) as doc:
  for i,page in enumerate(doc,1):
   txt=page.get_text()
   nums=[int(x) for x in re.findall(r'\b(\d{2,4})\s+Pixels\b',txt,re.I)]
   rows.append({'page':i,'category_hint':CATEGORIES.get(i,'notes'),
     'unattributed_heights_px':sorted(set(nums)),'extracted_height_labels':len(nums),
     'status':'unattributed' if nums else 'no_product_heights',
     'note':'Text extraction does not establish which photographed SKU/pose owns each value'})
 return {'pages':len(rows),'page_evidence':rows,'sku_matching':'requires_verified_sku_pose_image_association'}
