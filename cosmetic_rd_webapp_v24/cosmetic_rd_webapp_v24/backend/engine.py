"""Concentration Inference Engine V2 — defensible feasible mass fractions, not reverse-engineered facts.

All quantities are % w/w of final product. The engine enumerates possible
1%-tail boundaries rather than assuming where the unordered section starts.
Only explicitly provided numeric data are treated as concentration constraints.
"""
from __future__ import annotations

import re
from typing import Dict, List, Literal, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator
from scipy.optimize import linprog
from evidence_catalog import find_studies, find_limits, evidence_meta, regulatory_meta, find_preservation_systems, preservation_meta

Market = Literal['EU', 'US', 'KR', 'CN', 'VN', 'ASEAN']

RULES = {
    'EU': {'rule': '1pct_tail', 'threshold': 1.0, 'source': 'https://www.legislation.gov.uk/eur/2009/1223/article/19/2025-06-02'},
    'US': {'rule': '1pct_tail', 'threshold': 1.0, 'source': 'https://www.ecfr.gov/current/title-21/section-701.3'},
    'KR': {'rule': '1pct_tail', 'threshold': 1.0, 'source': 'https://www.easylaw.go.kr/CSP/CnpClsMain.laf?ccfNo=4&cciNo=1&cnpClsNo=2&csmSeq=1301&popMenu=ov'},
    'VN': {'rule': '1pct_tail', 'threshold': 1.0, 'source': 'https://vanban.chinhphu.vn/default.aspx?docid=99376&pageid=27160'},
    'ASEAN': {'rule': '1pct_tail', 'threshold': 1.0, 'source': 'https://asean.org/our-communities/economic-community/standards-technical-regulations-and-conformity-assessment-procedures/key-documents-publications/'},
    'CN': {'rule': 'cn_trace', 'threshold': 0.1, 'source': 'https://www.nidc.org.cn/nifdc/bshff/hzhpjssp/hzhpspcjwtjd/hzhpwtjdjssp/20220419212459114.html'},
}

class KnownPercent(BaseModel):
    value: float = Field(ge=0, le=100)
    source: str = Field(min_length=1, description='Link/nhãn/tài liệu có thể xác minh')
    note: str = ''

class RangeBound(BaseModel):
    min_pct: float = Field(default=0, ge=0, le=100)
    max_pct: float = Field(default=100, ge=0, le=100)
    source: str = Field(min_length=1)
    kind: Literal['scientific', 'regulatory', 'supplier', 'other'] = 'other'
    note: str = ''

    @model_validator(mode='after')
    def valid_range(self):
        if self.min_pct > self.max_pct:
            raise ValueError('min_pct phải <= max_pct')
        return self

class Premix(BaseModel):
    name: str
    usage_pct: float = Field(ge=0, le=100)
    composition_pct: Dict[str, float] = Field(description='Hàm lượng thành phần trong nguyên liệu premix (%)')
    exclusively_sourced: List[str] = Field(default_factory=list)
    source: str = Field(min_length=1)

    @model_validator(mode='after')
    def valid_comp(self):
        if not self.composition_pct or any(x < 0 or x > 100 for x in self.composition_pct.values()):
            raise ValueError('composition_pct không hợp lệ')
        if sum(self.composition_pct.values()) > 100 + 1e-8:
            raise ValueError('Tổng thành phần premix >100%')
        if any(k not in self.composition_pct for k in self.exclusively_sourced):
            raise ValueError('exclusively_sourced không thuộc premix')
        return self

class DeclaredConcentration(BaseModel):
    """A pure-INCI claim about the *finished product*; other bases are rejected."""
    value: float = Field(ge=0)
    unit: Literal['percent', 'ppm', 'mg_per_g'] = 'percent'
    basis: Literal['final_product_pure_inci', 'commercial_premix'] = 'final_product_pure_inci'
    precision: Literal['exact', 'approximate'] = 'exact'
    source: str = Field(min_length=1)

    def as_percent(self) -> float:
        factor = {'percent': 1.0, 'ppm': 0.0001, 'mg_per_g': 0.1}[self.unit]
        result = self.value * factor
        if result > 100 + 1e-9:
            raise ValueError(f'Hàm lượng công bố vượt 100% ({result:g}%).')
        return result


class StudyEvidence(BaseModel):
    min_pct: float = Field(ge=0, le=100)
    max_pct: float = Field(ge=0, le=100)
    source_url: str = Field(min_length=1)
    outcome: str = Field(min_length=1, description='Kết quả nghiên cứu, không phải giới hạn pháp lý')
    study_type: str = 'published_study'
    matrix: str = ''
    ph: Optional[str] = None
    notes: str = ''

    @model_validator(mode='after')
    def valid_range(self):
        if self.min_pct > self.max_pct:
            raise ValueError('min_pct nghiên cứu phải <= max_pct')
        return self


class AnalysisRequest(BaseModel):
    market: Market = 'EU'
    inci: str = Field(min_length=1, description='Danh sách INCI chính, ngăn bởi dấu phẩy hoặc xuống dòng')
    trace_inci: str = Field(default='', description='Chỉ CN: nhóm 其他微量成分, KHÔNG gộp vào inci')
    color_additives: List[str] = Field(default_factory=list, description='Tên chất màu được miễn ràng buộc thứ tự')
    fragrance_exempt: List[str] = Field(default_factory=list, description='Chỉ KR: chất tạo hương miễn ràng buộc thứ tự')
    known_pct: Dict[str, KnownPercent] = Field(default_factory=dict)
    declared_concentrations: Dict[str, DeclaredConcentration] = Field(default_factory=dict, description='Nhãn ppm, mg/g hoặc % cho INCI tinh khiết trong thành phẩm')
    include_catalog_evidence: bool = True
    apply_catalog_limits: bool = False
    intended_use: Dict[str, str] = Field(default_factory=dict, description='VD: {"Phenoxyethanol":"preservative"}; cần để áp quy định theo chức năng')
    bounds: Dict[str, RangeBound] = Field(default_factory=dict)
    premixes: List[Premix] = Field(default_factory=list)
    research_evidence: Dict[str, List[StudyEvidence]] = Field(default_factory=dict, description='Bằng chứng nghiên cứu mềm, KHÔNG giới hạn miền khả thi')
    max_unlisted_pct: float = Field(default=0, ge=0, le=100, description='Chỉ khi có cơ sở về tổng các chất không ghi nhãn')
    product_type: str = 'leave_on'

    @field_validator('inci')
    @classmethod
    def nonempty(cls, v):
        if not v.strip():
            raise ValueError('INCI rỗng')
        return v


def parse_inci(raw: str) -> List[str]:
    vals = [x.strip() for x in re.split(r'[,;\n]+', raw) if x.strip()]
    seen = set()
    for name in vals:
        k = name.casefold()
        if k in seen:
            raise ValueError(f'Thành phần trùng lặp: {name}. Gộp theo INCI trước khi phân tích.')
        seen.add(k)
    return vals


def _analysis(inp: AnalysisRequest) -> dict:
    main = parse_inci(inp.inci)
    trace = parse_inci(inp.trace_inci) if inp.trace_inci.strip() else []
    if inp.market != 'CN' and trace:
        raise ValueError('trace_inci chỉ dùng với nhãn Trung Quốc có nhóm 其他微量成分.')
    if set(n.lower() for n in main) & set(n.lower() for n in trace):
        raise ValueError('Một INCI xuất hiện đồng thời trong nhóm chính và nhóm vi lượng.')
    ingredients = main + trace
    if not ingredients or len(ingredients) > 75:
        raise ValueError('Cho phép từ 1 đến 75 thành phần cho mỗi lần phân tích.')
    keys = {name.casefold(): i for i, name in enumerate(ingredients)}
    n = len(ingredients)
    ix_unknown = n if inp.max_unlisted_pct else None
    total_dim = n + (1 if ix_unknown is not None else 0)
    limits: list[tuple[float, float]] = [(0, 100) for _ in ingredients]
    if ix_unknown is not None:
        limits.append((0, inp.max_unlisted_pct))
    reasons: dict[str, list[str]] = {k: [] for k in ingredients}
    warnings: list[str] = []
    claims_annotations: dict[str, list[dict]] = {k: [] for k in ingredients}
    applied_catalog_limits: list[dict] = []

    def idx(k: str) -> int:
        index = keys.get(k.strip().casefold())
        if index is None:
            raise ValueError(f'Không tìm thấy nguyên liệu {k!r} trong INCI.')
        return index

    # Hand-curated law is OFF by default. An explicit intended-use match is mandatory.
    # An unmatched market/ingredient is NEVER interpreted as legal permission.
    if inp.apply_catalog_limits:
        for name in ingredients:
            use = next((u for label, u in inp.intended_use.items() if label.casefold() == name.casefold()), None)
            if not use:
                continue
            for legal in find_limits(inci=name, market=inp.market):
                if (use.casefold() != legal['intended_use'].casefold() or
                    legal['product_type'] not in ('all', inp.product_type)):
                    continue
                i = idx(name)
                lo, hi = limits[i]
                limits[i] = (lo, min(hi, float(legal['max_pct'])))
                reasons[name].append(f"Mục pháp lý tùy chọn: ≤{legal['max_pct']}% — {legal['id']} — {legal['source_url']}")
                applied_catalog_limits.append(legal)
        if not applied_catalog_limits:
            warnings.append('Đã bật kho pháp lý mẫu nhưng không có mục phù hợp với thị trường/chức năng; không được suy ra hợp pháp.')
        warnings.append('Kho pháp lý chỉ có dữ liệu chọn lọc; KHÔNG phải bản rà soát tuân thủ cho 6 thị trường.')
    for label in inp.intended_use:
        idx(label)

    for label, bound in inp.bounds.items():
        i = idx(label)
        lo, hi = limits[i]
        limits[i] = (max(lo, bound.min_pct), min(hi, bound.max_pct))
        reasons[ingredients[i]].append(f'{bound.kind}: {bound.min_pct}–{bound.max_pct}% — {bound.source}')
        if bound.kind == 'regulatory' and not bound.source.startswith('http'):
            warnings.append(f'Giới hạn của {label} được nhập thủ công: cần kiểm tra nguồn pháp lý và loại sản phẩm.')
    for label, known in inp.known_pct.items():
        i = idx(label)
        lo, hi = limits[i]
        limits[i] = (max(lo, known.value), min(hi, known.value))
        reasons[ingredients[i]].append(f'Giá trị công bố: {known.value}% — {known.source}')

    # Convert strictly identified finished-product claims. Approximate marketing
    # numbers are displayed but not silently treated as exact equalities.
    for label, declared in inp.declared_concentrations.items():
        i = idx(label)
        if declared.basis != 'final_product_pure_inci':
            raise ValueError(f'{label}: % nguyên liệu thương mại/complex không chứng minh % INCI tinh khiết; dùng premixes + COA.')
        amount = declared.as_percent()
        claims_annotations[ingredients[i]].append({
            'value_input': declared.value, 'unit': declared.unit, 'converted_pct': round(amount, 8),
            'precision': declared.precision, 'source': declared.source,
        })
        if declared.precision == 'exact':
            lo, hi = limits[i]
            limits[i] = (max(lo, amount), min(hi, amount))
            reasons[ingredients[i]].append(f'Nhãn định lượng: {declared.value:g} {declared.unit} = {amount:.8g}% — {declared.source}')
        else:
            warnings.append(f'{label}: công bố xấp xỉ {amount:g}% chỉ hiển thị tham khảo; không ép thành tỷ lệ chính xác.')

    premix_eq: Dict[int, float] = {}
    premix_min: Dict[int, float] = {}
    for mix in inp.premixes:
        for name, percent_in_mix in mix.composition_pct.items():
            i = idx(name)
            contribution = mix.usage_pct * percent_in_mix / 100
            premix_min[i] = premix_min.get(i, 0) + contribution
            reasons[ingredients[i]].append(f'Đóng góp premix {mix.name}: ≥{contribution:.6g}% — {mix.source}')
            if name in mix.exclusively_sourced:
                premix_eq[i] = premix_eq.get(i, 0) + contribution
    for i, amount in premix_min.items():
        lo, hi = limits[i]
        limits[i] = (max(lo, amount), hi)
    for i, amount in premix_eq.items():
        lo, hi = limits[i]
        limits[i] = (max(lo, amount), min(hi, amount))
        reasons[ingredients[i]].append('Được khai báo nguồn độc quyền: cố định theo premix')
    for ingredient_name in inp.research_evidence:
        idx(ingredient_name)  # Validate evidence refers to a listed ingredient.
    for i, (lo, hi) in enumerate(limits):
        if lo > hi + 1e-9:
            return {'status': 'infeasible', 'market': inp.market, 'issues': [f'Mâu thuẫn cận của {ingredients[i]}: min {lo:.4g}% > max {hi:.4g}%.'], 'warnings': warnings}
    if sum(lo for lo, _ in limits) > 100 + 1e-8:
        return {'status': 'infeasible', 'market': inp.market, 'issues': ['Tổng tỷ lệ tối thiểu vượt 100%.'], 'warnings': warnings}
    if sum(hi for _, hi in limits) < 100 - 1e-8:
        return {'status': 'infeasible', 'market': inp.market, 'issues': ['Tổng tỷ lệ tối đa thấp hơn 100%. Có thể thiếu INCI hoặc nguyên liệu chưa được ghi nhận.'], 'warnings': warnings}

    excluded = {idx(name) for name in inp.color_additives}
    if inp.market == 'KR':
        excluded |= {idx(name) for name in inp.fragrance_exempt}
    else:
        if inp.fragrance_exempt:
            raise ValueError('fragrance_exempt hiện chỉ áp dụng cho KR.')
    excluded_main = set(i for i in excluded if i < len(main))
    ranked = [i for i in range(len(main)) if i not in excluded_main]
    if excluded_main:
        warnings.append('Chất màu/hương được khai báo miễn thứ tự; hệ thống không tự động kiểm chứng nhóm chức năng.')

    # equality sum=100: default is a closed composition assumption.
    A_eq = np.ones((1, total_dim), dtype=float)
    b_eq = np.array([100.0])

    def build_partition(cutoff: Optional[int]):
        rows, vals = [], []
        b = [list(pair) for pair in limits]
        if inp.market == 'CN':
            # Main China INCI ordered descending; <=0.1% separately marked trace ingredients.
            for a, c in zip(ranked[:-1], ranked[1:]):
                row = np.zeros(total_dim)
                row[c] = 1
                row[a] = -1
                rows.append(row)
                vals.append(0.)
            for i in ranked:
                b[i][0] = max(b[i][0], 0.1)
            for i in range(len(main), n):
                b[i][1] = min(b[i][1], 0.1)
        else:
            assert cutoff is not None
            before, after = ranked[:cutoff], ranked[cutoff:]
            # >=1 on ordered part, <=1 on unordered tail. Boundary at exactly 1 is allowed.
            for i in before:
                b[i][0] = max(b[i][0], 1.0)
            for i in after:
                b[i][1] = min(b[i][1], 1.0)
            for a, c in zip(before[:-1], before[1:]):
                row = np.zeros(total_dim)
                row[c] = 1
                row[a] = -1
                rows.append(row)
                vals.append(0.)
        if any(lo > hi + 1e-9 for lo, hi in b):
            return None
        A_ub = np.vstack(rows) if rows else None
        b_ub = np.array(vals) if vals else None
        return A_ub, b_ub, [tuple(pair) for pair in b]

    cutoffs = [None] if inp.market == 'CN' else list(range(len(ranked) + 1))
    feasible = []
    for cutoff in cutoffs:
        model = build_partition(cutoff)
        if model is None:
            continue
        A_ub, b_ub, b = model
        result = linprog(np.zeros(total_dim), A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=b, method='highs')
        if result.success:
            feasible.append((cutoff, model))

    if not feasible:
        return {
            'status': 'infeasible', 'market': inp.market,
            'issues': ['Không tồn tại công thức phù hợp đồng thời với: thứ tự INCI, tỷ lệ công bố, giới hạn đã nhập và tổng 100%. Kiểm tra phiên bản nhãn, đơn vị %, premix hoặc dữ liệu đầu vào.'],
            'warnings': warnings,
        }
    lo_out = np.full(n, np.inf)
    hi_out = np.full(n, -np.inf)
    for cutoff, (A_ub, b_ub, b) in feasible:
        for i in range(n):
            obj = np.zeros(total_dim)
            obj[i] = 1
            low_res = linprog(obj, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=b, method='highs')
            high_res = linprog(-obj, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=b, method='highs')
            if not low_res.success or not high_res.success:
                raise RuntimeError('Bộ giải LP mất ổn định khi tính min/max.')
            lo_out[i] = min(lo_out[i], max(0, low_res.fun))
            hi_out[i] = max(hi_out[i], min(100, -high_res.fun))

    warnings.append('Các khoảng là miền khả thi theo các giả định đã nhập; KHÔNG phải đo nồng độ thực nghiệm hay khoảng tin cậy thống kê.')
    if inp.include_catalog_evidence:
        warnings.append('Thư viện nghiên cứu được đính kèm để tham khảo, KHÔNG thay đổi khoảng min–max của bộ giải LP.')
    warnings.append('Mốc khoa học được ghi riêng, không dùng làm ràng buộc cứng và không thể thay cho challenge test trên thành phẩm.') if inp.research_evidence else None
    if inp.max_unlisted_pct == 0:
        warnings.append('Đang giả định danh sách INCI mô tả đủ 100% khối lượng; thành phần được miễn ghi nhãn/không khai báo có thể làm thay đổi kết quả.')
    else:
        warnings.append(f'Cho phép tối đa {inp.max_unlisted_pct}% thành phần không ghi nhãn trong biến ẩn; phải có căn cứ cho giả định này.')
    if not inp.known_pct and not inp.bounds and not inp.premixes and not inp.declared_concentrations and not applied_catalog_limits:
        warnings.append('Không có tỷ lệ công bố hay ràng buộc định lượng bổ sung: khoảng ước tính sẽ rộng. Không đưa ra giá trị có khả năng cao.')
    if inp.market == 'CN' and not trace:
        warnings.append('Không cung cấp phần nhãn 其他微量成分; không được tự suy ra mốc 0,1% cho bất kỳ thành phần nào.')
    if inp.market == 'US':
        warnings.append('Nếu sản phẩm thuộc nhóm thuốc OTC, cần tách nhãn Active Ingredients khỏi danh sách INCI mỹ phẩm.')

    output = []
    for i, name in enumerate(ingredients):
        studies = next((items for k, items in inp.research_evidence.items() if k.casefold() == name.casefold()), [])
        evidence = []
        for st in studies:
            lower = max(float(lo_out[i]), st.min_pct)
            upper = min(float(hi_out[i]), st.max_pct)
            evidence.append({
                **st.model_dump(),
                'source_kind': 'user_submitted_unverified',
                'overlap_with_feasible_pct': [round(lower, 6), round(upper, 6)] if lower <= upper + 1e-8 else None,
                'matrix_match': 'chưa kiểm chứng',
                'interpretation': 'Bằng chứng do người dùng nhập; cần kiểm tra nghiên cứu gốc và khả năng áp dụng.',
            })
        if inp.include_catalog_evidence:
            for record in find_studies(inci=name):
                lower = max(float(lo_out[i]), float(record['min_pct']))
                upper = min(float(hi_out[i]), float(record['max_pct']))
                evidence.append({
                    **record,
                    'source_kind': 'reviewed_catalog',
                    'overlap_with_feasible_pct': [round(lower, 6), round(upper, 6)] if lower <= upper + 1e-8 else None,
                    'matrix_match': 'cùng loại sản phẩm sơ bộ' if record['product_type'] == inp.product_type else 'khác hoặc chưa xác định nền công thức',
                    'interpretation': 'Dữ liệu nghiên cứu tham khảo; không suy ra % tối ưu, khả năng cao, hay hiệu lực bảo quản của sản phẩm đang xét.',
                })
        output.append({
            'research_evidence': evidence,
            'ingredient': name, 'position': i + 1, 'section': 'trace' if i >= len(main) else 'main',
            'min_pct': round(float(lo_out[i]), 6), 'max_pct': round(float(hi_out[i]), 6),
            'estimated_pct': None, 'estimate_status': 'chưa đủ dữ liệu hiệu chuẩn để dự đoán điểm',
            'claims_annotations': claims_annotations[name],
            'regulatory_references': find_limits(inci=name, market=inp.market),
            'constraints': reasons[name],
            'interval_kind': 'miền khả thi (LP)',
        })
    # WHOLE-SYSTEM research comparison only; no concentration constraints or
    # prediction of preservative efficacy. Even matching all ingredients does
    # not prove that those percentages are jointly feasible in this product.
    preservation_matches = []
    result_lookup = {r['ingredient'].casefold(): r for r in output}
    for item in find_preservation_systems():
        observed = [k for k in item['composition_pct'] if k.casefold() in result_lookup]
        if not observed:
            continue
        all_present = len(observed) == len(item['composition_pct'])
        individually_within = (all(
            result_lookup[name.casefold()]['min_pct'] - 1e-7 <= pct <= result_lookup[name.casefold()]['max_pct'] + 1e-7
            for name, pct in item['composition_pct'].items()) if all_present else None)
        preservation_matches.append({
            **item, 'matched_ingredients': observed, 'full_ingredient_match': all_present,
            'individual_intervals_contain_studied_values': individually_within,
            'interpretation': 'Chỉ đối chiếu nghiên cứu trên TOÀN HỆ; không chứng minh công thức này đạt/không đạt challenge test, không xác minh tính khả thi đồng thời.',
        })

    return {
        'status': 'feasible', 'market': inp.market, 'market_rule': RULES[inp.market],
        'n_ingredients': n, 'feasible_scenarios': len(feasible),
        'possible_tail_boundaries': [v for v, _ in feasible] if inp.market != 'CN' else [],
        'results': output, 'issues': [], 'warnings': warnings,
        'applied_catalog_limits': applied_catalog_limits,
        'catalog_versions': {'evidence': evidence_meta()['version'], 'regulatory': regulatory_meta()['version'], 'preservation': preservation_meta()['version']},
        'preservation_system_matches': preservation_matches,
        'method': 'Linear programming HiGHS; hợp của các miền ứng với mọi ranh giới nhóm <=1% khả thi; đơn vị % w/w',
    }


def analyze(payload: dict | AnalysisRequest) -> dict:
    req = payload if isinstance(payload, AnalysisRequest) else AnalysisRequest.model_validate(payload)
    return _analysis(req)
