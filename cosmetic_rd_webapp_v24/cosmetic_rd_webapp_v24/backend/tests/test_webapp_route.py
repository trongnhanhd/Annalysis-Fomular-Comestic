"""Smoke checks for the local-use Web App route."""
from fastapi.testclient import TestClient
from main import app


def test_webapp_served():
    with TestClient(app) as client:
        resp=client.get('/app')
        assert resp.status_code == 200
        assert 'Phòng nghiên cứu mỹ phẩm' in resp.text
        assert '/app/assets/app.js' in resp.text
        assert 'Pháp lý đa thị trường' in resp.text


def test_webapp_assets():
    with TestClient(app) as client:
        js=client.get('/app/assets/app.js')
        css=client.get('/app/assets/app.css')
        assert js.status_code==200 and 'runAnalysis' in js.text
        assert css.status_code==200 and 'analysis-layout' in css.text
