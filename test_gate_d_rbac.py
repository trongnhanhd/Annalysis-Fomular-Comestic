"""Gate D: RBAC matrix, session-bound traceability identity, lockout. Local SQLite only."""
import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
from api_v45 import app
from auth_r3 import create_user

ROOT = Path(__file__).resolve().parent
ORIGIN = 'http://localhost:3000'
PASSWORD = 'LongSecurePassword-2026!'


def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv('RND_AUTH_DB_PATH', str(tmp_path / 'auth.sqlite3'))
    monkeypatch.setenv('V45_DB_PATH', str(tmp_path / 'rnd.sqlite3'))
    monkeypatch.delenv('V45_DATABASE_URL', raising=False)
    monkeypatch.setenv('RND_AUTH_MODE', 'required')
    for name, role in (('gd.admin', 'admin'), ('gd.editor', 'editor'),
                       ('gd.reviewer', 'reviewer'), ('gd.viewer', 'viewer')):
        create_user(name, PASSWORD, role)
    return TestClient(app)


def _login(client, username, password=PASSWORD):
    return client.post('/api/v4.5/auth/login', json={'username': username, 'password': password},
                       headers={'Origin': ORIGIN})


def _study_payload():
    return json.loads((ROOT / 'examples/lip_balm_study_v45.json').read_text(encoding='utf-8'))


def _db_rows(path, sql, args=()):
    con = sqlite3.connect(path)
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def test_write_matrix_by_role(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    for username in ('gd.reviewer', 'gd.viewer'):
        client.cookies.clear()
        assert _login(client, username).status_code == 200
        assert client.get('/api/v4.5/studies').status_code == 200
        assert client.post('/api/v4.5/studies', json=_study_payload(), headers={'Origin': ORIGIN}).status_code == 403
        assert client.post('/api/v4.5/studies/x/batches', json={'lot_code': 'L', 'operator': 'o'},
                           headers={'Origin': ORIGIN}).status_code == 403
        assert client.post('/api/v4.5/studies/x/measurements', json={}, headers={'Origin': ORIGIN}).status_code == 403
    for username in ('gd.editor', 'gd.admin'):
        client.cookies.clear()
        assert _login(client, username).status_code == 200
        created = client.post('/api/v4.5/studies', json=_study_payload(), headers={'Origin': ORIGIN})
        assert created.status_code == 200, created.text


def test_batch_and_measurement_operator_comes_from_session(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    assert _login(client, 'gd.editor').status_code == 200
    sid = client.post('/api/v4.5/studies', json=_study_payload(), headers={'Origin': ORIGIN}).json()['study_id']
    batch = client.post(f'/api/v4.5/studies/{sid}/batches',
                        json={'lot_code': 'GD-01', 'operator': 'nguoi_gia_mao'}, headers={'Origin': ORIGIN})
    assert batch.status_code == 200, batch.text
    bid = batch.json()['batch_id']
    measurement = {'batch_id': bid, 'metric_code': 'HARDNESS', 'day': 0, 'value': 4.2, 'unit': 'N',
                   'method': 'SOP-RD', 'instrument_id': 'TESTER-01', 'operator': 'nguoi_gia_mao',
                   'evidence_uri': 'labbook://GD-01/HARDNESS-D0', 'data_kind': 'MEASURED'}
    assert client.post(f'/api/v4.5/studies/{sid}/measurements', json=measurement,
                       headers={'Origin': ORIGIN}).status_code == 200
    db = tmp_path / 'rnd.sqlite3'
    assert _db_rows(db, 'SELECT operator FROM batches WHERE id=?', (bid,)) == [('gd.editor',)]
    assert _db_rows(db, 'SELECT operator FROM measurements WHERE batch_id=?', (bid,)) == [('gd.editor',)]


def test_lockout_after_repeated_failures(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    for _ in range(5):
        assert _login(client, 'gd.editor', 'wrong-password-123').status_code == 401
    assert _login(client, 'gd.editor').status_code == 401, 'Correct password must be refused while locked'


def test_logout_invalidates_session(tmp_path, monkeypatch):
    client = _setup(tmp_path, monkeypatch)
    assert _login(client, 'gd.admin').status_code == 200
    assert client.get('/api/v4.5/auth/me').json()['role'] == 'admin'
    client.post('/api/v4.5/auth/logout', headers={'Origin': ORIGIN})
    assert client.get('/api/v4.5/auth/me').status_code == 401
