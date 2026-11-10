"""Phương án minh họa: phải thỏa mọi ràng buộc của phân tích, không ghi đè estimated_pct."""
from suggest import suggest

FORMULA = {
    'market': 'EU',
    'product_type': 'leave_on',
    'inci': 'Propylene Glycol, Methylpropanediol, Mandelic Acid, Aqua, Potassium Azeloyl Diglycinate, Triethanolamine, Panthenol, Ethoxydiglycol, Sodium Polyacryloyldimethyl Taurate, Phenoxyethanol, Salicylic Acid, Hyaluronic Acid, Centella Asiatica Extract, Aloe Vera Callus Extract, Allantoin, Chlorphenesin, Disodium EDTA, Caprylyl Glycol',
    'apply_catalog_limits': True,
    'intended_use': {'Phenoxyethanol': 'preservative'},
    'known_pct': {
        'Mandelic Acid': {'value': 15, 'source': 'người dùng khẳng định'},
        'Potassium Azeloyl Diglycinate': {'value': 8, 'source': 'người dùng khẳng định'},
    },
}


def test_suggestion_respects_known_values_and_sums_to_100():
    out = suggest(FORMULA)
    assert out['status'] == 'feasible'
    assert out['kind'] == 'illustrative_suggestion'
    assert out['within_analysis_ranges'] is True
    assert abs(out['listed_sum_pct'] + out['unlisted_pct'] - 100) < 1e-3
    by_name = {x['ingredient']: x for x in out['suggested']}
    assert by_name['Mandelic Acid']['suggested_pct'] == 15
    assert by_name['Potassium Azeloyl Diglycinate']['suggested_pct'] == 8


def test_estimated_pct_stays_null():
    out = suggest(FORMULA)
    assert all(x['estimated_pct'] is None for x in out['suggested'])


def test_suggestion_respects_eu_preservative_limit():
    out = suggest(FORMULA)
    phe = next(x for x in out['suggested'] if x['ingredient'] == 'Phenoxyethanol')
    assert phe['suggested_pct'] <= 1.0 + 1e-6
    assert 'phenoxyethanol' in out['legal_limits_checked']
    assert 'Mandelic Acid' in out['legal_limits_not_checked']


def test_suggestion_respects_one_percent_tail_order():
    out = suggest(FORMULA)
    above = [x['suggested_pct'] for x in out['suggested'] if x['suggested_pct'] >= 1.0 - 1e-6]
    assert above == sorted(above, reverse=True)


def test_infeasible_input_is_reported():
    out = suggest({
        'market': 'EU',
        'inci': 'Aqua, Glycerin',
        'known_pct': {
            'Aqua': {'value': 90, 'source': 'test'},
            'Glycerin': {'value': 90, 'source': 'test'},
        },
    })
    assert out['status'] == 'infeasible'

def test_analysis_output_contains_suggestion_summing_to_100_within_ranges():
    from suggest import analyze_with_suggestion
    out = analyze_with_suggestion(FORMULA)
    assert out['status'] == 'feasible'
    total = sum(r['suggested_pct'] for r in out['results'])
    assert abs(total - 100) < 1e-4
    for r in out['results']:
        assert r['min_pct'] - 1e-6 <= r['suggested_pct'] <= r['max_pct'] + 1e-6
        assert r['estimated_pct'] is None
    assert out['suggested_composition']['within_analysis_ranges'] is True
    assert out['suggested_composition']['objective'] == 'midpoint'


def test_preferred_optimal_value_is_used_as_target():
    from suggest import analyze_with_suggestion
    out = analyze_with_suggestion({'market': 'EU', 'inci': 'Aqua, Glycerin'}, preferred={'Aqua': 70})
    values = {r['ingredient']: r['suggested_pct'] for r in out['results']}
    assert abs(values['Aqua'] - 70) < 1e-4
    assert abs(values['Glycerin'] - 30) < 1e-4
    assert out['suggested_composition']['objective'] == 'preferred'

def test_infeasible_input_names_conflicting_sources():
    from suggest import analyze_with_suggestion
    out = analyze_with_suggestion({
        'market': 'EU', 'inci': 'Aqua, Glycerin',
        'known_pct': {'Aqua': {'value': 90, 'source': 'test'}, 'Glycerin': {'value': 90, 'source': 'test'}},
    })
    ex = out['explanation']
    assert ex['feasible'] is False
    joined = ' '.join(ex['contradictions'])
    # Glycerin đứng sau Aqua nên 90% của Glycerin buộc Aqua ≥ 90%: bỏ Glycerin là khôi phục khả thi.
    assert 'Glycerin' in joined and 'khả thi' in joined


def test_explanation_marks_fixed_and_undetermined_values():
    from suggest import analyze_with_suggestion
    out = analyze_with_suggestion(FORMULA)
    ex = out['explanation']
    assert ex['feasible'] is True
    status = {r['ingredient']: r['explanation']['status'] for r in out['results']}
    assert status['Mandelic Acid'] == 'fixed'
    assert status['Propylene Glycol'] == 'undetermined'
    assert 'Propylene Glycol' in ex['undetermined']
    assert ex['assumptions'] and ex['data_needed']
    for r in out['results']:
        assert r['explanation']['why']
