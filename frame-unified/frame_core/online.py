"""Search/verification interface: only VERIFIED physical product dimensions qualify.

An actual search backend must be configured by the deployed service. The user's
browser should NEVER be asked for API credentials. Product listing existence alone
is NOT a dimension match; retail shipping dimensions are explicitly rejected.
"""
from __future__ import annotations
from dataclasses import dataclass
import json,re
from urllib.parse import urlparse
from .evidence import validate_online_dimension, Evidence

@dataclass
class ResearchResult:
 sku:str
 pose:str
 status:str
 url:str|None=None
 height_mm:float|None=None
 reason:str|None=None

def parse_height_from_product_schema(page_json_ld:str,sku:str,pose:str,url:str):
 """Only schema.org Product.height counts, with unitCode MMT/CMT or explicit unitText."""
 try:obj=json.loads(page_json_ld)
 except (TypeError,ValueError):return Evidence(status='unknown',warning='No usable JSON-LD')
 blocks=obj if isinstance(obj,list) else obj.get('@graph',[obj]) if isinstance(obj,dict) else []
 for b in blocks:
  if not isinstance(b,dict):continue
  typ=b.get('@type','');types=[typ] if isinstance(typ,str) else typ
  if 'Product' not in types:continue
  if not b.get('name') or sku.lower() not in b['name'].lower():continue
  measurement=b.get('height')
  if not isinstance(measurement,dict):continue
  value=measurement.get('value');unit=measurement.get('unitCode',measurement.get('unitText',''))
  if str(unit).lower() not in ('mmt','mm','cmt','cm'):continue
  try:v=float(value)*(10 if str(unit).lower() in ('cm','cmt') else 1)
  except (TypeError,ValueError):continue
  return validate_online_dimension({'sku':sku,'pose':pose,'height_mm':v,'dimension_type':'product','url':url},sku,pose)
 return Evidence(status='unknown',warning='Matching product schema has no supported physical height')

class SearchProvider:
 def search(self,query:str)->list[dict]:
  raise NotImplementedError('Server-side search provider not connected. Do not fake online research.')

def research_product(sku:str,pose:str,provider:SearchProvider|None):
 if provider is None:return Evidence(status='unknown',warning='Online search backend is not connected')
 for hit in provider.search(sku+' product dimensions height mm'):
  url=hit.get('url','')
  if urlparse(url).scheme!='https':continue
  result=parse_height_from_product_schema(hit.get('json_ld',''),sku,pose,url)
  if result.status=='online_verified':return result
 return Evidence(status='unknown',warning='Search found no trustworthy same-SKU physical dimensions')
