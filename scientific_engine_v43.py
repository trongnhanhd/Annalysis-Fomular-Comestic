"""V4.3 scientific supplier-grade evidence overlay for V4.2 screening.
It is not a validated stability, microbiology, efficacy, or regulatory engine.
"""
from __future__ import annotations
import csv, copy
from collections import defaultdict
from pathlib import Path
from compatibility_engine import KnowledgeEngine, number
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'

def readcsv(name):
    with (DATA/name).open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

class ScientificEngineV43:
    def __init__(self):
        self.v42=KnowledgeEngine()
        self.observations=readcsv('scientific_property_observations_v43.csv')
        self.grades=readcsv('supplier_grade_reference_v43.csv')
        self.coverage=readcsv('ingredient_evidence_coverage_v43.csv')
        self.grade_components=readcsv('grade_components_qualitative_v43.csv')
        self.by_grade={r['grade_id']:r for r in self.grades}
        self.observations_by_grade=defaultdict(list)
        for r in self.observations:self.observations_by_grade[r['grade_id']].append(r)
        self.components_by_grade=defaultdict(list)
        for r in self.grade_components:self.components_by_grade[r['grade_id']].append(r)

    def find_properties(self,inci='',grade_id='',limit=100):
        q=inci.casefold().strip()
        return [r for r in self.observations if (not q or q in r['inci_candidate'].casefold()) and (not grade_id or r['grade_id']==grade_id)][:min(max(limit,0),200)]

    def evaluate(self,scenario):
        if not isinstance(scenario,dict):raise ValueError('scenario must be an object')
        rows=scenario.get('items',[])
        if not isinstance(rows,list):raise ValueError('items must be an array')
        cleaned=copy.deepcopy(scenario)
        grade_tags=[]
        for i,item in enumerate(cleaned.get('items',[])):
            if not isinstance(item,dict):raise ValueError('item must be object')
            gid=item.get('grade_id')
            if gid in self.by_grade:
                grade_tags.append((i,gid))
                # The V4.2 parser doesn't know these grades. Do NOT let its unknown-grade
                # branch generate a false positive or pretend that the gross grade is pure INCI.
                item.pop('grade_id',None)
        result=self.v42.evaluate(cleaned)
        issues=result['issues']
        def add(code,severity,message,inci=None,grade_id=None,detail=None,src=None):
            issues.append({'code':code,'severity':severity,'message_vi':message,'inci':inci,'grade_id':grade_id,'source_id':src,'details':detail or {}})
        temp=number(scenario.get('process_temperature_c'))
        if temp is not None and not 0<=temp<=200:raise ValueError('process_temperature_c must be 0..200')
        intent=scenario.get('process_intent')
        if intent is not None and intent not in ('full_melt','cold_blend','unknown'):raise ValueError('Invalid process_intent')
        ph=number(scenario.get('pH'))
        for index,gid in grade_tags:
            grade=self.by_grade[gid]
            item=rows[index]
            pct=number(item.get('percent'))
            inc=item.get('inci','')
            src=grade['source_id']
            use_context=(grade.get('use_context') or '').lower()
            product_context=' '.join([str(scenario.get('product_type') or ''),str(scenario.get('product_profile') or '')]).lower().replace(' ','_')
            if gid=='S43-G-K4074' and not any(word in product_context for word in ('lipstick','son_thỏi','son_màu')):
                add('GRADE_PRODUCT_SCOPE_NOT_MATCHED','review','Grade nền son màu chỉ có khuyến nghị dùng cho lipstick; không áp cho mọi lip balm.',inc,gid,{'grade_scope':use_context},src)
            obslist=self.observations_by_grade[gid]
            for o in obslist:
                if o['property_key']=='recommended_use':
                    # The recommended 85–90% premix base applies only to lipstick context.
                    if gid=='S43-G-K4074' and not any(word in product_context for word in ('lipstick','son_thỏi','son_màu')):continue
                    lo,hi=number(o['value_min']),number(o['value_max'])
                    if lo is not None and hi is not None and pct is not None and (pct<lo-1e-9 or pct>hi+1e-9):
                        add('OUTSIDE_SUPPLIER_USE_REFERENCE','review','Tỷ lệ grade ngoài dải khuyến nghị nhà cung cấp; chưa phải lỗi pháp lý.',inc,gid,{'actual_percent_as_supplied':pct,'supplier_low':lo,'supplier_high':hi,'range_type':'supplier_grade_reference'},o['source_id'])
                if o['property_key']=='melting_point' and temp is not None and intent=='full_melt':
                    lo,hi=number(o['value_min']),number(o['value_max'])
                    if lo is not None and temp < lo:
                        add('PROCESS_TEMP_BELOW_GRADE_MELT_RANGE','review','Nhiệt độ giai đoạn làm chảy hoàn toàn thấp hơn đầu dưới của khoảng nóng chảy grade; cần kiểm tra quy trình.',inc,gid,{'processing_temp_c':temp,'grade_melting_point_c':[lo,hi]},o['source_id'])
                    elif hi is not None and temp < hi:
                        add('PROCESS_TEMP_WITHIN_GRADE_MELT_RANGE','info','Nhiệt độ đang nằm trong khoảng nóng chảy; khả năng chảy hoàn toàn còn cần xác minh.',inc,gid,{'processing_temp_c':temp,'grade_melting_point_c':[lo,hi]},o['source_id'])
                if o['property_key']=='pH_stability_max' and ph is not None:
                    hi=number(o['value_max'])
                    if hi is not None and ph>hi:
                        add('PH_ABOVE_SUPPLIER_GRADE_STABILITY_REFERENCE','review','pH lớn hơn giới hạn ổn định tham chiếu cho grade thương mại này.',inc,gid,{'pH':ph,'supplier_pH_max':hi},o['source_id'])
            if grade['composition_status'] in ('blend_components_qualitative_only','grade_family_not_a_unique_grade'):
                add('GRADE_COMPONENT_FRACTIONS_UNKNOWN','review','Biết danh mục thành phần của grade nhưng chưa biết tỷ phần; không được phân rã định lượng.',inc,gid,{'known_component_names':[r['component_inci_candidate'] for r in self.components_by_grade.get(gid,[])], 'can_compute_final_inci_percent':False},src)
            else:
                add('GRADE_ASSAY_COA_NOT_VERIFIED','info','Thông số grade tham chiếu chưa có COA lô để chứng minh hàm lượng thực.',inc,gid,{},src)
        result['engine_version']='4.3.0'
        result['v43_grade_evidence']=[{'grade_id':gid,'grade_name':self.by_grade[gid]['grade_name'],'source_url':self.by_grade[gid]['source_url']} for _,gid in grade_tags]
        result['v43_observation_count_used']=sum(len(self.observations_by_grade[gid]) for _,gid in grade_tags)
        result['v43_evidence_assessment']='GRADE_REFERENCES_WITH_GAPS' if grade_tags else 'NO_EXACT_GRADE_SPECIFIED'
        result['scientific_compatibility_status']='REVIEW_REQUIRED' if any(i['severity'] in ('error','review') for i in issues) else 'NOT_ASSESSED'
        result['regulatory_status']='NOT_ASSESSED'
        result['stability_status']='NOT_TESTED'
        result['manufacturing_approval']=False
        return result
