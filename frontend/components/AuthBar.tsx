'use client';
import { useEffect, useState } from 'react';

type Identity = { auth_enabled?: boolean; username?: string; role?: string };
export default function AuthBar() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);
  useEffect(() => {
    let active = true;
    fetch('/backend/api/v4.5/auth/me', { cache: 'no-store', credentials: 'same-origin' })
      .then(async r => {
        if (!r.ok) { if (active) setNeedsLogin(r.status === 401); return; }
        const value = await r.json();
        if (active) setIdentity(value);
      })
      .catch(() => {});
    return () => { active = false; };
  }, []);
  if (needsLogin) return <aside style={{ padding: '0.65rem 1rem', background: '#FFF3E2', color: '#633700', textAlign:'center' }}>
    Cần đăng nhập để truy cập dữ liệu R&D. <a href="/login" style={{fontWeight:700,textDecoration:'underline'}}>Đăng nhập</a>
  </aside>;
  if (!identity?.auth_enabled) return null;
  return <aside style={{ display:'flex', justifyContent:'flex-end', gap:16, padding:'0.5rem 1.5rem', background:'#F0F5F8', color:'#23445B', fontSize:14 }}>
    <span>{identity.username} · {identity.role}</span>
    <button type="button" onClick={async () => {
      await fetch('/backend/api/v4.5/auth/logout', {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'}});
      window.location.href='/login';
    }}>Đăng xuất</button>
  </aside>;
}
