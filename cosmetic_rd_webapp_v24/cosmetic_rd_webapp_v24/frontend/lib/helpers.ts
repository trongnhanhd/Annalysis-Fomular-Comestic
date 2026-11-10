import type {Claim, Market} from './types';
export const markets: Market[] = ['EU','US','KR','CN','VN','ASEAN'];
export const marketNames: Record<Market,string> = {EU:'Liên minh Châu Âu',US:'Hoa Kỳ',KR:'Hàn Quốc',CN:'Trung Quốc',VN:'Việt Nam',ASEAN:'ASEAN'};
export const marketShort: Record<Market,string> = {EU:'EU',US:'Mỹ',KR:'Hàn Quốc',CN:'Trung Quốc',VN:'Việt Nam',ASEAN:'ASEAN'};
export const kindNames: Record<string,string> = {leave_on:'Lưu trên da',rinse_off:'Rửa trôi',body_lotion:'Dưỡng thể',other:'Khác'};
export const number = (x:number) => Number(x.toFixed(5)).toLocaleString('vi-VN',{maximumFractionDigits:5});
export const date = (value:string) => {const d=new Date(value);return Number.isNaN(d.getTime())?'—':d.toLocaleDateString('vi-VN')};
export const ingredients = (raw:string) => raw.split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean);
export const parseNumber = (s:string) => Number(s.trim().replace(',','.'));
export const errorText = (err:unknown) => err instanceof Error?err.message:'Đã xảy ra lỗi ngoài dự kiến';
export function newClaim():Claim { return {id:`c-${Date.now()}-${Math.round(Math.random()*99999)}`,inci:'',value:'',unit:'percent',precision:'exact',source:''}; }
export function csv(rows:Array<Array<string|number>>):string { return '\ufeff'+rows.map(r=>r.map(cell=>'"'+String(cell).replace(/"/g,'""')+'"').join(',')).join('\r\n'); }
export function download(text:string, filename:string, type:string){
 const blob=new Blob([text],{type}); const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export async function api<T>(path:string,init?:RequestInit):Promise<T> {
 const response=await fetch(`/api/bff/${path}`,{cache:'no-store',...init,headers:{'content-type':'application/json',...init?.headers}});
 let payload:unknown;
 try{payload=await response.json()}catch{throw new Error(`Máy chủ phản hồi không hợp lệ (HTTP ${response.status})`)}
 if(!response.ok){const detail=(payload as {detail?:unknown})?.detail;throw new Error(typeof detail==='string'?detail:JSON.stringify(detail??payload))}
 return payload as T;
}
