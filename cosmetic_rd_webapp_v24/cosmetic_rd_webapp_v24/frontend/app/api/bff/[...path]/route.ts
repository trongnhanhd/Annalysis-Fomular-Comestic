import { cookies } from 'next/headers';
import { validSession, cookieName } from '@/lib/auth';
export const dynamic = 'force-dynamic';
type Ctx = { params: Promise<{ path: string[] }> };
async function handler(req: Request, ctx: Ctx): Promise<Response> {
  const session = (await cookies()).get(cookieName)?.value;
  if (!validSession(session)) return Response.json({detail:'Phiên truy cập đã hết hạn'}, {status:401});
  const { path } = await ctx.params;
  if (!path?.length || !['v2','workspace'].includes(path[0]) || path.some(s => !/^[a-zA-Z0-9_.-]+$/.test(s))) {
    return Response.json({detail:'Đường dẫn không hợp lệ'}, {status:400});
  }
  const backend = process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000';
  const url = new URL(`/api/${path.join('/')}`, backend);
  url.search = new URL(req.url).search;
  const headers: Record<string,string> = {Accept:'application/json'};
  if (path[0] === 'workspace' && process.env.WORKSPACE_API_KEY) headers['x-api-key'] = process.env.WORKSPACE_API_KEY;
  if (req.method !== 'GET' && req.method !== 'HEAD') headers['content-type'] = 'application/json';
  try {
    const response = await fetch(url, {method:req.method, headers, body:req.method==='GET' ? undefined : await req.text(), cache:'no-store', redirect:'manual'});
    return new Response(await response.text(), {status:response.status, headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}});
  } catch {
    return Response.json({detail:'Không kết nối được FastAPI; kiểm tra dịch vụ backend'}, {status:502});
  }
}
export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const DELETE = handler;
