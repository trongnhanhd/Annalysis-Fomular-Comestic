'use client';
import { useEffect, useMemo, useState } from 'react';
import type {Analysis, CatalogStudy, Formula, LegalRecord, Market, Product, Research, Run, Tab} from '@/lib/types';

const MARKETS: Market[] = ['EU','US','KR','CN','VN','ASEAN'];
function inciNames(s:string):string[] { return s.split(/[,;\n]+/).map(x=>x.trim()).filter(Boolean); }
const RC_STATUS: Record<string,string> = {
  EXCEEDS_NUMERIC_MAX:'Vượt giới hạn số trong quy tắc',
  NOT_ABOVE_NUMERIC_MAX:'Không vượt giới hạn số trong quy tắc',
  NEEDS_BASIS_CONVERSION:'Cần quy đổi sang cơ sở tính của quy tắc',
  MANUAL_CONDITIONS_REQUIRED:'Cần kiểm tra điều kiện thủ công',
  NEEDS_LEGAL_REVIEW:'Cần rà soát pháp lý — không có bản ghi khớp, không có nghĩa là được phép',
  RESTRICTED_OR_NOT_AUTHORIZED:'Bị hạn chế hoặc không được phép',
};
const menu: Array<{id:Tab;icon:string;label:string}> = [
  {id:'overview',icon:'◫',label:'Tổng quan'},
  {id:'analyze',icon:'⌁',label:'Phân tích INCI'},
  {id:'products',icon:'▦',label:'Thư viện sản phẩm'},
  {id:'research',icon:'◇',label:'Nghiên cứu khoa học'},
  {id:'regulatory',icon:'◎',label:'Pháp lý 6 thị trường'},
  {id:'formulas',icon:'▧',label:'Công thức giả thuyết'},
];
const titles:Record<Tab,string> = {
  overview:'Tổng quan phòng nghiên cứu', analyze:'Phân tích ngược công thức INCI', products:'Thư viện sản phẩm',
  research:'Dữ liệu nghiên cứu & nguồn',regulatory:'Đối chiếu pháp lý đa thị trường',formulas:'Quản lý phiên bản công thức',
};
const fmt = (value:number) => value.toLocaleString('vi-VN', {maximumFractionDigits:2});
const shortDate = (s:string) => new Date(s).toLocaleDateString('vi-VN');
const errString=(e:unknown)=>e instanceof Error ? e.message : 'Đã xảy ra lỗi. Vui lòng thử lại.';
async function api<T>(url:string, init?:RequestInit):Promise<T> {
  const res = await fetch(`/api/bff/${url}`, {cache:'no-store',...init,
    headers:{'content-type':'application/json',...(init?.headers||{})}});
  const json:unknown = await res.json();
  if(!res.ok) {
    const obj = json as {detail?:string|unknown};
    const msg = typeof obj.detail === 'string' ? obj.detail : JSON.stringify(obj.detail || json);
    throw new Error(msg);
  }
  return json as T;
}
function Pill({children,tone='neutral'}:{children:React.ReactNode;tone?:'neutral'|'good'|'warn'|'bad'}) {
  return <span className={`pill ${tone}`}>{children}</span>;
}
function Empty({title,sub}:{title:string;sub:string}) {
  return <div className="empty"><div className="empty-art">✳</div><strong>{title}</strong><p>{sub}</p></div>;
}
function Field({title,children}:{title:string;children:React.ReactNode}){return <label className="field"><span>{title}</span>{children}</label>;}
function Metrics({label,value,foot,icon}:{label:string;value:string|number;foot:string;icon:string}) {
  return <div className="metric"><div className="metric-top"><span>{label}</span><span className="metric-icon">{icon}</span></div><div className="metric-value">{value}</div><div className="metric-foot">{foot}</div></div>;
}

export default function Workspace(){
  const [tab,setTab] = useState<Tab>('overview');
  const [products,setProducts] = useState<Product[]>([]);
  const [records,setRecords] = useState<Research[]>([]);
  const [curated,setCurated] = useState<CatalogStudy[]>([]);
  const [laws,setLaws] = useState<LegalRecord[]>([]);
  const [catalogCount,setCatalogCount] = useState(0);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState('');
  const [info,setInfo] = useState('');
  const [chosen,setChosen] = useState('');
  const [runs,setRuns] = useState<Run[]>([]);
  const [formulas,setFormulas] = useState<Formula[]>([]);
  const [result,setResult] = useState<Analysis|null>(null);
  const [running,setRunning] = useState(false);
  const [inci,setInci] = useState('Aqua, Glycerin, Niacinamide, Panthenol, Phenoxyethanol, Ethylhexylglycerin');
  const [market,setMarket] = useState<Market>('EU');
  const [kind,setKind] = useState('leave_on');
  const [productName,setProductName] = useState('Serum nghiên cứu mẫu');
  const [brand,setBrand] = useState('');
  const [knownRows,setKnownRows] = useState<Record<string,{pct:string;source:string}>>({});
  const [applyLimit,setApplyLimit] = useState(false);
  const [confirmedPreservative,setConfirmedPreservative] = useState(false);
  const [rForm,setRForm] = useState({inci:'',title:'',study_type:'clinical',source_url:'',doi:'',min_pct:'',max_pct:'',notes:''});
  const [rSearch,setRSearch] = useState('');
  const [reviewId,setReviewId] = useState('');
  const [reviewer,setReviewer] = useState('');
  const [reviewNote,setReviewNote] = useState('');
  const [formulaText,setFormulaText] = useState('');
  const [formulaName,setFormulaName] = useState('Công thức giả thuyết');
  const [formulaNotes,setFormulaNotes] = useState('');
  const [rcForm,setRcForm] = useState({market:'EU',category:'leave_on',purpose:'preservative',inci:'',pct:'',basis:'ingredient'});
  const [rcResult,setRcResult] = useState<Record<string,unknown>|null>(null);
  const [pending,setPending] = useState(false);
  const activeProduct = products.find(p=>p.id===chosen);
  const totalFormula = useMemo(()=>{
    return formulaText.split('\n').reduce((sum,line)=>{
      const i = line.lastIndexOf(':');
      return sum + (i===-1?0:(Number(line.slice(i+1).trim().replace(',','.'))||0));
    },0);
  },[formulaText]);

  async function reload() {
    try {
      const [p,r,c,l] = await Promise.all([
        api<{data:Product[]}>('workspace/products'),api<{data:Research[]}>('workspace/research'),
        api<{data:CatalogStudy[];metadata:{record_count:number}}>('v2/catalog/research'),
        api<{data:LegalRecord[]}>('v2/catalog/regulatory')]);
      setProducts(p.data);setRecords(r.data);setCurated(c.data);setCatalogCount(c.metadata.record_count);setLaws(l.data);setError('');
    } catch(e) { setError(errString(e)); }
    finally { setLoading(false); }
  }
  useEffect(()=>{void reload();},[]);
  useEffect(()=>{
    if(!chosen){setRuns([]);setFormulas([]);return;}
    void Promise.all([api<{data:Run[]}>(`workspace/products/${chosen}/analyses`),api<{data:Formula[]}>(`workspace/products/${chosen}/formulas`)]).then(([a,f])=>{setRuns(a.data);setFormulas(f.data)}).catch(e=>setError(errString(e)));
  },[chosen]);
  function go(t:Tab){setInfo('');setError('');setTab(t);}
  function handleProduct(p:Product){setChosen(p.id);setMarket(p.market);setInci(p.inci);setProductName(p.name);setBrand(p.brand);setKind(p.product_type);setFormulaText(p.inci.split(',').map(s=>`${s.trim()}: 0`).join('\n'));go('formulas');}
  function requestPayload(){
    const data:Record<string,unknown> = {inci,market,product_type:kind,include_catalog_evidence:true,
      apply_catalog_limits:applyLimit,
      intended_use:applyLimit && confirmedPreservative ? {'Phenoxyethanol':'preservative'}:{}};
    const known:Record<string,{value:number;source:string}>={};
    for(const name of inciNames(inci)){
      const row=knownRows[name];
      if(!row?.pct.trim()) continue;
      const v=Number(row.pct.replace(',','.'));
      if(!Number.isFinite(v)||v<0||v>100) throw new Error(`${name}: nồng độ công bố phải là số từ 0 đến 100.`);
      known[name]={value:v,source:row.source.trim()||'chưa ghi nguồn'};
    }
    const total=Object.values(known).reduce((s,x)=>s+x.value,0);
    if(total>100+1e-9) throw new Error(`Tổng các % công bố là ${total}%, vượt 100%.`);
    if(Object.keys(known).length) data.known_pct=known;
    return data;
  }
  async function runAnalysis(){
    setRunning(true);setError('');setInfo('');
    try { const data=await api<Analysis>('v2/analyze',{method:'POST',body:JSON.stringify(requestPayload())});setResult(data);setInfo(data.status==='feasible'?'Đã tính xong miền nồng độ khả thi.':'Ràng buộc mâu thuẫn; xem chi tiết bên dưới.'); }
    catch(e){setError(errString(e));}
    finally{setRunning(false);}
  }
  async function saveAnalysis(){
    if(!result) return;
    setPending(true);setError('');
    try {
      const payload=requestPayload();
      const p=await api<Product>('workspace/products',{method:'POST',body:JSON.stringify({name:productName,brand,inci,market,product_type:kind})});
      await api<Run>(`workspace/products/${p.id}/analyses`,{method:'POST',body:JSON.stringify(payload)});
      setChosen(p.id);await reload();setInfo('Đã lưu sản phẩm và bản phân tích với phiên bản dữ liệu nguồn.');
    } catch(e){setError(errString(e));}
    finally{setPending(false);}
  }
  async function createResearch(e:React.FormEvent){
    e.preventDefault();setPending(true);setError('');
    try {
      const payload={...rForm,min_pct:rForm.min_pct?Number(rForm.min_pct.replace(',','.')):null,
        max_pct:rForm.max_pct?Number(rForm.max_pct.replace(',','.')):null};
      await api('workspace/research',{method:'POST',body:JSON.stringify(payload)});
      setRForm({inci:'',title:'',study_type:'clinical',source_url:'',doi:'',min_pct:'',max_pct:'',notes:''});
      await reload();setInfo('Đã lưu nghiên cứu ở trạng thái NHÁP, chưa được dùng làm bằng chứng của bộ giải.');
    }catch(e){setError(errString(e))}finally{setPending(false)}
  }
  async function checkRegulatory(e:React.FormEvent){
    e.preventDefault();setPending(true);setError('');
    try {
      const pct=Number(rcForm.pct.replace(',','.'));
      if(Number.isNaN(pct)||pct<0) throw new Error('Nồng độ phải là số không âm.');
      setRcResult(await api<Record<string,unknown>>('v2/regulatory/check',{method:'POST',body:JSON.stringify({...rcForm,pct})}));
    }catch(e){setError(errString(e))}finally{setPending(false)}
  }
  async function review(decision:'reviewed'|'rejected') {
    if(!reviewId) return;
    setPending(true);setError('');
    try{
      await api(`workspace/research/${reviewId}/review`,{method:'POST',body:JSON.stringify({decision,reviewer,review_note:reviewNote})});
      await reload();setReviewId('');setReviewNote('');setInfo('Đã ghi quyết định kiểm duyệt. Dữ liệu vẫn không tự động thay đổi công thức LP.');
    }catch(e){setError(errString(e))}finally{setPending(false)}
  }
  async function saveFormula(e:React.FormEvent){
    e.preventDefault();if(!chosen)return;setPending(true);setError('');
    try{
      const ingredients=formulaText.split('\n').filter(l=>l.trim()).map(line=>{
        const pos=line.lastIndexOf(':');if(pos<1) throw new Error('Mỗi dòng phải có dạng INCI: %');
        const pct=Number(line.slice(pos+1).trim().replace(',','.'));
        if(!Number.isFinite(pct))throw new Error(`Tỷ lệ không hợp lệ: ${line}`);
        return {inci:line.slice(0,pos).trim(),pct};
      });
      await api(`workspace/products/${chosen}/formulas`,{method:'POST',body:JSON.stringify({name:formulaName,notes:formulaNotes,ingredients})});
      const f=await api<{data:Formula[]}>(`workspace/products/${chosen}/formulas`);setFormulas(f.data);setInfo('Đã lưu bản công thức mới với nhãn GIẢ THUYẾT.');
    }catch(e){setError(errString(e));}finally{setPending(false)}
  }
  function exportJson(){
    if(!result)return;
    const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json;charset=utf-8'});
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='phan-tich-inci.json';a.click();URL.revokeObjectURL(url);
  }
  async function logout(){await fetch('/api/session',{method:'DELETE'});window.location.href='/login';}
  const shownResearch=records.filter(r=>`${r.inci} ${r.title}`.toLowerCase().includes(rSearch.toLowerCase()));
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">✳</div><div><div className="brand-title">COSMETIC <b>R&D</b></div><div className="brand-sub">INTELLIGENCE LAB · V2.2</div></div></div>
      <div className="side-label">KHÔNG GIAN LÀM VIỆC</div>
      <nav aria-label="Điều hướng chính">{menu.map(item=><button key={item.id} onClick={()=>go(item.id)} className={`nav-item ${tab===item.id?'active':''}`}><span className="nav-icon">{item.icon}</span>{item.label}{tab===item.id&&<span className="nav-dot"/>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-note"><div className="online-indicator"/> <strong>Science-first</strong><p>Chỉ sử dụng dữ liệu có nguồn. Không tự suy diễn % tối ưu.</p></div>
      <button className="logout" onClick={logout}>↪ Đăng xuất</button></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="crumb">LAB WORKSPACE <span>/</span> <strong>{menu.find(x=>x.id===tab)?.label}</strong></div><div className="top-right"><span className="server-indicator">● Nghiên cứu nội bộ</span><div className="avatar">RD</div></div></header>
      <div className="content">
        <div className="page-heading"><div><div className="eyebrow">COSMETIC R&D / RESEARCH WORKSPACE</div><h1>{titles[tab]}</h1><p>{tab==='overview'?'Một hệ thống, nhiều nguồn dữ liệu, mọi kết luận đều có dấu vết.':tab==='analyze'?'Khôi phục miền nồng độ khả thi từ nhãn INCI và ràng buộc đã xác minh.':tab==='regulatory'?'Sáu khu vực được hỗ trợ về cấu trúc, phạm vi văn bản hiện chưa đầy đủ.':'Tách biệt dữ liệu thực nghiệm, công bố và giả thuyết để nghiên cứu có thể kiểm toán.'}</p></div><div className="heading-actions"><span className="version">● V2.2 MVP</span><button className="btn light" onClick={()=>void reload()}>↻ Làm mới</button></div></div>
        {error&&<div className="notice danger"><strong>Có lỗi:</strong> {error} <button onClick={()=>setError('')}>×</button></div>}
        {info&&<div className="notice success">✓ {info}<button onClick={()=>setInfo('')}>×</button></div>}
        {loading&&<div className="notice">Đang tải dữ liệu thư viện…</div>}
        {tab==='overview'&&<>
          <div className="metrics-grid"><Metrics label="Sản phẩm nghiên cứu" value={products.length} foot="Hồ sơ đã lưu trong cơ sở dữ liệu" icon="▦"/><Metrics label="Nguồn nghiên cứu gốc" value={catalogCount} foot="Bằng chứng tuyển chọn V2.1" icon="◇"/><Metrics label="Tài liệu nội bộ" value={records.length} foot="Nháp và bản ghi đã kiểm duyệt" icon="▤"/><Metrics label="Thị trường" value={6} foot="Quy tắc nhãn; pháp lý cần bổ sung" icon="◉"/></div>
          <div className="two-col"><section className="panel"><div className="panel-head"><div><div className="section-eyebrow">BẮT ĐẦU NGHIÊN CỨU</div><h2>Quy trình làm việc</h2></div><Pill tone="good">Khuyến nghị</Pill></div><div className="steps"><div><b>01</b><strong>Nhập danh sách INCI</strong><span>Giữ nguyên thứ tự thành phần trên nhãn.</span></div><div><b>02</b><strong>Gắn dữ liệu định lượng</strong><span>Chỉ khóa % có bằng chứng đúng bản chất hoạt chất.</span></div><div><b>03</b><strong>Đọc khoảng khả thi</strong><span>Kiểm tra pháp lý, bằng chứng và giả định LP.</span></div><div><b>04</b><strong>Lưu hồ sơ & công thức</strong><span>Lưu từng phiên bản để đối chiếu thử nghiệm.</span></div></div><button className="btn primary" onClick={()=>go('analyze')}>Bắt đầu phân tích →</button></section>
          <section className="panel"><div className="panel-head"><div><div className="section-eyebrow">QUẢN TRỊ BẰNG CHỨNG</div><h2>Nguyên tắc dữ liệu</h2></div><span className="orb">✳</span></div><div className="rule-list"><div><span className="rule-color teal"/><div><b>Miền khả thi LP</b><p>Đúng theo ràng buộc đã nhập; không phải % đo thực tế.</p></div></div><div><span className="rule-color amber"/><div><b>Dữ liệu nghiên cứu</b><p>Gắn DOI / PMID / nền thử nghiệm, không thay đổi miền LP.</p></div></div><div><span className="rule-color coral"/><div><b>Pháp lý</b><p>Chỉ áp ràng buộc khi khớp thị trường, mục đích và loại sản phẩm.</p></div></div><div><span className="rule-color grey"/><div><b>Khoảng dự đoán AI</b><p>Chưa hiệu chuẩn, hiển thị “chưa có dữ liệu” thay vì số tự tạo.</p></div></div></div></section></div>
          <section className="panel"><div className="panel-head"><div><div className="section-eyebrow">THƯ VIỆN SẢN PHẨM</div><h2>Sản phẩm gần đây</h2></div><button className="text-button" onClick={()=>go('products')}>Xem tất cả →</button></div>{products.length? <div className="table-wrap"><table><thead><tr><th>Sản phẩm</th><th>Thị trường</th><th>Loại</th><th>Ngày tạo</th><th></th></tr></thead><tbody>{products.slice(0,5).map(p=><tr key={p.id}><td><b>{p.name}</b><div className="muted">{p.brand||'Chưa khai báo thương hiệu'}</div></td><td><Pill>{p.market}</Pill></td><td>{p.product_type}</td><td>{shortDate(p.created_at)}</td><td><button className="text-button" onClick={()=>handleProduct(p)}>Mở →</button></td></tr>)}</tbody></table></div>:<Empty title="Chưa có sản phẩm" sub="Khi lưu lần phân tích đầu tiên, sản phẩm sẽ xuất hiện ở đây."/>}</section>
        </>}
        {tab==='analyze'&&<div className="analysis-layout"><section className="panel input-panel"><div className="panel-head"><div><div className="section-eyebrow">INPUT / RÀNG BUỘC</div><h2>Thông tin sản phẩm</h2></div><Pill>LP SOLVER</Pill></div>
          <div className="form-grid"><Field title="Tên sản phẩm"><input value={productName} onChange={e=>setProductName(e.target.value)}/></Field><Field title="Thương hiệu (nếu có)"><input value={brand} onChange={e=>setBrand(e.target.value)} placeholder="Tên thương hiệu"/></Field><Field title="Thị trường"><select value={market} onChange={e=>setMarket(e.target.value as Market)}>{MARKETS.map(x=><option key={x}>{x}</option>)}</select></Field><Field title="Loại sản phẩm"><select value={kind} onChange={e=>setKind(e.target.value)}><option value="leave_on">Lưu lại trên da</option><option value="rinse_off">Rửa trôi</option><option value="body_lotion">Sữa dưỡng thể</option><option value="other">Khác</option></select></Field></div>
          <Field title="Danh sách thành phần INCI theo thứ tự"><textarea className="inci-editor" rows={6} value={inci} onChange={e=>setInci(e.target.value)} placeholder="Aqua, Glycerin, Niacinamide…"/></Field><div className="field-note">Ngăn cách bằng dấu phẩy hoặc xuống dòng. Trung Quốc: nhóm vi lượng 0,1% cần khai báo riêng trong API nâng cao.</div>
          <div className="subsection"><h3>Nồng độ công bố có nguồn (từng nguyên liệu)</h3><p>Để trống nếu không có % công bố; khi đó gợi ý nằm trong khoảng min–max. Nguồn là không bắt buộc, nhưng % không có nguồn sẽ được ghi là "chưa ghi nguồn" và chỉ coi là giả định của người dùng.</p><div className="table-wrap"><table><thead><tr><th>INCI</th><th>% công bố (w/w)</th><th>Nguồn</th></tr></thead><tbody>{inciNames(inci).map(name=><tr key={name}><td><strong>{name}</strong></td><td><input inputMode="decimal" placeholder="Để trống" value={knownRows[name]?.pct??''} onChange={e=>setKnownRows({...knownRows,[name]:{pct:e.target.value,source:knownRows[name]?.source??''}})}/></td><td><input placeholder="URL, DOI, COA hoặc tài liệu gốc" value={knownRows[name]?.source??''} onChange={e=>setKnownRows({...knownRows,[name]:{pct:knownRows[name]?.pct??'',source:e.target.value}})}/></td></tr>)}</tbody></table></div></div>
          <div className="subsection"><h3>Giới hạn pháp lý có kiểm soát</h3><label className="checkline"><input type="checkbox" checked={applyLimit} onChange={e=>setApplyLimit(e.target.checked)}/> Áp dụng mục pháp lý tuyển chọn phù hợp (nếu có)</label>{applyLimit&&<label className="checkline indent"><input type="checkbox" checked={confirmedPreservative} onChange={e=>setConfirmedPreservative(e.target.checked)}/> Tôi đã xác minh Phenoxyethanol được dùng làm chất bảo quản</label>}<div className="field-note">Kho pháp lý mới có dữ liệu mẫu EU Phenoxyethanol; chưa thể kết luận tuân thủ tổng thể.</div></div>
          <div className="action-row"><button className="btn primary" disabled={running||!inci.trim()} onClick={()=>void runAnalysis()}>{running?'Đang tính…':'⌁ Phân tích INCI'}</button><button className="btn light" disabled={!result||pending} onClick={()=>void saveAnalysis()}>{pending?'Đang lưu…':'▧ Lưu sản phẩm + phân tích'}</button></div>
        </section><section className="result-column"><div className="panel result-panel"><div className="panel-head"><div><div className="section-eyebrow">KẾT QUẢ / ĐẦU RA</div><h2>Khoảng nồng độ khả thi</h2></div>{result&&<Pill tone={result.status==='feasible'?'good':'bad'}>{result.status==='feasible'?'Khả thi':'Mâu thuẫn'}</Pill>}</div>
          {!result?<Empty title="Chưa có kết quả" sub="Nhập danh sách INCI và bấm Phân tích để tính miền nồng độ từng thành phần."/>:<>
            {result.status!=='feasible'?<div className="notice danger">{(result.issues||[]).join('; ')}{(result.explanation?.contradictions||[]).map((x,i)=><p key={i}>{x}</p>)}{(result.explanation?.data_needed||[]).map((x,i)=><p key={`d${i}`}>Cần kiểm tra: {x}</p>)}</div>:<><div className="result-meta"><span><b>{result.n_ingredients}</b> thành phần</span><span><b>{result.market}</b> thị trường</span><span><b>{result.possible_tail_boundaries?.length||0}</b> ranh giới khả thi</span></div><div className="table-wrap"><table className="results-table"><thead><tr><th>Nguyên liệu</th><th>Min %</th><th>Max %</th><th>Gợi ý (minh họa)</th></tr></thead><tbody>{(result.results||[]).map(item=><tr key={item.ingredient}><td><b>{item.ingredient}</b><div className="muted">#{item.position} · {item.research_evidence?.length||0} nguồn tham chiếu</div></td><td className="num">{fmt(item.min_pct)}</td><td className="num">{fmt(item.max_pct)}</td><td className="num">{item.suggested_pct!==undefined?fmt(item.suggested_pct):<Pill tone="warn">Chưa có</Pill>}</td></tr>)}</tbody></table></div>{result.suggested_composition&&<div className="notice warn">Tổng gợi ý <b>{fmt(result.suggested_composition.sum_listed_pct+result.suggested_composition.unlisted_pct)}%</b> — mục tiêu: {result.suggested_composition.objective==='preferred'?'% tối ưu đã xác minh':'điểm giữa khoảng khả thi'}. Đây là phương án minh họa thỏa ràng buộc, không phải ước tính hàm lượng.</div>}{result.explanation&&<div className="panel"><div className="panel-head"><div><div className="section-eyebrow">EXPLANATION</div><h2>Giải thích kết quả</h2></div></div>{result.explanation.contradictions.length>0&&<div className="notice danger"><b>Mâu thuẫn / lưu ý:</b><ul>{result.explanation.contradictions.map((x,i)=><li key={i}>{x}</li>)}</ul></div>}<div className="mini-heading">GIẢ ĐỊNH</div><ul className="warning-list">{result.explanation.assumptions.map((x,i)=><li key={i}>{x}</li>)}</ul>{result.explanation.undetermined.length>0&&<><div className="mini-heading">CHƯA XÁC ĐỊNH</div><p>{result.explanation.undetermined.join(', ')}</p></>}<div className="mini-heading">CẦN THÊM DỮ LIỆU</div><ul className="warning-list">{result.explanation.data_needed.map((x,i)=><li key={i}>{x}</li>)}</ul><div className="mini-heading">LÝ DO TỪNG TỶ LỆ</div>{(result.results||[]).map(item=><details className="evidence-details" key={item.ingredient}><summary><b>{item.ingredient}</b><span>{item.explanation?.status==='fixed'?'cố định':item.explanation?.status==='undetermined'?'chưa xác định':'khoảng hẹp'} · {item.suggested_pct!==undefined?fmt(item.suggested_pct):'—'}%</span></summary><p>{item.explanation?.why}</p>{(item.explanation?.drivers||[]).map((d,i)=><p key={i} className="muted">{d}</p>)}{(item.explanation?.data_needed||[]).map((d,i)=><p key={i} className="muted">Cần: {d}</p>)}</details>)}</div>}</>}
            <div className="result-bottom"><button className="btn light" onClick={exportJson}>↓ Xuất JSON</button><span>Chỉ là miền khả thi, không phải tỷ lệ thực nghiệm.</span></div>
          </>}</div>
          {result?.status==='feasible'&&<div className="panel"><div className="panel-head"><div><div className="section-eyebrow">PROVENANCE</div><h2>Bằng chứng & cảnh báo</h2></div></div>{(result.results||[]).filter(x=>x.research_evidence?.length).map(item=><details className="evidence-details" key={item.ingredient}><summary><b>{item.ingredient}</b><span>{item.research_evidence.length} tài liệu ↗</span></summary>{item.research_evidence.map((x,i)=><div className="evidence-row" key={i}><Pill>{x.category||'Nghiên cứu'}</Pill><span>{fmt(x.min_pct)}–{fmt(x.max_pct)}%</span>{x.source_url&&<a href={x.source_url} target="_blank" rel="noopener noreferrer">Mở tài liệu nguồn ↗</a>}<p>{x.matrix_match}</p></div>)}</details>)}<div className="mini-heading">LƯU Ý PHƯƠNG PHÁP</div><ul className="warning-list">{(result.warnings||[]).slice(0,5).map((x,i)=><li key={i}>{x}</li>)}</ul></div>}
        </section></div>}
        {tab==='products'&&<section className="panel"><div className="panel-head"><div><div className="section-eyebrow">PRODUCT LIBRARY</div><h2>Hồ sơ nghiên cứu sản phẩm</h2></div><button className="btn primary" onClick={()=>go('analyze')}>+ Phân tích mới</button></div>{!products.length?<Empty title="Chưa lưu sản phẩm nào" sub="Mở phần Phân tích INCI để tạo sản phẩm và bản phân tích đầu tiên."/>:<div className="table-wrap"><table><thead><tr><th>Tên sản phẩm / thương hiệu</th><th>Thị trường</th><th>Danh sách INCI</th><th>Ngày tạo</th><th>Thao tác</th></tr></thead><tbody>{products.map(p=><tr key={p.id}><td><strong>{p.name}</strong><div className="muted">{p.brand||'Không có thương hiệu'}</div></td><td><Pill>{p.market}</Pill></td><td className="ellipsis-col">{p.inci}</td><td>{shortDate(p.created_at)}</td><td><button className="text-button" onClick={()=>handleProduct(p)}>Xem hồ sơ →</button></td></tr>)}</tbody></table></div>}</section>}
        {tab==='research'&&<div className="research-layout"><section className="panel"><div className="panel-head"><div><div className="section-eyebrow">EVIDENCE REGISTRY</div><h2>Kho nghiên cứu</h2></div><Pill tone="good">{catalogCount} nguồn gốc</Pill></div><Field title="Tìm tài liệu nội bộ"><input placeholder="Tên nguyên liệu, tiêu đề…" value={rSearch} onChange={e=>setRSearch(e.target.value)}/></Field><div className="mini-heading">CATALOG KHOA HỌC TUYỂN CHỌN ({curated.length})</div>{curated.filter(r=>!rSearch||r.inci.toLowerCase().includes(rSearch.toLowerCase())).map((r,i)=><div className="study-card" key={i}><div><strong>{r.inci}</strong><Pill>{r.category}</Pill></div><p>Khoảng nghiên cứu: {fmt(r.min_pct)}–{fmt(r.max_pct)}% · {r.product_type||'Chưa rõ loại'}</p><a href={r.source_url} target="_blank" rel="noopener noreferrer">Nguồn nghiên cứu ↗</a></div>)}
          <div className="mini-heading spaced">TÀI LIỆU ĐƯỢC THÊM VÀO ({shownResearch.length})</div>{shownResearch.length?shownResearch.map(r=><div className="study-card" key={r.id}><div><strong>{r.inci}</strong><Pill tone={r.review_status==='reviewed'?'good':r.review_status==='rejected'?'bad':'warn'}>{r.review_status==='reviewed'?'Đã kiểm duyệt':r.review_status==='rejected'?'Không duyệt':'Bản nháp'}</Pill></div><h3>{r.title}</h3><p>{r.min_pct??'—'}–{r.max_pct??'—'}% · {r.study_type}</p><a href={r.source_url} target="_blank" rel="noopener noreferrer">Đọc tài liệu ↗</a>{r.review_status==='draft'&&<button className="text-button review-btn" onClick={()=>setReviewId(r.id)}>Kiểm duyệt thủ công →</button>}{reviewId===r.id&&<div className="review-form"><Field title="Người kiểm duyệt"><input value={reviewer} onChange={e=>setReviewer(e.target.value)}/></Field><Field title="Ghi chú đánh giá"><textarea value={reviewNote} onChange={e=>setReviewNote(e.target.value)} rows={2}/></Field><div className="action-row"><button disabled={pending||!reviewer||!reviewNote} className="btn primary" onClick={()=>void review('reviewed')}>Duyệt</button><button disabled={pending||!reviewer||!reviewNote} className="btn light" onClick={()=>void review('rejected')}>Không duyệt</button></div></div>}</div>):<p className="muted">Chưa có tài liệu nội bộ phù hợp.</p>}</section>
          <section className="panel"><div className="panel-head"><div><div className="section-eyebrow">ADD EVIDENCE</div><h2>Thêm tài liệu nghiên cứu</h2></div></div><div className="notice warn">Tài liệu mới luôn ở trạng thái <b>nháp</b>; chỉ người kiểm duyệt được xác nhận, và không tự đưa vào bộ giải.</div><form onSubmit={e=>void createResearch(e)} className="form-stack"><Field title="Tên INCI"><input required value={rForm.inci} onChange={e=>setRForm({...rForm,inci:e.target.value})}/></Field><Field title="Tên nghiên cứu"><input required value={rForm.title} onChange={e=>setRForm({...rForm,title:e.target.value})}/></Field><Field title="Loại nghiên cứu"><select value={rForm.study_type} onChange={e=>setRForm({...rForm,study_type:e.target.value})}><option value="clinical">Thử nghiệm lâm sàng</option><option value="measured_market_product">Đo trên sản phẩm thị trường</option><option value="preservation_challenge">Thử thách bảo quản</option><option value="other">Khác</option></select></Field><Field title="URL tài liệu gốc"><input type="url" required placeholder="https://pubmed.ncbi.nlm.nih.gov/..." value={rForm.source_url} onChange={e=>setRForm({...rForm,source_url:e.target.value})}/></Field><Field title="DOI (nếu có)"><input value={rForm.doi} onChange={e=>setRForm({...rForm,doi:e.target.value})}/></Field><div className="form-grid"><Field title="Min %"><input value={rForm.min_pct} onChange={e=>setRForm({...rForm,min_pct:e.target.value})}/></Field><Field title="Max %"><input value={rForm.max_pct} onChange={e=>setRForm({...rForm,max_pct:e.target.value})}/></Field></div><Field title="Ghi chú / bối cảnh nghiên cứu"><textarea rows={3} value={rForm.notes} onChange={e=>setRForm({...rForm,notes:e.target.value})}/></Field><button disabled={pending} className="btn primary" type="submit">+ Lưu tài liệu nháp</button></form></section></div>}
        {tab==='regulatory'&&<><div className="notice warn"><b>Phạm vi dữ liệu chưa đầy đủ:</b> Hệ thống hỗ trợ đọc quy tắc ghi nhãn của sáu thị trường nhưng catalog giới hạn nguyên liệu hiện chỉ có mục tuyển chọn. “Không có dữ liệu” không đồng nghĩa “được phép sử dụng”.</div><div className="market-grid">{MARKETS.map(m=><div className="market-card" key={m}><div className="market-title"><strong>{m}</strong><span>↗</span></div><p>{({EU:'Liên minh Châu Âu',US:'Hoa Kỳ',KR:'Hàn Quốc',CN:'Trung Quốc',VN:'Việt Nam',ASEAN:'Khu vực ASEAN'} as Record<Market,string>)[m]}</p><div><Pill tone={laws.some(l=>l.market===m)?'warn':'neutral'}>{laws.some(l=>l.market===m)?`${laws.filter(l=>l.market===m).length} mục tham khảo`:'Chưa có mục giới hạn'}</Pill></div></div>)}</div><section className="panel"><div className="panel-head"><div><div className="section-eyebrow">REGULATORY REFERENCES</div><h2>Những mục pháp lý đã tuyển chọn</h2></div></div>{laws.length?<div className="table-wrap"><table><thead><tr><th>INCI</th><th>Thị trường</th><th>Chức năng</th><th>Giới hạn</th><th>Nguồn</th></tr></thead><tbody>{laws.map((law,i)=><tr key={i}><td><strong>{law.inci}</strong></td><td>{law.market}</td><td>{law.intended_use}</td><td>{fmt(law.max_pct)}%</td><td><a href={law.source_url} target="_blank" rel="noopener noreferrer">Văn bản ↗</a></td></tr>)}</tbody></table></div>:<Empty title="Chưa có bản ghi" sub="Kho giới hạn cần được rà soát, nhập có nguồn và duyệt thủ công."/>}</section><section className="panel"><div className="panel-head"><div><div className="section-eyebrow">PRELIMINARY SCREEN</div><h2>Kiểm tra sơ bộ theo bộ luật tham chiếu</h2></div></div><form onSubmit={e=>void checkRegulatory(e)} className="form-stack"><Field title="Thị trường"><select value={rcForm.market} onChange={e=>setRcForm({...rcForm,market:e.target.value})}>{MARKETS.map(m=><option key={m} value={m}>{m}</option>)}</select></Field><Field title="Loại sản phẩm (product_scope)"><input value={rcForm.category} onChange={e=>setRcForm({...rcForm,category:e.target.value})}/></Field><Field title="Tên INCI"><input value={rcForm.inci} onChange={e=>setRcForm({...rcForm,inci:e.target.value})}/></Field><Field title="Nồng độ (% w/w)"><input value={rcForm.pct} onChange={e=>setRcForm({...rcForm,pct:e.target.value})}/></Field><button type="submit" className="btn primary" disabled={pending||!rcForm.inci.trim()||!rcForm.pct.trim()}>Kiểm tra</button></form>{rcResult&&<div className="notice warn"><b>{RC_STATUS[String(rcResult.status)]??String(rcResult.status)}</b>{rcResult.limit_pct!==undefined&&<> · giới hạn {String(rcResult.limit_pct)}%</>}{rcResult.rule_id!==undefined&&<> · quy tắc {String(rcResult.rule_id)}</>}<p>{String(rcResult.disclaimer)}</p></div>}</section></>}
        {tab==='formulas'&&<div className="two-col"><section className="panel"><div className="panel-head"><div><div className="section-eyebrow">FORMULATION VERSIONING</div><h2>Tạo công thức giả thuyết</h2></div><Pill tone="warn">Không xác nhận thực nghiệm</Pill></div><Field title="Chọn sản phẩm"><select value={chosen} onChange={e=>{setChosen(e.target.value);const p=products.find(p=>p.id===e.target.value);if(p)setFormulaText(p.inci.split(',').map(s=>`${s.trim()}: 0`).join('\n'));}}><option value="">— Chọn sản phẩm —</option>{products.map(p=><option key={p.id} value={p.id}>{p.name} ({p.market})</option>)}</select></Field>{!activeProduct?<Empty title="Chưa chọn sản phẩm" sub="Hãy lưu phân tích INCI, sau đó chọn sản phẩm để dựng công thức giả thuyết."/>:<form onSubmit={e=>void saveFormula(e)} className="form-stack"><Field title="Tên phiên bản"><input value={formulaName} onChange={e=>setFormulaName(e.target.value)}/></Field><Field title="Công thức (% w/w, mỗi dòng INCI: %) "><textarea className="formula-editor" rows={11} value={formulaText} onChange={e=>setFormulaText(e.target.value)} placeholder={'Aqua: 90\nGlycerin: 5\nNiacinamide: 5'}/></Field><div className={`sum-line ${Math.abs(totalFormula-100)<.0001?'sum-ok':'sum-bad'}`}><span>Tổng tỷ lệ</span><strong>{fmt(totalFormula)} / 100%</strong></div><Field title="Ghi chú quy trình / điều kiện"><textarea rows={3} value={formulaNotes} onChange={e=>setFormulaNotes(e.target.value)} placeholder="pH dự kiến, điều kiện pha, những điểm cần thử nghiệm…"/></Field><div className="notice warn">Chỉ lưu giả thuyết công thức; không suy ra độ ổn định, an toàn hay đạt thử thách bảo quản.</div><button type="submit" className="btn primary" disabled={pending||Math.abs(totalFormula-100)>.0001}>+ Lưu phiên bản mới</button></form>}</section><section className="panel"><div className="panel-head"><div><div className="section-eyebrow">VERSION HISTORY</div><h2>Lịch sử hồ sơ</h2></div></div>{activeProduct?<><div className="product-summary"><h3>{activeProduct.name}</h3><div className="muted">{activeProduct.brand||'Sản phẩm nghiên cứu'} · {activeProduct.market}</div><p>{activeProduct.inci}</p></div><div className="mini-heading">CÁC BẢN PHÂN TÍCH ĐÃ LƯU ({runs.length})</div>{runs.length?runs.map(r=><div className="history-item" key={r.id}><strong>Phân tích {shortDate(r.created_at)}</strong><Pill tone={r.status==='feasible'?'good':'bad'}>{r.status}</Pill></div>):<p className="muted">Chưa có bản phân tích.</p>}<div className="mini-heading spaced">CÔNG THỨC GIẢ THUYẾT ({formulas.length})</div>{formulas.length?formulas.map(f=><div className="history-item" key={f.id}><div><strong>V{f.version} · {f.name}</strong><p>{f.ingredients.length} nguyên liệu · {shortDate(f.created_at)}</p></div><Pill tone="warn">Giả thuyết</Pill><button className="text-button" onClick={()=>{setFormulaText(f.ingredients.map(i=>`${i.inci}: ${i.pct}`).join('\n'));setFormulaName(`${f.name} (bản mới)`);}}>Sao chép</button></div>):<p className="muted">Chưa có phiên bản công thức.</p>}</>:<Empty title="Thư viện chưa có lựa chọn" sub="Chọn sản phẩm ở cột bên trái."/>}</section></div>}
      </div>
      <footer className="footer"><span>© Cosmetic R&D Intelligence · Nghiên cứu có nguồn và có kiểm toán</span><span>Không thay thế kiểm nghiệm phòng lab hoặc đánh giá pháp lý chuyên gia</span></footer>
    </main>
  </div>;
}
