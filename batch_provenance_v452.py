"""Freeze DoE candidate and weigh-sheet linkage. No guessed measurements."""
from __future__ import annotations
from math import isfinite
from experimental_validation_v45 import canonical_hash, build_doe, finite_float
from optimizer_v44 import solve_scenario, InputError
from formula_group_service import Catalog


def freeze_candidates(scenario,design=None):
    if design is None:
        solved=solve_scenario(scenario,Catalog() if scenario.get('product_id') else None)
        if solved.get('status')!='FEASIBLE':raise InputError('Không thể lưu ứng viên BASELINE khi công thức không khả thi')
        composition={i['item_id']:float(i['percent_example']) for i in solved['items']}
        result=[dict(candidate_id='BASELINE',composition_percent=composition,
                     design={'design_point':'BASELINE','source':'optimizer_v44'})]
    else:
        if not isinstance(design,dict) or canonical_hash(design.get('scenario'))!=canonical_hash(scenario):
            raise InputError('Thiết kế DoE phải cùng snapshot công thức với nghiên cứu')
        doe=build_doe(design,Catalog() if scenario.get('product_id') else None)
        result=[dict(candidate_id=c['candidate_id'],composition_percent=c['composition_percent'],
                     design={'design_point':c['design_point'],'factor_values':c['factor_values'],
                             'balance_item_id':c['balance_item_id']}) for c in doe.get('results',[])
                if c['status']=='FEASIBLE']
        if not result:raise InputError('Không có phương án DoE khả thi để khóa')
    for row in result:
        row['candidate_sha256']=canonical_hash({'scenario_sha256':canonical_hash(scenario),
            'candidate_id':row['candidate_id'],'composition_percent':row['composition_percent']})
    return result


def verify_batch_provenance(candidate,body):
    weights=body.get('actual_weights_g');lots=body.get('raw_material_lots');process=body.get('process')
    weighed_by=str(body.get('weighed_by','')).strip()
    if not isinstance(weights,dict) or not isinstance(lots,dict):
        raise InputError('Cần bảng khối lượng cân thực và số lô nguyên liệu theo item_id')
    if not isinstance(process,dict) or not str(process.get('procedure_ref','')).strip() or not weighed_by:
        raise InputError('Cần quy trình (procedure_ref) và người thực cân (weighed_by)')
    target=candidate['composition_percent']
    if set(weights)!=set(target) or set(lots)!=set(target):
        raise InputError('Danh sách item_id phải khớp chính xác phương án DoE')
    clean={k:finite_float(v,k+'.actual_weight_g') for k,v in weights.items()}
    if any(v<0 for v in clean.values()) or sum(clean.values())<=0:
        raise InputError('Khối lượng cân phải không âm và tổng lớn hơn 0')
    if any(not isinstance(v,str) or not v.strip() for v in lots.values()):
        raise InputError('Mỗi nguyên liệu phải có mã lô hoặc ký hiệu truy vết')
    total=sum(clean.values())
    deviation=max(abs(100*clean[k]/total-float(target[k])) for k in target)
    status='LINKED_DEVIATED' if deviation>0.1 else 'LINKED_MATCHED'
    return dict(candidate_id=candidate['candidate_id'],candidate_sha256=candidate['candidate_sha256'],
        actual_weights_g=clean,raw_material_lots={k:v.strip() for k,v in lots.items()},
        process=process,weighed_by=weighed_by,deviation_max_pp=round(deviation,5),traceability_status=status)


def apply_traceability_gate(report,batches):
    linked=sum(b.get('traceability_status') in ('LINKED_MATCHED','LINKED_DEVIATED') for b in batches)
    missing=[b['id'] for b in batches if b.get('traceability_status') not in ('LINKED_MATCHED','LINKED_DEVIATED')]
    report['traceability']={'linked_batches':linked,'total_batches':len(batches),
                            'unlinked_batch_ids':missing,
                            'all_batches_linked':bool(batches) and not missing}
    deviations=[b['id'] for b in batches if b.get('traceability_status')=='LINKED_DEVIATED']
    report['traceability']['deviated_batch_ids']=deviations
    report['traceability']['review_readiness']=('INCOMPLETE' if missing else
        ('DEVIATION_REVIEW_REQUIRED' if deviations else ('COMPLETE' if batches else 'NO_BATCH')))
    report['eligible_for_model_training']=False
    report['approved_for_manufacturing']=False
    return report
