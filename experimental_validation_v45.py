"""V4.5 exploratory DoE and R&D observation assessment.

All input concentration priors are model assumptions; laboratory results are
measured observations with provenance. This module NEVER approves manufacture,
market authorization, safety or ISO compliance.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import itertools
import json
import math
import statistics
from typing import Any

from optimizer_v44 import solve_scenario, InputError


def canonical_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def finite_float(value: Any, name: str) -> float:
    try:
        if isinstance(value, bool): raise ValueError()
        v = float(value)
    except (ValueError, TypeError):
        raise InputError(f'{name}: phải là số hữu hạn')
    if not math.isfinite(v):
        raise InputError(f'{name}: phải là số hữu hạn')
    return v


def verify_protocol(protocol: dict) -> dict:
    if not isinstance(protocol, dict):
        raise InputError('protocol phải là object')
    metrics=protocol.get('metrics',[])
    if not isinstance(metrics,list) or not 1<=len(metrics)<=24:
        raise InputError('protocol.metrics: cần 1–24 chỉ tiêu')
    seen=set(); cleaned=[]
    for row in metrics:
        if not isinstance(row,dict):raise InputError('Mỗi metric phải là object')
        code=str(row.get('code','')).strip().upper()
        if not code or len(code)>48 or not all(c.isalnum() or c=='_' for c in code):
            raise InputError('metric.code không hợp lệ')
        if code in seen:raise InputError(f'Trùng chỉ tiêu: {code}')
        seen.add(code)
        kind=row.get('kind','numeric')
        if kind not in ('numeric','categorical'):raise InputError(f'{code}: kind không hợp lệ')
        points=row.get('timepoints_days',[0])
        if not isinstance(points,list) or not 1<=len(points)<=32 or any(type(x)!=int or x<0 or x>3650 for x in points) or len(set(points))!=len(points):
            raise InputError(f'{code}: timepoints_days không hợp lệ')
        unit=str(row.get('unit','')).strip()
        if kind=='numeric' and not unit:raise InputError(f'{code}: numeric phải khai báo đơn vị')
        lo=row.get('target_min'); hi=row.get('target_max')
        if lo is not None:lo=finite_float(lo,f'{code}.target_min')
        if hi is not None:hi=finite_float(hi,f'{code}.target_max')
        if lo is not None and hi is not None and lo>hi:raise InputError(f'{code}: min > max')
        allowed=row.get('acceptable_values',[])
        if kind=='categorical' and (not isinstance(allowed,list) or not allowed or any(not isinstance(a,str) or not a for a in allowed)):
            raise InputError(f'{code}: thiếu acceptable_values')
        if kind=='numeric' and (lo is None and hi is None):
            # The record is useful, but never considered compliant with an unknown specification.
            pass
        cleaned.append({'code':code, 'name':str(row.get('name') or code), 'kind':kind, 'unit':unit,
                        'timepoints_days':sorted(points), 'target_min':lo, 'target_max':hi,
                        'acceptable_values':allowed if kind=='categorical' else [],
                        'method':str(row.get('method','')), 'condition':str(row.get('condition','')),
                        'criteria_source':str(row.get('criteria_source','USER_DEFINED'))})
    return {'version':'4.5.0','metrics':cleaned,
            'guidance':'Tiêu chí R&D do người dùng thiết lập, không mặc nhiên là yêu cầu ISO hoặc quy định pháp lý.'}


def build_doe(data: dict, catalog=None) -> dict:
    """Controlled OFAT/factorial proposal: freeze all non-factor items at V4.4 representative.

    Factor deviations are compensated ONLY by a designated balance ingredient.
    Every proposed candidate is revalidated by V4.4 solver, not merely renormalized.
    """
    scenario=data.get('scenario')
    if not isinstance(scenario,dict):raise InputError('scenario phải là object')
    variables=data.get('variables',[])
    if not isinstance(variables,list) or not 1<=len(variables)<=3:raise InputError('Chọn 1–3 biến nguyên liệu')
    balance_id=str(data.get('balance_item_id',''))
    base=solve_scenario(scenario,catalog)
    if base.get('status')!='FEASIBLE':
        return {'version':'4.5.0','status':'BASE_NOT_FEASIBLE','base_result':base,
                'approved_for_manufacturing':False}
    initial={x['item_id']:x['percent_example'] for x in base['items']}
    if balance_id not in initial:raise InputError('balance_item_id không thuộc công thức')
    factorids=[]; levels=[]
    for v in variables:
        ident=str(v.get('item_id',''))
        if ident not in initial or ident==balance_id or ident in factorids:raise InputError('Danh sách biến không hợp lệ/trùng/bằng biến cân bằng')
        lo=finite_float(v.get('low'),f'{ident}.low'); hi=finite_float(v.get('high'),f'{ident}.high')
        if not (0<=lo<hi<=100):raise InputError(f'{ident}: cần 0 <= low < high <= 100')
        factorids.append(ident);levels.append((lo,hi))
    values=[tuple(round(initial[k],5) for k in factorids)] + list(itertools.product(*levels))
    results=[]; seen=set()
    for ix,vals in enumerate(values):
        key=tuple(round(float(v),5) for v in vals)
        if key in seen:continue
        seen.add(key)
        proposed=initial.copy()
        for k,v in zip(factorids,vals):proposed[k]=float(v)
        proposed[balance_id]=round(initial[balance_id]+sum(initial[k]-proposed[k] for k in factorids),5)
        candidate=deepcopy(scenario)
        candidate.pop('ambiguous_claims',None)
        candidate['claims']=deepcopy(scenario.get('claims',[])) + [
            {'basis':'raw_material','item_id':k,'percent':max(0,float(value))}
            for k,value in proposed.items()]
        if proposed[balance_id]<0:
            status='INFEASIBLE'; outcome={'status':status,'reason':'Nguyên liệu cân bằng âm'}
        else:
            outcome=solve_scenario(candidate,catalog)
            status=outcome['status']
        results.append({'candidate_id':f'DOE-{len(results)+1:03}',
                        'design_point':'BASELINE' if ix==0 else 'FACTORIAL',
                        'factor_values':{k:round(float(v),5) for k,v in zip(factorids,vals)},
                        'balance_item_id':balance_id,'balance_percent':proposed[balance_id],
                        'status':status,'composition_percent':proposed if status=='FEASIBLE' else None,
                        'rejection':None if status=='FEASIBLE' else outcome.get('reason','Ràng buộc công thức không có nghiệm'),
                        'diagnostics':outcome.get('diagnostic_single_constraint_removals',[]) if status!='FEASIBLE' else [],
                        'scenario_input':candidate if status=='FEASIBLE' else None,
                        'candidate_scenario_sha256':canonical_hash(candidate) if status=='FEASIBLE' else None})
    return {'version':'4.5.0','status':'PROPOSED_NOT_MEASURED','base_formula_hash':canonical_hash(scenario),
            'factor_count':len(factorids),'candidate_count':len(results),
            'feasible_count':sum(x['status']=='FEASIBLE' for x in results),'results':results,
            'caution':'Thiết kế thí nghiệm sàng lọc; tính ổn định, an toàn và hiệu năng vẫn phải đo và thẩm định.',
            'approved_for_manufacturing':False}


def classify_measurement(spec: dict, record: dict) -> str:
    if spec['kind']=='numeric':
        v=record.get('value_numeric')
        if v is None:return 'NO_RESULT'
        if spec['unit']!=record.get('unit'):return 'UNIT_MISMATCH'
        if spec['target_min'] is None and spec['target_max'] is None:return 'NO_SPECIFICATION'
        if spec['target_min'] is not None and v<spec['target_min']-1e-9:return 'OUT_OF_SPEC'
        if spec['target_max'] is not None and v>spec['target_max']+1e-9:return 'OUT_OF_SPEC'
        return 'WITHIN_USER_SPEC'
    if record.get('value_text') is None:return 'NO_RESULT'
    return 'WITHIN_USER_SPEC' if record['value_text'] in spec['acceptable_values'] else 'OUT_OF_SPEC'


def evaluate_study(study:dict,batches:list[dict],measurements:list[dict]) ->dict:
    protocol=study['protocol']; specs={r['code']:r for r in protocol['metrics']}
    current_ids={m['supersedes_measurement_id'] for m in measurements if m.get('supersedes_measurement_id')}
    active=[m for m in measurements if m['id'] not in current_ids]
    live_measured=[m for m in active if m['data_kind']=='MEASURED']
    demo_count=sum(m['data_kind']=='DEMO_SYNTHETIC' for m in active)
    expected={(b['id'],spec['code'],day) for b in batches for spec in specs.values() for day in spec['timepoints_days']}
    actual={(m['batch_id'],m['metric_code'],m['day']) for m in live_measured}
    completed=len(expected & actual)
    classified=[]
    for m in live_measured:
        spec=specs[m['metric_code']]
        classified.append({'measurement_id':m['id'],'batch_id':m['batch_id'],'metric_code':m['metric_code'],
                           'day':m['day'],'classification':classify_measurement(spec,m),
                           'value':m['value_numeric'] if spec['kind']=='numeric' else m['value_text'],
                           'unit':m['unit']})
    count_oos=sum(x['classification']=='OUT_OF_SPEC' for x in classified)
    count_unresolved=sum(x['classification'] in ('NO_SPECIFICATION','UNIT_MISMATCH','NO_RESULT') for x in classified)
    # Only claimed coverage per batch + metric + timepoint, never per individual replicate.
    if not batches:state='NO_BATCH'
    elif not live_measured:state='NO_MEASUREMENTS'
    elif count_oos:state='OUT_OF_USER_SPEC'
    elif completed<len(expected):state='INCOMPLETE'
    elif count_unresolved:state='NEEDS_SPECIFICATION'
    else:state='READY_FOR_RND_REVIEW'
    trends=[]
    for code,spec in specs.items():
        if spec['kind']!='numeric':continue
        for day in spec['timepoints_days']:
            matching=[m for m in live_measured if m['metric_code']==code and m['day']==day and m['unit']==spec['unit'] and m['value_numeric'] is not None]
            by_batch={}
            for m in matching:by_batch.setdefault(m['batch_id'],[]).append(float(m['value_numeric']))
            batch_means=[statistics.mean(vals) for vals in by_batch.values()]
            trends.append({'metric_code':code,'day':day,'independent_batches':len(batch_means),
                           'mean_of_batch_means':round(statistics.mean(batch_means),6) if batch_means else None,
                           'sample_sd_across_batches':round(statistics.stdev(batch_means),6) if len(batch_means)>=2 else None,
                           'eligible_for_exploratory_trend':len(batch_means)>=3,
                           'unit':spec['unit'],'claim':'OBSERVED_DATA_ONLY'})
    return {'version':'4.5.0','study_id':study['id'],'formula_sha256':study['formula_sha256'],
            'status':state,'batch_count':len(batches),'observations_measured':len(live_measured),
            'observations_demo_excluded':demo_count,
            'required_slots':len(expected),'completed_slots':completed,
            'data_coverage_percent':round(100*completed/len(expected),2) if expected else 0,
            'out_of_user_spec_count':count_oos,'not_interpretable_count':count_unresolved,
            'missing_slots':[{'batch_id':b,'metric_code':c,'day':d} for b,c,d in sorted(expected-actual)][:200],
            'classified_measurements':classified,'metric_trends':trends,
            'preservation_status':'NOT_AUTOMATICALLY_EVALUATED',
            'regulatory_status':'NOT_ASSESSED','stability_confirmation':'NOT_ESTABLISHED',
            'approved_for_manufacturing':False,
            'decision_note':'READY_FOR_RND_REVIEW chỉ nghĩa đủ dữ liệu đối chiếu quy cách người dùng; không phải chứng nhận an toàn, ổn định hay phép lưu hành.'}
