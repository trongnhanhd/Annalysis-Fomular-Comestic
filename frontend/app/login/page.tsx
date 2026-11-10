'use client';
import { useState } from 'react';
export default function Login() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function login(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const r = await fetch('/api/session',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({password})});
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail||'Không thể đăng nhập');
      window.location.href='/';
    } catch(e) { setError(e instanceof Error?e.message:'Lỗi đăng nhập'); } finally { setBusy(false); }
  }
  return <main className="login-screen"><form onSubmit={login} className="login-card">
    <div className="brand-mark big">✳</div><div className="eyebrow">PHÒNG NGHIÊN CỨU SỐ</div>
    <h1>Cosmetic R&D</h1><p>Đăng nhập để truy cập thư viện công thức và dữ liệu nghiên cứu.</p>
    <label>Mã truy cập nội bộ<input autoComplete="current-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Nhập mã truy cập" required /></label>
    {error&&<div className="notice danger">{error}</div>}
    <button disabled={busy} className="btn primary" type="submit">{busy?'Đang xác thực…':'Mở phòng nghiên cứu →'}</button>
    <div className="hint">Ứng dụng nội bộ · Không chia sẻ mã truy cập</div>
  </form></main>;
}
