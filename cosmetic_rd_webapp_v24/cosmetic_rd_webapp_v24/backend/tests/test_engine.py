import pytest
from engine import analyze


def get(r, name):
    return next(x for x in r['results'] if x['ingredient'] == name)


def test_demo_5_percent_anchor_and_lower_predecessor():
    r = analyze({'market':'EU','inci':'Aqua, Glycerin, Niacinamide, Panthenol, Phenoxyethanol, Ethylhexylglycerin, Sodium Hyaluronate',
        'known_pct':{'Niacinamide':{'value':5,'source':'Demo'}}})
    assert r['status']=='feasible'
    assert get(r,'Niacinamide')['min_pct']==5
    assert get(r,'Niacinamide')['max_pct']==5
    assert get(r,'Glycerin')['min_pct']>=5
    assert get(r,'Panthenol')['max_pct']<=5.000001


def test_unordered_tail_does_not_impose_monotonicity():
    r = analyze({'market':'US','inci':'Aqua, Glycerin, A, B',
        'known_pct':{'Glycerin':{'value':4,'source':'Demo'},'A':{'value':0.2,'source':'Demo'},'B':{'value':0.8,'source':'Demo'}}})
    assert r['status']=='feasible'
    assert get(r,'B')['min_pct']==pytest.approx(.8)


def test_china_trace_0_1():
    r=analyze({'market':'CN','inci':'Aqua, Glycerin, Niacinamide', 'trace_inci':'Tocopherol, Sodium Hyaluronate',
        'known_pct':{'Niacinamide':{'value':5,'source':'Demo'}}})
    assert r['status']=='feasible'
    assert get(r,'Tocopherol')['max_pct']<=.1+1e-6


def test_china_main_order_restricts():
    r=analyze({'market':'CN','inci':'Aqua, Glycerin, Niacinamide, Panthenol',
        'known_pct':{'Niacinamide':{'value':5,'source':'Demo'}}})
    assert r['status']=='feasible'
    assert get(r,'Glycerin')['min_pct']>=5
    assert get(r,'Panthenol')['max_pct']<=5


def test_premix_exclusive_fixing():
    r=analyze({'market':'EU','inci':'Aqua, Glycerin, Niacinamide, Panthenol',
        'premixes':[{'name':'Demo mix','usage_pct':10,'composition_pct':{'Niacinamide':50,'Aqua':50},'exclusively_sourced':['Niacinamide'],'source':'COA'}]})
    assert r['status']=='feasible'
    assert get(r,'Niacinamide')['min_pct']==5
    assert get(r,'Aqua')['min_pct']>=5


def test_contradictory_bound():
    r=analyze({'market':'EU','inci':'Aqua, Niacinamide',
        'known_pct':{'Niacinamide':{'value':5,'source':'Demo'}},
        'bounds':{'Niacinamide':{'max_pct':1,'source':'Demo'}}})
    assert r['status']=='infeasible'


def test_does_not_guess_a_point_estimate():
    r=analyze({'market':'VN','inci':'Aqua, Glycerin, Niacinamide'})
    assert r['status']=='feasible'
    assert all(x['estimated_pct'] is None for x in r['results'])


def test_us_color_order_exempt():
    r=analyze({'market':'US','inci':'Aqua, CI 77491, Glycerin, Niacinamide',
        'color_additives':['CI 77491'],
        'known_pct':{'Glycerin':{'value':5,'source':'demo'},'CI 77491':{'value':15,'source':'demo'}}})
    assert r['status']=='feasible'


def test_missing_tail_not_inferred_cn():
    r=analyze({'market':'CN','inci':'Aqua, Glycerin, Niacinamide'})
    assert r['status']=='feasible'
    assert get(r,'Niacinamide')['max_pct']>.1


def test_us_infeasible_rank_and_claim():
    r=analyze({'market':'US','inci':'Aqua, Glycerin, Niacinamide, Panthenol',
        'known_pct':{'Niacinamide':{'value':20,'source':'demo'},'Glycerin':{'value':2,'source':'demo'}}})
    assert r['status']=='infeasible'


def test_unknown_share():
    r=analyze({'market':'EU','inci':'Aqua, Niacinamide',
        'known_pct':{'Niacinamide':{'value':5,'source':'demo'}},'max_unlisted_pct':3})
    assert r['status']=='feasible'
    assert get(r,'Aqua')['min_pct']==92
    assert get(r,'Aqua')['max_pct']==95


def test_all_six_markets_support():
    for m in ['EU','US','KR','CN','VN','ASEAN']:
        r=analyze({'market':m,'inci':'Aqua, Glycerin, Niacinamide'})
        assert r['status']=='feasible',m


def test_name_lookup_casefold():
    r=analyze({'market':'EU','inci':'Aqua, Niacinamide',
        'known_pct':{'niacinamide':{'value':5,'source':'demo'}}})
    assert get(r,'Niacinamide')['max_pct']==5


def test_duplicate_inci_fails():
    with pytest.raises(ValueError,match='trùng lặp'):
        analyze({'market':'EU','inci':'Aqua, aqua'})


def test_research_evidence_is_annotation_not_constraint():
    r=analyze({'market':'EU','inci':'Aqua, Phenoxyethanol',
       'research_evidence':{'Phenoxyethanol':[{'min_pct':0.48,'max_pct':0.48,'source_url':'https://doi.org/10.1038/s41598-024-69624-9','outcome':'pass in research system'}]}})
    assert r['status']=='feasible'
    item=get(r,'Phenoxyethanol')
    assert item['max_pct'] > .48
    assert item['research_evidence'][0]['overlap_with_feasible_pct']==[.48,.48]
