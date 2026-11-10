'use client';
import {useState} from 'react';
import {Icon} from '@/components/Icons';
export default function Login(){
 const [password,setPassword]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');try{const response=await fetch('/api/session',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({password})});const payload=await response.json();if(!response.ok)throw new Error(payload.detail||'Không thể đăng nhập');window.location.replace('/')}catch(err){setError(err instanceof Error?err.message:'Đã có lỗi đăng nhập')}finally{setBusy(false)}}
 return <main className="login-screen"><form className="login-card" onSubmit={e=>void submit(e)}><div className="brand-mark"><Icon name="flask" size={29}/></div><div className="eyebrow">PHÒNG NGHIÊN CỨU MỸ PHẨM SỐ</div><h1>Cosmetic R&D</h1><p>Phân tích INCI, nghiên cứu nồng độ và lưu phiên bản công thức trên cùng một không gian.</p><label>Mã truy cập nội bộ<input required autoComplete="current-password" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Nhập mã truy cập"/></label>{error&&<div className="notice danger"><Icon name="alert" size={17}/><span>{error}</span></div>}<button className="btn primary" type="submit" disabled={busy}>{busy?'Đang xác thực…':'Mở phòng nghiên cứu'} <Icon name="arrow" size={17}/></button><div className="hint">Dữ liệu nghiên cứu nội bộ · Không chia sẻ mã truy cập</div></form></main>
}
