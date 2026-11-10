#!/usr/bin/env python3
"""Preliminary cosmetic formulation screen; not a legal approval engine.
Usage: python check_formula.py --market VN --category leave_on --purpose preservative --inci Phenoxyethanol --pct 1.2
Run with regulatory_rules.json in same directory.
"""
import argparse,json,sys
from pathlib import Path
from datetime import date
p=argparse.ArgumentParser()
p.add_argument('--market',required=True,choices=['EU','US','VN','ASEAN','KR','CN'])
p.add_argument('--category',required=True,help='product_scope e.g. leave_on, rinse_off, other_cosmetics, otc_sunscreen_drug')
p.add_argument('--purpose',default='preservative')
p.add_argument('--inci',required=True)
p.add_argument('--pct',type=float,required=True)
p.add_argument('--basis',default='ingredient',help='ingredient, as_benzoic_acid, retinol_equivalent, mixture_3_to_1 ...')
p.add_argument('--date',default='2026-11-09')
a=p.parse_args()
if a.pct<0: sys.exit('pct must be >= 0')
data=json.loads((Path(__file__).parent/'regulatory_rules.json').read_text(encoding='utf-8'))
rows=[r for r in data['regulatory_rules'] if r['market']==a.market and r['inci_name'].lower()==a.inci.lower()
      and (r['purpose']==a.purpose or r['purpose']=='any' or a.purpose=='any')
      and (not r['effective_from'] or r['effective_from']<=a.date)
      and (not r['effective_to'] or r['effective_to']>=a.date)]
# deliberately conservative: only wildcard or exact scope; no fuzzy matching
matching=[r for r in rows if r['product_scope'] in ('all_cosmetics',a.category)]
if a.market=='US' and a.category=='otc_sunscreen_drug' and a.purpose=='otc_sunscreen_active':
    matching=[r for r in rows if r['product_scope']=='otc_sunscreen_drug']
if not matching:
    result={'status':'NEEDS_LEGAL_REVIEW','explanation':'No exactly matching verified source rule. This does not imply allowed or prohibited.'}
elif any(r['rule_type'] in ('PROHIBITED_INTENTIONAL_USE','NOT_ALLOWED_FOR_PURPOSE','REMOVED_FROM_OTC_MONOGRAPH') for r in matching):
    result={'status':'RESTRICTED_OR_NOT_AUTHORIZED','rule_ids':[r['rule_id'] for r in matching]}
elif len(matching)!=1:
    result={'status':'NEEDS_LEGAL_REVIEW','explanation':'Multiple matching rules require product context.', 'rule_ids':[r['rule_id'] for r in matching]}
else:
    r=matching[0]
    if r['rule_type']!='MAX' or r['max_pct_w_w'] is None:
        result={'status':'NEEDS_LEGAL_REVIEW','rule_id':r['rule_id']}
    elif r['concentration_basis']!=a.basis:
        result={'status':'NEEDS_BASIS_CONVERSION','required_basis':r['concentration_basis'],'rule_id':r['rule_id']}
    elif not r['auto_checkable'] or r['limit_group_id'] or r['additional_conditions'] or r['label_warning']:
        result={'status':'MANUAL_CONDITIONS_REQUIRED','threshold_pct':r['max_pct_w_w'],'above_numeric_threshold':a.pct>r['max_pct_w_w'],'rule_id':r['rule_id']}
    else:
        result={'status':'EXCEEDS_NUMERIC_MAX' if a.pct>r['max_pct_w_w'] else 'NOT_ABOVE_NUMERIC_MAX', 'limit_pct':r['max_pct_w_w'],'rule_id':r['rule_id']}
result.update({'market':a.market,'inci':a.inci,'product_scope':a.category,'input_pct':a.pct,'disclaimer':'Never use as regulatory approval; verify version, function, category, warnings, aggregated ingredients and local adoption.'})
print(json.dumps(result,ensure_ascii=False,indent=2))
