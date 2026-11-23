"""Independent *reject-only* creative QA.

Visual heuristics do not certify aesthetic excellence; they can veto obviously flat
arrangements. A human-reviewed commercial reference remains necessary for release.
"""
from __future__ import annotations
from statistics import pstdev


def judge_draft(scene:dict)->dict:
 layers=scene['layers'];qa=scene['qa'];m=qa['metrics']
 diagnostics=[]
 if not qa['pass']:diagnostics.append('geometry_or_labels_failed')
 feet=[(l['y']+l['h'])/2000 for l in layers]
 if pstdev(feet)<.045:diagnostics.append('weak_depth_staggering')
 occlusion=[x['occlusion'] for x in m['labels']]
 if sum(v>.015 for v in occlusion)<2:diagnostics.append('too_few_meaningful_layer_interactions')
 if m['group_width']>.72:diagnostics.append('wide_spread_packshot_row')
 if m['group_height']<.61:diagnostics.append('insufficient_vertical_rhythm')
 # This is not an image model. Do not claim it understands taste, brand, styling, or perspective.
 return {'creative_approved':False,'automatic_visual_gate':'REJECT' if diagnostics else 'REVIEW_REQUIRED',
  'diagnostics':diagnostics,'limitation':'Reference-aware human visual approval is not automated; no numerical score can confer Photoshop-grade status'}
