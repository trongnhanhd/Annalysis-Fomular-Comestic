'use client';
import {useCallback,useEffect,useState} from 'react';
import type {CatalogStudy,LegalRecord,Product,Research,Tab} from '@/lib/types';
import {api,date,errorText} from '@/lib/helpers';
import {Icon} from './Icons';
import {Pill,Panel,PanelHeader,Empty,Notice} from './UI';
import {AnalysisView} from './AnalysisView';
import {ProductsView,ResearchView,RegulationView,FormulaView} from './LibraryViews';

const menu: {id:Tab;label:string;icon:string}[]=[
 {id:'overview',label:'Tổng quan',icon:'grid'},
 {id:'analyze',label:'Phân tích INCI',icon:'flask'},
 {id:'products',label:'Thư viện sản phẩm',icon:'layers'},
 {id:'research',label:'Nghiên cứu khoa học',icon:'book'},
 {id:'regulatory',label:'Pháp lý 6 thị trường',icon:'globe'},
 {id:'formulas',label:'Công thức giả thuyết',icon:'beaker'},
];
const headings:Record<Tab,{eyebrow:string;title:string;description:string}>={
 overview:{eyebrow:'TRANG CHỦ / PHÒNG NGHIÊN CỨU',title:'Tổng quan nghiên cứu',description:'Quản lý sản phẩm, bằng chứng và các phiên bản công thức trên cùng một không gian làm việc.'},
 analyze:{eyebrow:'PHÂN TÍCH / INCI INTELLIGENCE',title:'Phân tích ngược công thức',description:'Ước lượng khoảng nồng độ khả thi dựa trên thứ tự INCI, tỷ lệ công bố và ràng buộc đã xác minh.'},
 products:{eyebrow:'CƠ SỞ DỮ LIỆU / PRODUCTS',title:'Thư viện sản phẩm',description:'Lưu hồ sơ sản phẩm và lịch sử các lần phân tích có thể kiểm toán.'},
 research:{eyebrow:'KHO DỮ LIỆU / SCIENTIFIC EVIDENCE',title:'Thư viện nghiên cứu',description:'Đối chiếu tài liệu khoa học đã tuyển chọn với tài liệu do nhóm R&D nhập và kiểm duyệt.'},
 regulatory:{eyebrow:'ĐỐI CHIẾU / COMPLIANCE',title:'Pháp lý đa thị trường',description:'Tra cứu dữ liệu giới hạn có nguồn cho EU, Mỹ, Hàn Quốc, Trung Quốc, Việt Nam và ASEAN.'},
 formulas:{eyebrow:'FORMULATION / WORKBENCH',title:'Phòng phát triển công thức',description:'Tạo phiên bản công thức giả thuyết từ hồ sơ đã lưu; không nhầm lẫn với kết quả thử nghiệm.'},
};
type Message={text:string;tone:'info'|'warn'|'danger'|'success'};
export default function Workspace(){
 const [tab,setTab]=useState<Tab>('overview');const [mobileNav,setMobileNav]=useState(false);const [products,setProducts]=useState<Product[]>([]);const [studies,setStudies]=useState<CatalogStudy[]>([]);const [research,setResearch]=useState<Research[]>([]);const [laws,setLaws]=useState<LegalRecord[]>([]);const [selected,setSelected]=useState('');const [busy,setBusy]=useState(true);const [message,setMessage]=useState<Message|null>(null);const [libraryOnline,setLibraryOnline]=useState(false);const [catalogOnline,setCatalogOnline]=useState(false);
 const notify=useCallback((text:string,tone:Message['tone']='info')=>setMessage({text,tone}),[]);
 const reload=useCallback(async()=>{
  setBusy(true);
  const values=await Promise.allSettled([
   api<{data:Product[]}>('workspace/products'),api<{data:Research[]}>('workspace/research'),
   api<{data:CatalogStudy[]}>('v2/catalog/research'),api<{data:LegalRecord[]}>('v2/catalog/regulatory')
  ]);
  if(values[0].status==='fulfilled'){setProducts(values[0].value.data);setLibraryOnline(true)}else{setLibraryOnline(false)}
  if(values[1].status==='fulfilled')setResearch(values[1].value.data);
  if(values[2].status==='fulfilled'){setStudies(values[2].value.data);setCatalogOnline(true)}else setCatalogOnline(false);
  if(values[3].status==='fulfilled')setLaws(values[3].value.data);
  if(values.some(x=>x.status==='rejected'))setMessage({tone:'warn',text:'Một số dịch vụ chưa phản hồi. Kiểm tra FastAPI, PostgreSQL và khóa kết nối, sau đó bấm Tải lại.'});
  setBusy(false);
 },[]);
 useEffect(()=>{const readTab=()=>{const q=new URLSearchParams(window.location.search).get('tab');if(menu.some(x=>x.id===q))setTab(q as Tab)};readTab();window.addEventListener('popstate',readTab);void reload();return()=>window.removeEventListener('popstate',readTab)},[reload]);
 function navigate(to:Tab){setTab(to);setMobileNav(false);setMessage(null);window.history.pushState({},'',to==='overview'?'/':`/?tab=${to}`)}
 async function logout(){await fetch('/api/session',{method:'DELETE'});window.location.replace('/login')}
 function openProduct(id:string){setSelected(id);navigate('formulas')}
 const h=headings[tab];const reviewed=research.filter(r=>r.review_status==='reviewed').length;
 return <div className="app-shell">
  <aside className={`sidebar ${mobileNav?'show-mobile':''}`}>
   <div className="brand-lockup"><div className="brand-logo"><Icon name="flask" size={26}/></div><div><div className="brand-name">COSMETIC <span>R&D</span></div><div className="brand-caption">INTELLIGENCE WORKSPACE</div></div><button className="mobile-close" onClick={()=>setMobileNav(false)} aria-label="Đóng điều hướng"><Icon name="close"/></button></div>
   <div className="sidebar-section-title">KHÔNG GIAN LÀM VIỆC</div><nav aria-label="Điều hướng ứng dụng" className="sidebar-menu">{menu.map(m=><button key={m.id} className={`nav-link ${tab===m.id?'active':''}`} onClick={()=>navigate(m.id)} aria-current={tab===m.id?'page':undefined}><Icon name={m.icon} size={19}/><span>{m.label}</span>{tab===m.id&&<i/>}</button>)}</nav>
   <div className="sidebar-bottom"><div className="sidebar-note"><div className="sidebar-note-head"><Icon name="shield" size={18}/> Nghiên cứu có căn cứ</div><p>Dữ liệu khoa học, giới hạn pháp lý và suy luận toán học được tách riêng.</p></div><button className="sidebar-logout" onClick={()=>void logout()}><Icon name="logout" size={18}/> Đăng xuất</button><div className="sidebar-version">V2.3 FRONTEND · SCIENCE FIRST</div></div>
  </aside>
  {mobileNav&&<button className="mobile-shade" aria-label="Đóng menu" onClick={()=>setMobileNav(false)}/>}
  <div className="app-main"><header className="topbar"><div className="top-left"><button className="hamburger" aria-label="Mở menu" onClick={()=>setMobileNav(true)}><Icon name="menu" size={22}/></button><span className="breadcrumb">COSMETIC R&D</span><Icon name="chevron" size={14}/><strong>{menu.find(x=>x.id===tab)?.label}</strong></div><div className="top-actions"><div className={`connection-status ${libraryOnline&&catalogOnline?'connected':'partial'}`}><span className="status-dot"/>{libraryOnline&&catalogOnline?'Dữ liệu đã kết nối':'Chưa đủ kết nối'}</div><button className="top-refresh" onClick={()=>void reload()} aria-label="Tải lại dữ liệu" title="Tải lại dữ liệu" disabled={busy}><Icon name="refresh" size={18}/></button><span className="account-avatar" title="Không gian R&D nội bộ">RD</span></div></header>
   <main className="page-content"><div className="page-intro"><div><div className="eyebrow">{h.eyebrow}</div><h1>{h.title}</h1><p>{h.description}</p></div><div className="page-intro-actions"><span className="version-badge"><span/> FRONTEND V2.3</span>{tab!=='analyze'&&<button className="btn primary" onClick={()=>navigate('analyze')}><Icon name="add" size={16}/> Phân tích mới</button>}</div></div>
    {message&&<div className={`global-message ${message.tone}`}><Icon name={message.tone==='success'?'check':'alert'} size={18}/><span>{message.text}</span><button aria-label="Đóng thông báo" onClick={()=>setMessage(null)}><Icon name="close" size={16}/></button></div>}
    {tab==='overview'&&<><div className="stats-grid"><div className="stat-card"><div className="stat-head"><span>Sản phẩm đã lưu</span><span className="stat-symbol"><Icon name="layers" size={19}/></span></div><div className="stat-value">{products.length}</div><div className="stat-caption">Hồ sơ trong thư viện R&D</div></div><div className="stat-card"><div className="stat-head"><span>Nguồn tuyển chọn</span><span className="stat-symbol"><Icon name="book" size={19}/></span></div><div className="stat-value">{studies.length}</div><div className="stat-caption">Công bố khoa học đã lưu</div></div><div className="stat-card"><div className="stat-head"><span>Tài liệu nội bộ</span><span className="stat-symbol"><Icon name="shield" size={19}/></span></div><div className="stat-value">{research.length}</div><div className="stat-caption">{reviewed} đã được kiểm duyệt</div></div><div className="stat-card"><div className="stat-head"><span>Thị trường</span><span className="stat-symbol"><Icon name="globe" size={19}/></span></div><div className="stat-value">06</div><div className="stat-caption">Quy tắc ghi nhãn đã hỗ trợ</div></div></div>
    <div className="overview-grid"><Panel className="welcome-panel"><div className="welcome-copy"><span className="eyebrow">QUY TRÌNH NGHIÊN CỨU</span><h2>Từ nhãn INCI đến hồ sơ R&D có thể kiểm chứng.</h2><p>Đọc thành phần, nhập các nồng độ đã công bố, xem miền % khả thi và mở ngay nguồn nghiên cứu. Mọi kết luận đều giữ được bối cảnh dữ liệu đầu vào.</p><button className="btn primary" onClick={()=>navigate('analyze')}>Bắt đầu phân tích <Icon name="arrow" size={17}/></button></div><div className="welcome-illustration" aria-hidden="true"><div className="orbital orbital-one"/><div className="orbital orbital-two"/><div className="hero-flask"><Icon name="flask" size={74}/></div><span className="floating-tag tag-one">INCI</span><span className="floating-tag tag-two">Min / Max</span><span className="floating-tag tag-three">Evidence</span></div></Panel><Panel><PanelHeader label="CÁCH HỆ THỐNG HOẠT ĐỘNG" title="4 bước nghiên cứu"/><div className="step-list">{[['01','Nhập danh sách INCI','Giữ nguyên thứ tự thành phần theo thị trường.'],['02','Bổ sung dữ liệu đã biết','Tỷ lệ hoạt chất có nguồn, đơn vị %, ppm, mg/g.'],['03','Đọc kết quả suy luận','Khoảng khả thi cùng bằng chứng và giới hạn.'],['04','Lưu & phát triển công thức','Lưu hồ sơ và thử nghiệm giả thuyết.']].map(([n,a,b])=><div className="step-item" key={n}><span>{n}</span><div><b>{a}</b><p>{b}</p></div></div>)}</div></Panel></div>
    <div className="two-column overview-bottom"><Panel><PanelHeader label="HỒ SƠ GẦN ĐÂY" title="Sản phẩm nghiên cứu" aside={<button className="text-action" onClick={()=>navigate('products')}>Xem tất cả <Icon name="arrow" size={15}/></button>}/>{products.length?<div className="recent-list">{products.slice(0,4).map(p=><button onClick={()=>openProduct(p.id)} className="recent-item" key={p.id}><div className="recent-symbol"><Icon name="beaker" size={20}/></div><span><b>{p.name}</b><small>{p.brand||'Chưa có thương hiệu'} · {date(p.created_at)}</small></span><Pill tone="blue">{p.market}</Pill><Icon name="chevron" size={16}/></button>)}</div>:<Empty title="Chưa có sản phẩm đã lưu" description="Khi bạn hoàn thành phân tích đầu tiên, hồ sơ sẽ xuất hiện ở đây."/>}</Panel><Panel><PanelHeader label="CHUẨN HÓA NGHIÊN CỨU" title="Phân loại mức độ bằng chứng"/><div className="knowledge-list"><div><span className="knowledge-dot green"/><div><b>Miền khả thi toán học</b><p>Do bộ giải LP suy ra từ thứ tự, mốc công bố và ràng buộc.</p></div></div><div><span className="knowledge-dot blue"/><div><b>Bằng chứng khoa học</b><p>Kết quả nghiên cứu theo nồng độ, nền công thức và đối tượng thử.</p></div></div><div><span className="knowledge-dot orange"/><div><b>Giới hạn pháp lý</b><p>Áp dụng có điều kiện theo quốc gia và chức năng nguyên liệu.</p></div></div><div><span className="knowledge-dot gray"/><div><b>Ước lượng xác suất</b><p>Chưa triển khai do thiếu dữ liệu hiệu chuẩn đáng tin cậy.</p></div></div></div></Panel></div>
    </>}
    {tab==='analyze'&&<AnalysisView products={products} onSaved={async p=>{setSelected(p.id);await reload()}} onNotice={notify}/>}
    {tab==='products'&&<ProductsView products={products} onNew={()=>navigate('analyze')} onSelect={openProduct}/>}
    {tab==='research'&&<ResearchView studies={studies} research={research} onReload={reload} notify={notify}/>}
    {tab==='regulatory'&&<RegulationView laws={laws}/>}
    {tab==='formulas'&&<FormulaView products={products} chosen={selected} onChosen={setSelected} notify={notify}/>}
   </main><footer className="page-footer"><span>© Cosmetic R&D Intelligence · Nền tảng nghiên cứu mỹ phẩm</span><span>Không thay thế thử nghiệm phòng lab hoặc rà soát pháp lý chuyên gia</span></footer></div>
 </div>;
}
