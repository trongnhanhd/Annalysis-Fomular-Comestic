"""Local-prototype authentication gate for Formula Intelligence.

No production multi-tenant claims: accounts are kept in a dedicated local SQLite file.
Enable explicitly with RND_AUTH_MODE=required. Only local demo use is supported.
"""
from __future__ import annotations

from contextlib import contextmanager

import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

ROLES = {'viewer', 'reviewer', 'editor', 'admin'}
USER_PATTERN = re.compile(r'^[A-Za-z0-9_.@-]{3,64}$')
SESSION_SECONDS = 8 * 3600


def auth_mode():
    value = os.getenv('RND_AUTH_MODE', 'disabled').strip().lower()
    if value not in ('disabled', 'required'):
        raise RuntimeError('Invalid RND_AUTH_MODE; only disabled or required are accepted')
    return value


def _database_path() -> Path:
    return Path(os.getenv('RND_AUTH_DB_PATH', 'var/auth_r3.sqlite3'))


@contextmanager
def _connect():
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise RuntimeError('Auth database must not be a symbolic link')
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=10000')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS rnd_auth_users (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE COLLATE NOCASE NOT NULL,
            salt TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL,
            disabled INTEGER NOT NULL DEFAULT 0, failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS rnd_auth_sessions (
            token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES rnd_auth_users(id)
        );
    ''')
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _pwd(password: str, salt: bytes) -> str:
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=1, dklen=32).hex()


def create_user(username: str, password: str, role: str):
    if not USER_PATTERN.fullmatch(username):
        raise ValueError('Username must have 3–64 allowed characters')
    if len(password) < 12 or len(password) > 1024:
        raise ValueError('Password must contain 12–1024 characters')
    if role not in ROLES:
        raise ValueError('Invalid role')
    salt = secrets.token_bytes(16)
    with _connect() as con:
        con.execute('INSERT INTO rnd_auth_users(username,salt,password_hash,role) VALUES (?,?,?,?)',
                    (username, salt.hex(), _pwd(password, salt), role))



def disable_user(username: str):
    with _connect() as con:
        changed = con.execute('UPDATE rnd_auth_users SET disabled=1 WHERE username=?', (username,))
        if changed.rowcount != 1:
            raise ValueError('User does not exist')
        con.execute('DELETE FROM rnd_auth_sessions WHERE user_id=(SELECT id FROM rnd_auth_users WHERE username=?)', (username,))


def _digest_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def login(username: str, password: str):
    now = int(time.time())
    with _connect() as con:
        row = con.execute('SELECT * FROM rnd_auth_users WHERE username=?', (username,)).fetchone()
        # Constant-work for missing accounts.
        digest = _pwd(password, bytes.fromhex(row['salt']) if row else bytes(16))
        if not row or row['disabled'] or row['locked_until'] > now or not hmac.compare_digest(digest, row['password_hash']):
            if row and not row['disabled'] and row['locked_until'] <= now:
                failures = row['failed_attempts'] + 1
                con.execute('UPDATE rnd_auth_users SET failed_attempts=?,locked_until=? WHERE id=?',
                            (0 if failures >= 5 else failures, now + 900 if failures >= 5 else 0, row['id']))
            return None
        con.execute('UPDATE rnd_auth_users SET failed_attempts=0,locked_until=0 WHERE id=?', (row['id'],))
        token = secrets.token_urlsafe(32)
        con.execute('DELETE FROM rnd_auth_sessions WHERE expires_at<=?', (now,))
        con.execute('INSERT INTO rnd_auth_sessions(token_hash,user_id,expires_at) VALUES (?,?,?)',
                    (_digest_token(token), row['id'], now + SESSION_SECONDS))
        return {'token': token, 'username': row['username'], 'role': row['role']}


def current_user(request: Request):
    token = request.cookies.get('rnd_session_r3', '')
    if not token or len(token) > 256:
        return None
    now = int(time.time())
    with _connect() as con:
        row = con.execute('''SELECT u.username,u.role,u.disabled FROM rnd_auth_sessions s
                              JOIN rnd_auth_users u ON u.id=s.user_id
                              WHERE s.token_hash=? AND s.expires_at>?''', (_digest_token(token), now)).fetchone()
        if not row or row['disabled']:
            return None
        return {'username': row['username'], 'role': row['role']}


def revoke(request: Request):
    token = request.cookies.get('rnd_session_r3', '')
    if token:
        with _connect() as con:
            con.execute('DELETE FROM rnd_auth_sessions WHERE token_hash=?', (_digest_token(token),))


def _allowed_origin(request: Request) -> bool:
    origin = request.headers.get('origin')
    allowed = {s.strip().rstrip('/') for s in os.getenv(
        'RND_AUTH_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if s.strip()}
    # Browser-origin state changes must be explicitly same-origin/allowlisted.
    return origin in allowed


async def guard(request: Request, call_next):
    try:
        mode = auth_mode()
    except RuntimeError:
        return JSONResponse({'detail': 'Cấu hình xác thực không hợp lệ'}, status_code=503)
    if mode == 'disabled':
        # This remains a local-only prototype. Do NOT expose the API on public interfaces.
        return await call_next(request)
    path = request.url.path
    public = path in ('/health/v4.5', '/health/v4.4', '/health') or path == '/api/v4.5/auth/login'
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and request.headers.get('origin') and not _allowed_origin(request):
        return JSONResponse({'detail': 'Nguồn yêu cầu không được phép'}, status_code=403)
    if public:
        return await call_next(request)
    user = current_user(request)
    if user is None:
        return JSONResponse({'detail': 'Yêu cầu đăng nhập'}, status_code=401)
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and not _allowed_origin(request):
        return JSONResponse({'detail': 'Thiếu Origin hợp lệ cho thao tác có phiên đăng nhập'}, status_code=403)
    is_persistent_write = (request.method == 'POST' and path.startswith('/api/v4.5/studies'))
    if is_persistent_write and user['role'] not in {'editor', 'admin'}:
        return JSONResponse({'detail': 'Không có quyền ghi dữ liệu nghiên cứu'}, status_code=403)
    request.state.rnd_user = user
    return await call_next(request)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


def register_auth_routes(app):
    @app.post('/api/v4.5/auth/login')
    def login_api(body: LoginRequest, request: Request):
        if auth_mode() != 'required':
            raise HTTPException(409, 'Chưa bật chế độ xác thực')
        # Deny login without an explicitly allowlisted browser Origin.
        # The Next.js same-origin fetch sends Origin on POST.
        if not _allowed_origin(request):
            raise HTTPException(403, 'Nguồn yêu cầu không được phép')
        user = login(body.username, body.password)
        if user is None:
            raise HTTPException(401, 'Thông tin đăng nhập không hợp lệ hoặc tài khoản đang bị khóa')
        result = JSONResponse({'username': user['username'], 'role': user['role']})
        result.set_cookie('rnd_session_r3', user['token'], max_age=SESSION_SECONDS, httponly=True,
                          secure=os.getenv('RND_AUTH_COOKIE_SECURE', '').lower() == 'true',
                          samesite='strict', path='/')
        return result

    @app.get('/api/v4.5/auth/me')
    def me_api(request: Request):
        if auth_mode() == 'disabled':
            return {'auth_enabled': False, 'role': 'local_preview'}
        return {**request.state.rnd_user, 'auth_enabled': True}

    @app.post('/api/v4.5/auth/logout')
    def logout_api(request: Request):
        revoke(request)
        response = JSONResponse({'ok': True})
        response.delete_cookie('rnd_session_r3', path='/', samesite='strict')
        return response
