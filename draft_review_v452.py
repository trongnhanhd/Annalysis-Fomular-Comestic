"""Read-only preflight for Vietnamese R&D form editor.

Not a safety approval, legal authorization, stability finding or validation of
commercial-grade assay. Scientific and regulatory status remain unresolved.
"""
from __future__ import annotations
from typing import Any
from experimental_validation_v45 import verify_protocol
from optimizer_v44 import solve_scenario, InputError
from formula_group_service import Catalog


def review_draft(payload: dict[str, Any]) -> dict[str, Any]:
    scenario = payload.get('scenario')
    if not isinstance(scenario, dict) or not isinstance(scenario.get('items'), list):
        raise InputError('scenario.items: cần danh sách nguyên liệu')
    protocol = payload.get('protocol')
    if protocol is not None:
        verify_protocol(protocol)
    unknown = [str(x.get('item_id','')) for x in scenario['items']
               if not x.get('composition',{}).get('complete',False)]
    ambiguous = bool(scenario.get('ambiguous_claims'))
    result = solve_scenario(scenario, Catalog() if scenario.get('product_id') is not None else None)
    notes = []
    if unknown:
        notes.append(f'{len(unknown)} nguyên liệu có thành phần grade chưa định lượng; không thể xác định đầy đủ % INCI cuối cùng.')
    if ambiguous:
        notes.append('Claim có nhiều cách hiểu; cần xác minh trước khi tạo nghiên cứu/mẻ thử.')
    if result.get('status') != 'FEASIBLE':
        notes.append('Các ràng buộc hiện tại không tạo được công thức 100% khả thi.')
    status = 'REQUIRES_CLAIM_RESOLUTION' if ambiguous else ('FEASIBLE' if result.get('status') == 'FEASIBLE' else 'INFEASIBLE')
    return {
        'version':'4.5.2','status':status,
        'raw_material_total_percent':result.get('raw_material_total_percent'),
        'group_results':result.get('groups',[]) if result.get('status')=='FEASIBLE' else [],
        'unresolved_grade_item_ids':unknown,
        'notes':notes,
        'technical_result':result,
        'approved_for_manufacturing':False,
        'stability_confirmation':'NOT_ESTABLISHED',
        'regulatory_status':'NOT_ASSESSED'
    }
