from scripts.check_frontend_api_contract_r4 import check

def test_frontend_backend_openapi_contract():
    r=check()
    assert r['status']=='PASS'
    assert r['ui_api_contracts'] >= 20
