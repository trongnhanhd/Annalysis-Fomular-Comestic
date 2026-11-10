"""R3 dedicated SQLite auth tests. Not proof of production security."""
from fastapi.testclient import TestClient
from api_v45 import app
from auth_r3 import create_user

BASE_ORIGIN = 'http://localhost:3000'

def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv('RND_AUTH_DB_PATH', str(tmp_path/'auth.sqlite3'))
    monkeypatch.setenv('V45_DB_PATH', str(tmp_path/'rnd.sqlite3'))
    monkeypatch.delenv('V45_DATABASE_URL', raising=False)
    monkeypatch.setenv('RND_AUTH_MODE', 'required')
    create_user('rnd.editor', 'LongSecurePassword-2026!', 'editor')
    create_user('rnd.viewer', 'AnotherSecurePassword-2026!', 'viewer')
    return TestClient(app)

def _login(client, username, password):
    return client.post('/api/v4.5/auth/login', json={'username':username,'password':password},
                       headers={'Origin': BASE_ORIGIN})

def test_login_required_and_session_cookie(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    assert client.get('/api/v4.5/studies').status_code == 401
    assert client.get('/openapi.json').status_code == 401
    assert client.get('/health/v4.5').status_code == 200
    assert _login(client, 'rnd.editor', 'badpassword').status_code == 401
    ok = _login(client, 'rnd.editor', 'LongSecurePassword-2026!')
    assert ok.status_code == 200, ok.text
    assert 'httponly' in ok.headers['set-cookie'].lower()
    assert 'samesite=strict' in ok.headers['set-cookie'].lower()
    assert 'longsecurepassword' not in str(ok.json()).lower()
    assert client.get('/api/v4.5/auth/me').json()['username'] == 'rnd.editor'
    assert client.get('/api/v4.5/studies').status_code == 200
    assert client.post('/api/v4.5/auth/logout', headers={'Origin':BASE_ORIGIN}).status_code == 200
    assert client.get('/api/v4.5/studies').status_code == 401

def test_viewer_cannot_write_but_can_read(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    assert _login(client, 'rnd.viewer', 'AnotherSecurePassword-2026!').status_code == 200
    assert client.get('/api/v4.5/studies').status_code == 200
    blocked = client.post('/api/v4.5/studies', json={}, headers={'Origin':BASE_ORIGIN})
    assert blocked.status_code == 403
    assert client.post('/api/v4.5/studies/test/batches',json={},headers={'Origin':BASE_ORIGIN}).status_code==403
    assert client.post('/api/v4.5/studies/test/measurements',json={},headers={'Origin':BASE_ORIGIN}).status_code==403

def test_session_cookie_rejects_cross_origin_write(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    assert _login(client, 'rnd.editor', 'LongSecurePassword-2026!').status_code == 200
    assert client.post('/api/v4.5/studies',json={},headers={'Origin':'https://attacker.invalid'}).status_code==403
    assert client.post('/api/v4.5/studies',json={}).status_code==403
    # Approved origin reaches input validation rather than denied by auth.
    response=client.post('/api/v4.5/studies',json={},headers={'Origin':BASE_ORIGIN})
    assert response.status_code==422


def test_creator_comes_from_session_not_request_body(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parent
    client=_setup(tmp_path,monkeypatch)
    assert _login(client,'rnd.editor','LongSecurePassword-2026!').status_code==200
    payload=json.loads((root/'examples/lip_balm_study_v45.json').read_text(encoding='utf-8'))
    payload['created_by']='pretend_admin'
    created=client.post('/api/v4.5/studies',json=payload,headers={'Origin':BASE_ORIGIN})
    assert created.status_code == 200, created.text
    record=client.get('/api/v4.5/studies/'+created.json()['study_id'])
    assert record.status_code == 200
    assert record.json()['created_by'] == 'rnd.editor'


def test_invalid_mode_fails_closed(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    monkeypatch.setenv('RND_AUTH_MODE', 'maybe')
    assert client.get('/api/v4.5/studies').status_code == 503


def test_auth_disabled_legacy_mode(tmp_path, monkeypatch):
    _setup(tmp_path,monkeypatch)
    monkeypatch.setenv('RND_AUTH_MODE', 'disabled')
    c=TestClient(app)
    assert c.get('/api/v4.5/studies').status_code==200
    assert c.get('/api/v4.5/auth/me').json()['auth_enabled'] is False


def test_disabled_account_revokes_active_session(tmp_path, monkeypatch):
    from auth_r3 import disable_user
    client=_setup(tmp_path,monkeypatch)
    assert _login(client,'rnd.editor','LongSecurePassword-2026!').status_code==200
    assert client.get('/api/v4.5/studies').status_code==200
    disable_user('rnd.editor')
    assert client.get('/api/v4.5/studies').status_code==401
    assert _login(client,'rnd.editor','LongSecurePassword-2026!').status_code==401


def test_login_rejects_missing_and_cross_site_origin(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    payload={'username':'rnd.editor','password':'LongSecurePassword-2026!'}
    assert client.post('/api/v4.5/auth/login',json=payload).status_code == 403
    assert client.post('/api/v4.5/auth/login',json=payload,headers={'Origin':'null'}).status_code == 403
    assert client.post('/api/v4.5/auth/login',json=payload,headers={'Origin':'https://untrusted.invalid'}).status_code == 403
    assert client.post('/api/v4.5/auth/login',json=payload,headers={'Origin':BASE_ORIGIN}).status_code == 200
