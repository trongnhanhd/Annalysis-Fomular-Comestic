import json
from pathlib import Path
from scientific_bridge_v44 import screen_representative
from optimizer_v44 import solve_scenario
from formula_group_service import Catalog
ROOT=Path(__file__).resolve().parent

def test_scientific_bridge_returns_nonapproval():
    data=json.loads((ROOT/'examples/lip_balm_optimizer_v44.json').read_text(encoding='utf-8'))
    ans=solve_scenario(data,Catalog())
    sci=screen_representative(data,ans)
    assert sci['status']=='SCREENING_ONLY'
    assert sci['approved_for_manufacturing'] is False
    assert sci['regulatory_status']=='NOT_ASSESSED'
