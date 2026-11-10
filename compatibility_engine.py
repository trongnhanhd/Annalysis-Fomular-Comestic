"""Formula Intelligence V4.2: evidence-scoped, non-approval compatibility SCREENING.
Works with the V4.1 library; stdlib only. No invented legal or scientific limits.
"""
from __future__ import annotations
import csv, json, math
from collections import defaultdict
from pathlib import Path
from formula_group_service import Catalog as V41GroupCatalog

ROOT = Path(__file__).resolve().parent
DATA = ROOT/'data'

def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as fh:
        return list(csv.DictReader(fh))

def number(v, fallback=None):
    if v is None or v == '': return fallback
    try:
        n=float(v)
        if not math.isfinite(n): return fallback
        return n
    except (ValueError, TypeError): return fallback

class KnowledgeEngine:
    def __init__(self, data_dir=DATA):
        self.data_dir=Path(data_dir)
        self.ingredients=read_csv(self.data_dir/'ingredients.csv')
        self.properties=read_csv(self.data_dir/'ingredient_properties.csv')
        self.grades=read_csv(self.data_dir/'commercial_grade_models.csv')
        self.grade_components=read_csv(self.data_dir/'grade_component_models.csv')
        self.group_rules=read_csv(self.data_dir/'group_rules_source.csv')
        self.sources=read_csv(self.data_dir/'source_registry.csv')
        self.v41_group_catalog=V41GroupCatalog(ROOT/'ingredient_catalog_v4_1.json')
        self.by_name={p['inci_name_candidate'].lower():p for p in self.properties}
        self.by_id={p['ingredient_id']:p for p in self.properties}
        self.grade_by_id={g['grade_id']:g for g in self.grades}
        self.comp_by_grade=defaultdict(list)
        for c in self.grade_components: self.comp_by_grade[c['grade_id']].append(c)

    def search(self, query='', limit=30):
        q=query.lower().strip()
        return [{'ingredient_id':p['ingredient_id'],'inci':p['inci_name_candidate'],
                 'status':p['property_status'],'phase':p['phase'] or None,
                 'source_id':p['evidence_id'] or None}
                for p in self.properties if q in p['inci_name_candidate'].lower()][:max(0,min(limit,100))]

    def evaluate(self, scenario):
        """Input example: {'product_type':'Serum','physical_form':'aqueous',
           'pH':3.2,'water_phase_percent':45,'preservation_tested':False,
           'items':[{'inci':'Allantoin','percent':0.5}, ...]}.
           % is RAW MATERIAL percent, *not* INCI after trade-grade breakdown.
        """
        if not isinstance(scenario,dict): raise ValueError('scenario must be an object')
        rows=scenario.get('items',[])
        if not isinstance(rows,list): raise ValueError('items must be a list')
        if len(rows)>300: raise ValueError('too many formula items')
        phys=(scenario.get('physical_form') or 'unknown').lower()
        if phys not in ('anhydrous','aqueous','emulsion','unknown'): raise ValueError('invalid physical_form')
        ph=number(scenario.get('pH'))
        if ph is not None and not 0<=ph<=14: raise ValueError('pH outside 0..14')
        water_phase=number(scenario.get('water_phase_percent'))
        if water_phase is not None and not 0<=water_phase<=100: raise ValueError('invalid water_phase_percent')
        issues=[];group_totals=defaultdict(float); total=0.0; unknown_profiles=[]; recognized=[]; known_components=defaultdict(float);unresolved_grade_mass=0.0
        def add(code,severity,vi,inci=None,source=None,detail=None):
            issues.append({'code':code,'severity':severity,'message_vi':vi,'inci':inci,
                           'source_id':source,'details':detail or {}})
        solubilizer_present=bool(scenario.get('solubilizer_system_confirmed'))
        for idx,row in enumerate(rows):
            if not isinstance(row,dict): raise ValueError('each item must be an object')
            pct=number(row.get('percent'))
            if pct is None or pct<0 or pct>100: raise ValueError(f'Invalid % at index {idx}')
            total+=pct
            group_code=row.get('group_code') or 'UNCLASSIFIED'
            group_totals[group_code]+=pct
            if pct<=0: continue
            name=(row.get('inci') or row.get('inci_name_candidate') or '').strip()
            profile=self.by_id.get(row.get('ingredient_id','')) or self.by_name.get(name.lower())
            grade_id=row.get('grade_id')
            if grade_id:
                grade=self.grade_by_id.get(grade_id)
                if grade is None:
                    add('GRADE_UNKNOWN','review','Chưa có grade thương mại này trong thư viện; không được giả định thành phần.',name,None,{'grade_id':grade_id})
                    unresolved_grade_mass+=pct
                else:
                    for c in self.comp_by_grade.get(grade_id,[]):
                        comp=pct*float(c['mass_fraction'])
                        if c['component_inci']=='UNRESOLVED_REMAINDER':
                            unresolved_grade_mass+=comp
                        else:
                            known_components[c['component_inci']]+=comp
                    add('GRADE_COMPOSITION_UNRESOLVED','review','Chưa có toàn bộ INCI/COA của grade; phần còn lại chưa được nhận diện.',name,grade['source_id'],{'grade_id':grade_id,'unassigned_percent_of_finished_product':round(sum(pct*float(c['mass_fraction']) for c in self.comp_by_grade.get(grade_id,[]) if c['component_inci']=='UNRESOLVED_REMAINDER'),6)})
            if profile is None:
                unknown_profiles.append(name or f'item-{idx+1}')
                continue
            recognized.append(profile)
            if profile['property_status']=='not_assessed':
                unknown_profiles.append(profile['inci_name_candidate'])
                continue
            title=profile['inci_name_candidate']; eid=profile['evidence_id'] or None
            lo=number(profile['ph_min']); hi=number(profile['ph_max'])
            if lo is not None and hi is not None:
                if ph is None:
                    add('PH_NOT_PROVIDED','info','Chưa có pH đo được để đối chiếu điều kiện của grade.',title,eid)
                elif ph<lo or ph>hi:
                    add('PH_OUTSIDE_SUPPLIER_REFERENCE','review','pH nằm ngoài khoảng tham chiếu của tài liệu grade; yêu cầu thử ổn định.',title,eid,{'pH':ph,'min':lo,'max':hi,'reference_scope':profile['grade_scope']})
            if phys=='anhydrous' and profile['phase']=='water':
                add('ANHYDROUS_HYDROPHILIC_INGREDIENT','review','Nguyên liệu thiên về pha nước trong nền khan: cần chứng minh phân tán/độ ổn định.',title,eid)
            if phys=='aqueous' and profile['phase']=='oil' and not solubilizer_present:
                add('OIL_SOLUBLE_IN_AQUEOUS_ONLY_SYSTEM','review','Nguyên liệu tan dầu trong hệ nước chưa xác minh hệ hòa tan/phân tán.',title,eid)
            if title=='Allantoin' and water_phase and water_phase>0 and (not grade_id or title in [c['component_inci'] for c in self.comp_by_grade.get(grade_id,[])]):
                # Screening only. For a known grade use the modeled Allantoin component, never the full weighed grade.
                active_pct = pct if not grade_id else sum(pct*float(c['mass_fraction']) for c in self.comp_by_grade.get(grade_id,[]) if c['component_inci']==title)
                c=active_pct/water_phase*100
                threshold=number(profile['water_solubility_percent_25c'])
                if threshold is not None and c>threshold+1e-9:
                    add('ALLANTOIN_AQUEOUS_SOLUBILITY_SCREEN','review','Allantoin trên lượng nước vượt độ tan tham chiếu ở 25°C; không phải kết luận kết tinh.',title,eid,{'allantoin_relative_to_declared_water_percent':round(c,4),'reference_water_solubility_percent_at_25C':threshold,'does_not_account_for':'cosolvents, actual continuous phase, heating, kinetics'})
            if title=='Carbomer':
                add('CARBOMER_GRADE_NEEDS_PROCESS_DATA','review','Carbomer cần xác minh grade, pH, hệ điện giải và mức trung hòa để dự đoán độ nhớt.',title,eid)
        if unknown_profiles:
            add('PROPERTY_EVIDENCE_MISSING','info','Thiếu hồ sơ khoa học cho một số nguyên liệu; không tự suy ra tính tương thích.',None,None,{'count':len(unknown_profiles),'ingredients':unknown_profiles[:25]})
        if water_phase is None and phys in ('aqueous','emulsion'):
            add('WATER_PHASE_NOT_QUANTIFIED','info','Chưa có tỷ lệ pha nước, không thể kiểm tra độ tan theo pha.',None,None)
        if (phys in ('aqueous','emulsion') or (water_phase is not None and water_phase>0)) and not scenario.get('preservation_evidence'):
            add('PRESERVATION_ASSESSMENT_NEEDED','review','Cần đánh giá bảo vệ vi sinh theo rủi ro và thử nghiệm bảo quản thích hợp; có chất bảo quản không đồng nghĩa đã đạt.',None,'SRC-ISO11930')
        v41_group_result=None
        if scenario.get('product_id') is not None:
            try:
                v41_group_result=self.v41_group_catalog.validate_formula(int(scenario['product_id']),rows,scenario.get('ui_base_display_percent'))
                if not v41_group_result['passed_structural_check']:
                    add('V41_GROUP_TEMPLATE_REVIEW','review','Các nhóm hoặc số nguyên liệu chưa đáp ứng cấu trúc mẫu tham chiếu V4.1; đây không phải kết luận pháp lý.',None,None,{'v41_issues': [i for i in v41_group_result['issues'] if i['severity']=='error']})
            except (ValueError,TypeError,KeyError) as exc:
                add('V41_TEMPLATE_NOT_AVAILABLE','review','Không tìm được mẫu nhóm V4.1 tương ứng.',None,None,{'reason':str(exc)})
        if abs(total-100)>1e-6:
            add('MASS_BALANCE_FAILED','error','Tổng nguyên liệu cân thực không bằng 100%.',None,None,{'observed_total':round(total,6),'target':100})
        return {
            'engine_version':'4.2.0','product_type':scenario.get('product_type') or 'Chưa xác định',
            'raw_material_mass_percent':round(total,6), 'v41_group_validation':v41_group_result, 'primary_groups_raw_material_percent':dict(sorted((k,round(v,6)) for k,v in group_totals.items())),
            'known_trade_grade_inci_contributions_percent':{k:round(v,6) for k,v in sorted(known_components.items())},
            'trade_grade_unresolved_mass_percent':round(unresolved_grade_mass,6),
            'assessed_ingredient_count':len(recognized), 'items_count':len(rows),
            'scientific_compatibility_status':'REVIEW_REQUIRED' if any(i['severity'] in ('review','error') for i in issues) else 'NOT_ASSESSED',
            'regulatory_status':'NOT_ASSESSED', 'stability_status':'NOT_TESTED', 'manufacturing_approval':False,
            'issues':issues
        }

if __name__=='__main__':
    demo=json.loads((ROOT/'examples'/'serum_review.json').read_text(encoding='utf8'))
    print(json.dumps(KnowledgeEngine().evaluate(demo),ensure_ascii=False,indent=2))
