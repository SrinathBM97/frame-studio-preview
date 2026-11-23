#!/usr/bin/env python3
"""Audit supplied Nykaa chart text (page-height evidence), not visual SKU recognition.
An exact match is only valid with independent SKU+pose verification.
"""
import fitz, json, re, argparse, pathlib
p=argparse.ArgumentParser();p.add_argument('pdf',type=pathlib.Path);p.add_argument('--output',required=True);args=p.parse_args()
doc=fitz.open(args.pdf)
entries=[]
for i,page in enumerate(doc):
    heights=[int(n) for n in re.findall(r'(\d{3,4})\s+Pixels',page.get_text())]
    entries.append({'page':i+1,'observed_reference_heights_px':heights,
     'contains_1200_anchor':1200 in heights,'source':'supplied-nykaa-chart','identifies_sku':False})
result={'pages':len(doc),'source_pdf':args.pdf.name,'source_limitation':'Text layer contains reference heights and category, but not a reliable SKU-to-column map. Manual visual SKU/pose verification still required.', 'pages_index':entries}
pathlib.Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf8')
print('PDF pages:',len(doc),'page 6 has 1036:',1036 in entries[5]['observed_reference_heights_px'])
