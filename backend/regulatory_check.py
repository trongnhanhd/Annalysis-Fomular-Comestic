"""Kiểm tra sơ bộ giới hạn từ bộ luật tham chiếu (data/regulatory_rules.json).

Logic đồng bộ từ check_formula.py. KHÔNG phải phê duyệt pháp lý; không có bản ghi khớp
nghĩa là cần rà soát, không phải là được phép.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

DATA_PATH = Path(__file__).parent / 'data' / 'regulatory_rules.json'
DISCLAIMER = 'Never use as regulatory approval; verify version, function, category, warnings, aggregated ingredients and local adoption.'


class RegulatoryCheckIn(BaseModel):
    market: Literal['EU', 'US', 'VN', 'ASEAN', 'KR', 'CN']
    category: str = Field(min_length=1, description='product_scope, ví dụ leave_on, rinse_off, other_cosmetics')
    purpose: str = 'preservative'
    inci: str = Field(min_length=1)
    pct: float = Field(ge=0)
    basis: str = Field(default='ingredient', description='ingredient, as_benzoic_acid, retinol_equivalent, mixture_3_to_1 ...')
    date: str | None = Field(default=None, description='YYYY-MM-DD; mặc định là hôm nay')


@lru_cache(maxsize=1)
def _rules() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding='utf-8'))['regulatory_rules']


def check_limit(req: RegulatoryCheckIn) -> dict:
    on = req.date or date.today().isoformat()
    rows = [
        r for r in _rules()
        if r['market'] == req.market and r['inci_name'].lower() == req.inci.lower()
        and (r['purpose'] == req.purpose or r['purpose'] == 'any' or req.purpose == 'any')
        and (not r['effective_from'] or r['effective_from'] <= on)
        and (not r['effective_to'] or r['effective_to'] >= on)
    ]
    # Conservative: only wildcard or exact scope; no fuzzy matching.
    matching = [r for r in rows if r['product_scope'] in ('all_cosmetics', req.category)]
    if req.market == 'US' and req.category == 'otc_sunscreen_drug' and req.purpose == 'otc_sunscreen_active':
        matching = [r for r in rows if r['product_scope'] == 'otc_sunscreen_drug']

    if not matching:
        result = {'status': 'NEEDS_LEGAL_REVIEW', 'explanation': 'No exactly matching verified source rule. This does not imply allowed or prohibited.'}
    elif any(r['rule_type'] in ('PROHIBITED_INTENTIONAL_USE', 'NOT_ALLOWED_FOR_PURPOSE', 'REMOVED_FROM_OTC_MONOGRAPH') for r in matching):
        result = {'status': 'RESTRICTED_OR_NOT_AUTHORIZED', 'rule_ids': [r['rule_id'] for r in matching]}
    elif len(matching) != 1:
        result = {'status': 'NEEDS_LEGAL_REVIEW', 'explanation': 'Multiple matching rules require product context.', 'rule_ids': [r['rule_id'] for r in matching]}
    else:
        r = matching[0]
        if r['rule_type'] != 'MAX' or r['max_pct_w_w'] is None:
            result = {'status': 'NEEDS_LEGAL_REVIEW', 'rule_id': r['rule_id']}
        elif r['concentration_basis'] != req.basis:
            result = {'status': 'NEEDS_BASIS_CONVERSION', 'required_basis': r['concentration_basis'], 'rule_id': r['rule_id']}
        elif not r['auto_checkable'] or r['limit_group_id'] or r['additional_conditions'] or r['label_warning']:
            result = {'status': 'MANUAL_CONDITIONS_REQUIRED', 'threshold_pct': r['max_pct_w_w'], 'above_numeric_threshold': req.pct > r['max_pct_w_w'], 'rule_id': r['rule_id']}
        else:
            result = {'status': 'EXCEEDS_NUMERIC_MAX' if req.pct > r['max_pct_w_w'] else 'NOT_ABOVE_NUMERIC_MAX', 'limit_pct': r['max_pct_w_w'], 'rule_id': r['rule_id']}

    result.update({'market': req.market, 'inci': req.inci, 'product_scope': req.category, 'input_pct': req.pct, 'disclaimer': DISCLAIMER})
    return result
