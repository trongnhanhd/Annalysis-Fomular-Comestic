"""Actual Chromium smoke: Next pages and FastAPI via the /backend rewrite.

Read-only: does not create studies, batches or synthetic measurements.
Usage: python scripts/browser_smoke_v452.py [http://127.0.0.1:3000]
Requires running Next and API and 'pip install playwright; playwright install chromium'.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = (sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:3000').rstrip('/')
OUTPUT = Path(os.environ.get('RND_SMOKE_OUTPUT', '/tmp/formula-intelligence-browser-smoke'))
OUTPUT.mkdir(parents=True, exist_ok=True)
PAGES = [
    ('/', 'Tri thức nguyên liệu & bằng chứng khoa học'),
    ('/optimizer', 'Tối ưu cấu trúc công thức'),
    ('/experiments', 'Thiết kế & xác minh thí nghiệm'),
]


def main() -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    with sync_playwright() as p:
        launch_args = {'headless': True, 'args':['--no-sandbox']}
        chromium_path = os.environ.get('RND_CHROMIUM_PATH')
        if chromium_path:
            launch_args['executable_path'] = chromium_path
        browser = p.chromium.launch(**launch_args)
        page = browser.new_page(locale='vi-VN', viewport={'width':1440,'height':900})
        js_errors = []
        page.on('pageerror', lambda err: js_errors.append(str(err)))
        try:
            username = os.environ.get('RND_SMOKE_USERNAME', '')
            password = os.environ.get('RND_SMOKE_PASSWORD', '')
            if username or password:
                assert username and password, 'Both RND_SMOKE_USERNAME and RND_SMOKE_PASSWORD are required'
                response = page.goto(BASE_URL + '/login', wait_until='domcontentloaded', timeout=30000)
                assert response and response.status == 200, 'Login page unreachable'
                page.get_by_label('Tài khoản').fill(username)
                page.get_by_label('Mật khẩu').fill(password)
                page.get_by_role('button', name='Đăng nhập').click()
                page.wait_for_url('**/experiments', timeout=20000)
                user = page.evaluate("""async () => {
                  const r=await fetch('/backend/api/v4.5/auth/me');
                  return {status:r.status,body:await r.json()};
                }""")
                assert user['status']==200 and user['body'].get('username')==username, f'Authenticated browser session missing: {user}'
                print('PASS browser: credentials and HttpOnly cookie authenticated through Next rewrite')
            for route, title in PAGES:
                response = page.goto(BASE_URL + route, wait_until='domcontentloaded',timeout=30000)
                assert response and response.status == 200, f'{route}: HTTP {response.status if response else "no response"}'
                page.get_by_role('heading', name=title).wait_for(timeout=20000)
                print(f'PASS browser: {route} — {title}')
            health = page.evaluate('''async () => {
              const r=await fetch('/backend/health/v4.5', {cache:'no-store'});
              return {status:r.status,body: await r.json()};
            }''')
            assert health['status']==200 and health['body'].get('ok') is True, f'Next rewrite API failed: {health}'
            print('PASS browser: Next /backend rewrite -> FastAPI /health/v4.5')
            page.get_by_text('API: Đã kết nối').wait_for(timeout=15000)
            print('PASS browser: experiments page displays connected API')
            assert not js_errors, f'Uncaught client JavaScript errors: {js_errors}'
            print('PASS browser: no uncaught JavaScript errors during navigation')
            return 0
        except Exception:
            page.screenshot(path=str(OUTPUT/'failure.png'),full_page=True)
            (OUTPUT/'page.html').write_text(page.content(), encoding='utf-8')
            (OUTPUT/'browser_errors.json').write_text(json.dumps(js_errors,ensure_ascii=False,indent=2), encoding='utf-8')
            raise
        finally:
            browser.close()


if __name__ == '__main__':
    sys.exit(main())
