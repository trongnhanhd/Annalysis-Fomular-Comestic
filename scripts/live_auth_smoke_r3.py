import os, subprocess, tempfile, time, sys, socket
from pathlib import Path
import httpx
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    env=os.environ.copy()
    env.update({'RND_AUTH_MODE':'required','RND_AUTH_DB_PATH':tmp+'/auth.sqlite3','V45_DB_PATH':tmp+'/rnd.sqlite3'})
    sys.path.insert(0,str(root))
    from auth_r3 import create_user
    old=os.environ.copy()
    os.environ.update({'RND_AUTH_DB_PATH':env['RND_AUTH_DB_PATH']})
    create_user('review.user','ReviewUserPassword2026!','viewer')
    os.environ.clear();os.environ.update(old)
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    process=subprocess.Popen([sys.executable,'-m','uvicorn','api_v45:app','--host','127.0.0.1','--port',str(port)],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        url=f'http://127.0.0.1:{port}'
        for _ in range(80):
            try:
                if httpx.get(url+'/health/v4.5',timeout=1).status_code==200:break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('uvicorn startup did not complete')
        with httpx.Client(base_url=url,timeout=10) as client:
            results={}
            results['health']=client.get('/health/v4.5').status_code
            results['anonymous_list']=client.get('/api/v4.5/studies').status_code
            results['login']=client.post('/api/v4.5/auth/login',headers={'Origin':'http://localhost:3000'},json={'username':'review.user','password':'ReviewUserPassword2026!'}).status_code
            results['authenticated_list']=client.get('/api/v4.5/studies').status_code
            results['viewer_write_denied']=client.post('/api/v4.5/studies',headers={'Origin':'http://localhost:3000'},json={}).status_code
            results['logout']=client.post('/api/v4.5/auth/logout',headers={'Origin':'http://localhost:3000'},json={}).status_code
            results['after_logout']=client.get('/api/v4.5/studies').status_code
            assert results=={'health':200,'anonymous_list':401,'login':200,'authenticated_list':200,'viewer_write_denied':403,'logout':200,'after_logout':401},results
            print('LIVE HTTP SMOKE PASS:',results)
    finally:
        process.terminate()
        try:process.wait(timeout=8)
        except subprocess.TimeoutExpired:process.kill()
