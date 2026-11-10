"""Gợi ý nồng độ minh họa thỏa mọi ràng buộc + giải thích. KHÔNG phải ước tính hàm lượng.

Dùng cùng mô hình LP của engine (thứ tự INCI, ngưỡng 1%, % công bố, giới hạn đã áp).
Mặc định: chọn điểm gần điểm giữa của từng khoảng khả thi nhất.
Nếu có % tối ưu đã xác minh (preferred), mục tiêu chuyển sang giá trị đó.
estimated_pct luôn để null.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from engine import AnalysisRequest, _analysis

TOLERANCE = 1e-6
PREFERRED_WEIGHT = 1000.0
CONSTRAINED_WIDTH = 5.0  # khoảng rộng hơn ngưỡng này (điểm %) được coi là chưa xác định


def _best_partition(captured: dict, preferred: dict[int, float]):
    n, total_dim = captured['n'], captured['total_dim']
    A_eq, b_eq = captured['A_eq'], captured['b_eq']
    best = None
    for cutoff, (A_ub, b_ub, bounds) in captured['feasible']:
        target = np.array([(lo + hi) / 2 for lo, hi in bounds[:n]])
        for i, value in preferred.items():
            target[i] = value
        nv = total_dim + n
        rows, vals = [], []
        if A_ub is not None:
            for row, val in zip(A_ub, b_ub):
                rows.append(np.concatenate([row, np.zeros(n)]))
                vals.append(val)
        for i in range(n):
            up = np.zeros(nv); up[i] = 1; up[total_dim + i] = -1
            down = np.zeros(nv); down[i] = -1; down[total_dim + i] = -1
            rows += [up, down]
            vals += [target[i], -target[i]]
        c = np.zeros(nv)
        c[total_dim:] = 1
        for i in preferred:
            c[total_dim + i] = PREFERRED_WEIGHT
        res = linprog(
            c,
            A_ub=np.array(rows), b_ub=np.array(vals),
            A_eq=np.hstack([A_eq, np.zeros((A_eq.shape[0], n))]), b_eq=b_eq,
            bounds=list(bounds) + [(0, None)] * n,
            method='highs',
        )
        if res.success and (best is None or res.fun < best[0] - 1e-9):
            best = (res.fun, cutoff, res.x[:total_dim])
    return best


def _conflict_sources(req: AnalysisRequest) -> list[dict]:
    """Thử bỏ từng nguồn ràng buộc; nguồn nào bỏ đi thì khôi phục khả thi là nguồn mâu thuẫn."""
    culprits = []

    def feasible_without(update: dict) -> bool:
        try:
            return _analysis(req.model_copy(update=update))['status'] == 'feasible'
        except ValueError:
            return False

    for name in req.known_pct:
        if feasible_without({'known_pct': {k: v for k, v in req.known_pct.items() if k != name}}):
            culprits.append({'source': 'known_pct', 'ingredient': name, 'detail': f'Giá trị công bố {req.known_pct[name].value}% (nguồn: {req.known_pct[name].source})'})
    for name in req.bounds:
        if feasible_without({'bounds': {k: v for k, v in req.bounds.items() if k != name}}):
            b = req.bounds[name]
            culprits.append({'source': 'bounds', 'ingredient': name, 'detail': f'Khoảng {b.min_pct}–{b.max_pct}% ({b.kind}: {b.source})'})
    for name in req.declared_concentrations:
        if feasible_without({'declared_concentrations': {k: v for k, v in req.declared_concentrations.items() if k != name}}):
            culprits.append({'source': 'declared_concentrations', 'ingredient': name, 'detail': 'Nhãn định lượng đã khai báo'})
    if req.apply_catalog_limits and feasible_without({'apply_catalog_limits': False}):
        culprits.append({'source': 'apply_catalog_limits', 'ingredient': None, 'detail': 'Giới hạn pháp lý tuyển chọn đang bật'})
    return culprits


def _explain_infeasible(req: AnalysisRequest, analysis: dict) -> dict:
    culprits = _conflict_sources(req)
    if culprits:
        contradictions = [f"Mâu thuẫn: {c['ingredient'] or c['source']} — {c['detail']}. Bỏ nguồn này thì công thức khả thi trở lại." for c in culprits]
        needed = ['Kiểm tra lại các giá trị công bố/khoảng đã nhập có cùng đơn vị, cùng nền và đúng tên INCI.']
    else:
        contradictions = ['Không tìm được một nguồn đơn lẻ gây mâu thuẫn; nguyên nhân có thể nằm ở tổng 100% hoặc thứ tự INCI theo ngưỡng 1%.']
        needed = ['Kiểm tra danh sách INCI có đủ và đúng thứ tự nhãn; kiểm tra tổng các cận tối thiểu.']
    return {
        'feasible': False,
        'contradictions': contradictions,
        'assumptions': [],
        'undetermined': [],
        'data_needed': needed,
        'issues': analysis.get('issues', []),
    }


def _explain_feasible(req: AnalysisRequest, analysis: dict, comp: dict) -> dict:
    results = analysis['results']
    undetermined, explained = [], []
    for r in results:
        width = r['max_pct'] - r['min_pct']
        value = r['suggested_pct']
        at_min = abs(value - r['min_pct']) <= 1e-4
        at_max = abs(value - r['max_pct']) <= 1e-4
        drivers = list(r['constraints'])
        if width <= TOLERANCE:
            status = 'fixed'
            why = 'Giá trị cố định bởi ràng buộc đã nhập.'
        elif width < CONSTRAINED_WIDTH:
            status = 'constrained'
            why = 'Khoảng hẹp.'
        else:
            status = 'undetermined'
            why = 'Khoảng rộng, chưa đủ dữ liệu để xác định.'
        if status != 'fixed':
            if at_min and not at_max:
                why += ' Đặt ở cận dưới để nhường phần còn lại cho các thành phần khác (tổng 100%).'
            elif at_max and not at_min:
                why += ' Đặt ở cận trên để đủ tổng 100%.'
            else:
                why += f" Chọn gần điểm {'mục tiêu đã xác minh' if comp['objective'] == 'preferred' else 'giữa khoảng'}."
        needs = []
        if status == 'undetermined':
            needs.append('Công bố % đã xác minh (known_pct) hoặc khoảng nhà cung cấp/pháp lý (bounds) để thu hẹp khoảng.')
            undetermined.append(r['ingredient'])
        if not r['research_evidence']:
            needs.append('Chưa có nghiên cứu nồng độ trong kho; cần tài liệu có nguồn.')
        if not r['regulatory_references']:
            needs.append('Chưa có giới hạn pháp lý đã kiểm chứng cho thị trường này.')
        explained.append({'ingredient': r['ingredient'], 'status': status, 'why': why, 'drivers': drivers, 'data_needed': needs})
        r['explanation'] = explained[-1]

    assumptions = []
    if req.max_unlisted_pct == 0:
        assumptions.append('Danh sách INCI được giả định mô tả đủ 100% khối lượng (không có thành phần ẩn).')
    else:
        assumptions.append(f'Cho phép tối đa {req.max_unlisted_pct}% thành phần không ghi nhãn.')
    if req.market != 'CN':
        assumptions.append('Thành phần trên 1% được xếp theo thứ tự INCI; thành phần dưới 1% không cần đúng thứ tự.')
    if not req.known_pct:
        assumptions.append('Không có % công bố nào: mọi khoảng chỉ dựa trên ràng buộc chung nên rất rộng.')
    if not req.apply_catalog_limits:
        assumptions.append('Giới hạn pháp lý tuyển chọn chưa được áp dụng.')

    data_needed = []
    if undetermined:
        data_needed.append(f"Thu hẹp {len(undetermined)} thành phần chưa xác định: {', '.join(undetermined)}.")
    if comp['legal_limits_not_checked']:
        data_needed.append(f"Giới hạn pháp lý cho {len(comp['legal_limits_not_checked'])} thành phần chưa được kiểm tra.")
    if not req.known_pct:
        data_needed.append('Công bố % đã xác minh cho các thành phần hoạt tính (kèm nguồn).')

    fixed_sum = sum(r['suggested_pct'] for r, e in zip(results, explained) if e['status'] == 'fixed')
    contradictions = []
    if fixed_sum > 100 - 1e-6:
        contradictions.append('Các giá trị cố định đã chiếm 100%; không còn chỗ cho thành phần khác.')
    return {
        'feasible': True,
        'contradictions': contradictions,
        'assumptions': assumptions,
        'undetermined': undetermined,
        'fixed_sum_pct': round(float(fixed_sum), 6),
        'data_needed': data_needed,
        'issues': [],
    }


def analyze_with_suggestion(payload: dict | AnalysisRequest, preferred: dict[str, float] | None = None) -> dict:
    """Phân tích khoảng khả thi + gợi ý điểm thỏa ràng buộc + giải thích."""
    req = payload if isinstance(payload, AnalysisRequest) else AnalysisRequest.model_validate(payload)
    captured: dict = {}
    analysis = _analysis(req, captured)
    if analysis['status'] != 'feasible':
        analysis['explanation'] = _explain_infeasible(req, analysis)
        return analysis

    results = analysis['results']
    names = [r['ingredient'] for r in results]
    preferred_idx = {names.index(k): float(v) for k, v in (preferred or {}).items() if k in names}
    best = _best_partition(captured, preferred_idx)
    if best is None:
        analysis['suggested_composition'] = None
        analysis['warnings'].append('Không tìm được phương án gợi ý thỏa ràng buộc.')
        analysis['explanation'] = _explain_infeasible(req, analysis)
        return analysis

    n = captured['n']
    _, cutoff, x = best
    within = True
    for r, value in zip(results, x[:n]):
        value = float(value)
        ok = r['min_pct'] - TOLERANCE <= value <= r['max_pct'] + TOLERANCE
        within = within and ok
        r['suggested_pct'] = round(value, 6)

    applied = {item['inci'].casefold() for item in captured['applied_catalog_limits']}
    comp = {
        'kind': 'illustrative_suggestion',
        'method': 'LP: min tổng |x_i - mục tiêu| trong miền khả thi; mục tiêu = % tối ưu đã xác minh nếu có, nếu không là điểm giữa khoảng',
        'objective': 'preferred' if preferred_idx else 'midpoint',
        'cutoff': cutoff,
        'sum_listed_pct': round(float(sum(x[:n])), 6),
        'unlisted_pct': round(float(x[n]) if captured['total_dim'] > n else 0.0, 6),
        'within_analysis_ranges': within,
        'legal_limits_checked': sorted(applied),
        'legal_limits_not_checked': [name for name in names if name.casefold() not in applied],
    }
    analysis['suggested_composition'] = comp
    analysis['explanation'] = _explain_feasible(req, analysis, comp)
    analysis['warnings'] += [
        'Gợi ý (suggested_pct) là điểm minh họa thỏa ràng buộc đã nhập, KHÔNG phải ước tính hàm lượng; không chứng minh hiệu lực, bảo quản hay tuân thủ pháp lý.',
        'estimated_pct giữ null: chưa có mô hình thống kê được kiểm định trên dữ liệu đo thực.',
        'Chỉ các giới hạn pháp lý đã áp dụng được kiểm tra. Không có bản ghi pháp lý KHÔNG có nghĩa là được phép.',
    ]
    return analysis


def suggest(payload: dict | AnalysisRequest, preferred: dict[str, float] | None = None) -> dict:
    analysis = analyze_with_suggestion(payload, preferred)
    if analysis['status'] != 'feasible' or not analysis.get('suggested_composition'):
        return analysis
    comp = analysis['suggested_composition']
    return {
        'status': 'feasible', 'market': analysis['market'], 'kind': comp['kind'], 'method': comp['method'],
        'cutoff': comp['cutoff'],
        'suggested': [
            {'ingredient': r['ingredient'], 'position': r['position'], 'suggested_pct': r['suggested_pct'],
             'min_pct': r['min_pct'], 'max_pct': r['max_pct'], 'estimated_pct': None}
            for r in analysis['results']
        ],
        'listed_sum_pct': comp['sum_listed_pct'], 'unlisted_pct': comp['unlisted_pct'],
        'within_analysis_ranges': comp['within_analysis_ranges'],
        'legal_limits_checked': comp['legal_limits_checked'], 'legal_limits_not_checked': comp['legal_limits_not_checked'],
        'warnings': analysis['warnings'],
    }
