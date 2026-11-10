'use client';
import { FormEvent, useState } from 'react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const response = await fetch('/backend/api/v4.5/auth/login', {
        method:'POST', headers:{'Content-Type':'application/json'}, credentials:'same-origin',
        body:JSON.stringify({username, password}),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Đăng nhập thất bại (HTTP ${response.status})`);
      }
      window.location.href='/experiments';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể đăng nhập');
    } finally { setBusy(false); setPassword(''); }
  }
  return <main style={{ maxWidth:460, padding:32, margin:'8vh auto',fontFamily:'system-ui,sans-serif' }}>
    <a href="/">← Formula Intelligence</a>
    <h1>Đăng nhập R&D</h1>
    <p>Truy cập bản thử nghiệm nội bộ V4.5.2-R3. Chưa được phép triển khai công khai.</p>
    <form onSubmit={signIn} style={{display:'grid',gap:16}}>
      <label>Tài khoản<input required autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} style={{display:'block',width:'100%',padding:10}} /></label>
      <label>Mật khẩu<input required type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} style={{display:'block',width:'100%',padding:10}} /></label>
      {error && <p role="alert" style={{color:'#A12825'}}>{error}</p>}
      <button disabled={busy} type="submit" style={{padding:12}}>{busy?'Đang xác thực...':'Đăng nhập'}</button>
    </form>
  </main>;
}
