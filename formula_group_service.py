"""Reference-only group assignment and validation for Web App R&D (stdlib).
No regulatory permission, safety claim or supplier-grade inference is made.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import json
import math

ROOT=Path(__file__).resolve().parent

class ValidationError(Exception):pass

class Catalog:
    def __init__(self,path=ROOT/'ingredient_catalog_v4_1.json'):
        self.db=json.loads(Path(path).read_text(encoding='utf-8'))
        self.ingredients={x['ingredient_id']:x for x in self.db['ingredients']}
        self.members={(x['ingredient_id'],x['group_code']) for x in self.db['ingredient_groups']}
        self.product_rules={(int(x['product_id']),x['group_code']):x for x in self.db['group_rules']}
        self.products={int(x['product_id']):x for x in self.db['product_types']}

    def suggested_candidates(self, product_id, group_code, limit=100):
        if (product_id,group_code) not in self.product_rules:raise ValidationError('unknown_template_group')
        return [x for x in self.db['ingredient_groups'] if x['group_code']==group_code][:limit]

    def validate_formula(self,product_id,raw_items,ui_base_display_percent=None):
        """raw_items = [{ingredient_id,group_code,pct,grade_id?}].
        The UI 100% base placeholder is NEVER added to mass balance.
        Every physical material percentage is counted once, including a real selected base.
        """
        if product_id not in self.products:raise ValidationError('unknown_product_type')
        issues=[];by_group=defaultdict(float);qty=defaultdict(int);total=0.0
        for i,row in enumerate(raw_items):
            iid=row.get('ingredient_id'); group=row.get('group_code')
            pct=row.get('percent')
            if not isinstance(pct,(int,float)) or not math.isfinite(pct) or pct<0:
                issues.append({'severity':'error','code':'INVALID_PERCENT','item_index':i});continue
            if (product_id,group) not in self.product_rules:
                issues.append({'severity':'error','code':'GROUP_NOT_IN_TEMPLATE','item_index':i});continue
            if iid and iid not in self.ingredients:
                issues.append({'severity':'error','code':'UNKNOWN_INGREDIENT','item_index':i});continue
            if iid and (iid,group) not in self.members:
                issues.append({'severity':'warning','code':'INGREDIENT_GROUP_NOT_PREMAPPED','item_index':i})
            if pct==0:continue
            by_group[group]+=float(pct);qty[group]+=1;total+=float(pct)
            if row.get('grade_id'):
                issues.append({'severity':'warning','code':'GRADE_COMPOSITION_NEEDS_COA','item_index':i})
        for (p,g),rule in self.product_rules.items():
            if p!=product_id:continue
            n=qty.get(g,0);summ=by_group.get(g,0)
            lo=float(rule.get('min_percent') or 0);hi=float(rule.get('max_percent') or 100)
            low_n=int(rule.get('min_ingredients') or 0);hi_n=int(rule.get('max_ingredients') or 99)
            # Base selector is not a duplicate virtual mass; a selected base raw material IS real mass.
            if n<low_n:
                issues.append({'severity':'error','code':'REQUIRED_GROUP_MISSING','group':g,'required_min':low_n})
            if n>hi_n:
                issues.append({'severity':'error','code':'INGREDIENT_COUNT_EXCEEDS','group':g,'allowed_max':hi_n})
            if n and (summ < lo -1e-8 or summ > hi+1e-8):
                issues.append({'severity':'error','code':'GROUP_OUTSIDE_SCREENSHOT_REFERENCE_RANGE','group':g,'value':round(summ,6),'min':lo,'max':hi})
        if abs(total-100.0)>1e-6:
            issues.append({'severity':'error','code':'MASS_BALANCE_FAILED','mass_percent':round(total,6),'expected':100.0})
        if ui_base_display_percent is not None and ui_base_display_percent != 100:
            issues.append({'severity':'info','code':'UI_BASE_DISPLAY_IGNORED','display_percent':ui_base_display_percent})
        # No grade deconvolution or chemical INCI totals without a verified grade composition.
        issues.append({'severity':'info','code':'MARKET_LEGAL_CHECK_NOT_PERFORMED'})
        return {'product_id':product_id,'raw_material_total_percent':round(total,6),
                'group_percentages':dict(sorted((g,round(v,6)) for g,v in by_group.items())),
                'group_ingredient_counts':dict(sorted(qty.items())),
                'counted_ui_base_placeholder':False,
                'passed_structural_check':not any(x['severity']=='error' for x in issues),
                'approved_for_manufacture':False,'issues':issues}

if __name__=='__main__':
    demo=json.loads((ROOT/'sample_lip_balm_scenario.json').read_text(encoding='utf-8'))
    result=Catalog().validate_formula(demo['product_id'],demo['items'],demo['ui_base_display_percent'])
    print(json.dumps(result,indent=2,ensure_ascii=False))
