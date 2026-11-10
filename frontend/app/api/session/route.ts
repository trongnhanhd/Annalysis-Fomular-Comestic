import { NextRequest, NextResponse } from 'next/server';
import { cookieName, makeSession, validPassword } from '@/lib/auth';

export async function POST(req: NextRequest) {
  if (!process.env.WEB_ACCESS_TOKEN) return NextResponse.json({detail:'WEB_ACCESS_TOKEN chưa được cấu hình'}, {status:503});
  let value: unknown;
  try { ({ password: value } = await req.json()); } catch { return NextResponse.json({detail:'Dữ liệu không hợp lệ'}, {status:400}); }
  if (typeof value !== 'string' || !validPassword(value)) return NextResponse.json({detail:'Mã truy cập không đúng'}, {status:401});
  const res = NextResponse.json({ok:true});
  res.cookies.set(cookieName, makeSession(), {httpOnly:true, sameSite:'strict', secure:process.env.FORCE_SECURE_COOKIES==='1', path:'/', maxAge:60*60*8});
  return res;
}
export async function DELETE() {
  const res = NextResponse.json({ok:true});
  res.cookies.delete(cookieName);
  return res;
}
