"use client";
import {useEffect,useMemo,useState} from "react";

type Material={inci:string;percent:string;group_code:string;grade_id?:string};
type Finding={code:string;severity:string;message_vi:string;inci:string|null;grade_id?:string|null;source_id:string|null;details:Record<string,unknown>};
type Outcome={engine_version:string;v43_observation_count_used:number;v43_grade_evidence?:{grade_id:string;grade_name:string;source_url:string}[];raw_material_mass_percent:number;v41_group_validation?:{passed_structural_check:boolean;issues:Finding[]}|null;primary_groups_raw_material_percent:Record<string,number>;scientific_compatibility_status:string;regulatory_status:string;stability_status:string;manufacturing_approval:boolean;issues:Finding[]};
type Suggestion={ingredient_id:string;inci:string;status:string;phase:string|null;source_id:string|null};
type Grade={grade_id:string;display_name:string;expected_inci:string;catalog_version?:string};
type Template={product_id:string;product_type:string;family:string};
const API="/backend";
const seed:Material[]=[{inci:"Aqua",percent:"60",group_code:"b_water"},{inci:"Glycerin",percent:"20",group_code:"hum"},{inci:"Panthenol",percent:"5",group_code:"active"},{inci:"Allantoin",percent:"1",group_code:"active"},{inci:"Bisabolol",percent:"1",group_code:"active"},{inci:"Carbomer",percent:"1",group_code:"thick"},{inci:"Propanediol",percent:"12",group_code:"solv"}];
function f(n:number){return n.toLocaleString("vi-VN",{maximumFractionDigits:3})}
export default function Page(){
 const [materials,setMaterials]=useState<Material[]>(seed);
 const [form,setForm]=useState("aqueous");
 const [ph,setPh]=useState("3.2");
 const [water,setWater]=useState("60");
 const [preservation,setPreservation]=useState(false);
 const [processTemp,setProcessTemp]=useState("");
 const [processIntent,setProcessIntent]=useState("unknown");
 const [scientificObs,setScientificObs]=useState<{grade_id:string;property_key:string;value_min:string;value_max:string;unit:string;source_url:string;qualitative_value:string}[]>([]);
 const [solubilized,setSolubilized]=useState(false);
 const [query,setQuery]=useState("");
 const [suggestions,setSuggestions]=useState<Suggestion[]>([]);
 const [grades,setGrades]=useState<Grade[]>([]);
 const [templates,setTemplates]=useState<Template[]>([]);
 const [productId,setProductId]=useState("");
 const [outcome,setOutcome]=useState<Outcome|null>(null);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const total=useMemo(()=>materials.reduce((s,m)=>s+ (Number(m.percent)||0),0),[materials]);
 useEffect(()=>{let cancel=false;const controller=new AbortController();fetch(`${API}/api/v4.3/ingredients?q=${encodeURIComponent(query)}&limit=15`,{signal:controller.signal}).then(r=>r.json()).then(d=>{if(!cancel)setSuggestions(d.results||[])}).catch(()=>{});return ()=>{cancel=true;controller.abort()};},[query]);
 useEffect(()=>{fetch(`${API}/api/v4.3/grades`).then(r=>r.json()).then(d=>setGrades(d.results||[])).catch(()=>{});fetch(`${API}/api/v4.3/templates`).then(r=>r.json()).then(d=>setTemplates(d.templates||[])).catch(()=>{});},[]);
 function update(index:number,key:keyof Material,value:string){setMaterials(prev=>prev.map((m,i)=>i===index?{...m,[key]:value}:m));}
 async function evaluate(){setBusy(true);setError("");setOutcome(null);try{
  const rows=materials.map(m=>({...m,percent:Number(m.percent)}));
  if(rows.some(m=>!Number.isFinite(m.percent)||m.percent<0))throw new Error("Có tỷ lệ không hợp lệ.");
  const r=await fetch(`${API}/api/v4.3/evaluate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({product_type:templates.find(t=>t.product_id===productId)?.product_type||(form==="anhydrous"?"Hệ khan":"Mẫu nghiên cứu"),product_id:productId?Number(productId):null,ui_base_display_percent:100,physical_form:form,pH:ph===""?null:Number(ph),water_phase_percent:water===""?null:Number(water),preservation_evidence:preservation,solubilizer_system_confirmed:solubilized,process_temperature_c:processTemp===""?null:Number(processTemp),process_intent:processIntent,items:rows})});
  if(!r.ok)throw new Error((await r.text()).slice(0,500));setOutcome(await r.json());
 }catch(e){setError(e instanceof Error?e.message:"Lỗi khi kiểm tra.")}finally{setBusy(false)}}
 function addSuggestion(s:Suggestion){setMaterials(p=>[...p,{inci:s.inci,percent:"0",group_code:"active"}]);setQuery("");}
 useEffect(()=>{const grade=materials.find(m=>m.grade_id?.startsWith('S43-G-'))?.grade_id;if(!grade){setScientificObs([]);return;}fetch(`${API}/api/v4.3/observations?grade_id=${encodeURIComponent(grade)}`).then(r=>r.json()).then(d=>setScientificObs(d.results||[])).catch(()=>setScientificObs([]));},[materials]);
 return <main className="wrap">
  <header className="hero"><div><p className="eyebrow">FORMULA INTELLIGENCE / R&D · BẢN DEMO</p><h1>Tri thức nguyên liệu & bằng chứng khoa học</h1><p className="muted">Phân tích có nguồn · Tách grade thương mại · Sàng lọc rủi ro trước thử nghiệm</p></div><span className="tag">V4.3</span></header>
  <section className="tiles"><article><b>190</b><small>INCI ứng viên</small></article><article><b>32</b><small>Nhóm chức năng</small></article><article><b>11</b><small>Grade tham chiếu mới</small></article><article><b>22</b><small>Quan sát kỹ thuật mới</small></article></section>
  <div className="columns"><section className="panel"><div className="sectionhead"><h2>Thông số hệ công thức</h2><span className="hint">Tỷ lệ % w/w</span></div>
   <div className="templatepick"><label>Mẫu nhóm tham chiếu (tùy chọn)<select value={productId} onChange={e=>setProductId(e.target.value)}><option value="">Không áp dụng mẫu nhóm V4.1</option>{templates.map(t=><option value={t.product_id} key={t.product_id}>{t.product_type} — {t.family}</option>)}</select></label></div><div className="formgrid"><label>Dạng hệ<select value={form} onChange={e=>{setForm(e.target.value);if(e.target.value==="anhydrous"){setWater("0");setPh("");}}}><option value="aqueous">Hệ nước</option><option value="emulsion">Nhũ tương</option><option value="anhydrous">Hệ khan</option><option value="unknown">Chưa biết</option></select></label><label>pH dự kiến<input type="number" min="0" max="14" step="0.1" value={ph} onChange={e=>setPh(e.target.value)} /></label><label>Pha nước (%)<input type="number" min="0" max="100" step="0.1" value={water} onChange={e=>setWater(e.target.value)} /></label></div>
   <div className="formgrid"><label>Nhiệt độ gia công (°C)<input type="number" value={processTemp} onChange={e=>setProcessTemp(e.target.value)} min="0" max="200" step="1" placeholder="Không có dữ liệu" /></label><label>Mục đích công đoạn<select value={processIntent} onChange={e=>setProcessIntent(e.target.value)}><option value="unknown">Chưa xác định</option><option value="full_melt">Làm chảy hoàn toàn</option><option value="cold_blend">Phối trộn nguội</option></select></label></div>
   <label className="check"><input type="checkbox" checked={solubilized} onChange={e=>setSolubilized(e.target.checked)}/> Đã có dữ liệu chứng minh hệ hòa tan dầu trong nước</label>
   <label className="check"><input type="checkbox" checked={preservation} onChange={e=>setPreservation(e.target.checked)}/> Đã có hồ sơ đánh giá bảo quản phù hợp</label>
   {scientificObs.length>0&&<div className="refbox"><h3>Dữ liệu kỹ thuật từ grade đang chọn</h3>{scientificObs.map((o,i)=><div key={i} className="refrow"><span>{o.property_key}: {o.qualitative_value||[o.value_min,o.value_max].filter(Boolean).join("–")} {o.unit}</span><a href={o.source_url} target="_blank" rel="noreferrer">Nguồn</a></div>)}<small>Chỉ áp dụng cho grade và điều kiện được nhà cung cấp công bố.</small></div>}
   <h3>Nguyên liệu trong mẻ</h3><div className="materials"><div className="material head"><span>Tên INCI</span><span>Nhóm</span><span>% cân</span><span></span></div>
   {materials.map((m,i)=><div className="material" key={i}><div className="material-name"><input aria-label={`INCI ${i+1}`} value={m.inci} onChange={e=>update(i,"inci",e.target.value)}/>{grades.some(g=>g.expected_inci.toLowerCase().split(";").some(n=>n.trim()===m.inci.toLowerCase())||g.display_name.toLowerCase()===m.inci.toLowerCase())&&<select aria-label={`Grade ${i+1}`} value={m.grade_id||""} onChange={e=>update(i,"grade_id",e.target.value)}><option value="">Không chọn grade</option>{grades.filter(g=>g.expected_inci.toLowerCase().split(";").some(n=>n.trim()===m.inci.toLowerCase())||g.display_name.toLowerCase()===m.inci.toLowerCase()).map(g=><option value={g.grade_id} key={g.grade_id}>{g.display_name}</option>)}</select>}</div><input aria-label={`Nhóm ${i+1}`} value={m.group_code} onChange={e=>update(i,"group_code",e.target.value)}/><input aria-label={`Tỷ lệ ${i+1}`} type="number" min="0" max="100" step="0.01" value={m.percent} onChange={e=>update(i,"percent",e.target.value)}/><button className="delete" aria-label={`Xóa dòng ${i+1}`} onClick={()=>setMaterials(prev=>prev.filter((_,j)=>j!==i))}>×</button></div>)}
   </div><div className="searchbar"><input placeholder="Tìm INCI để thêm..." value={query} onChange={e=>setQuery(e.target.value)}/><button onClick={()=>setMaterials(prev=>[...prev,{inci:"",percent:"0",group_code:"active"}])}>+ Dòng trống</button></div>
   {query&&<div className="suggestions">{suggestions.map(s=><button key={s.ingredient_id} onClick={()=>addSuggestion(s)}>{s.inci} <span>{s.status==="not_assessed"?"Chưa có TDS":"Có tài liệu tham chiếu"}</span></button>)}</div>}
   <div className="total"><span>Tổng nguyên liệu cân</span><strong className={Math.abs(total-100)<0.000001?"good":"warn"}>{f(total)}%</strong></div>
   <button className="primary" disabled={busy} onClick={evaluate}>{busy?"Đang phân tích...":"Kiểm tra công thức V4.3"}</button>
   {error&&<p className="err" role="alert">{error}</p>}
  </section>
  <section className="panel"><div className="sectionhead"><h2>Kết quả sàng lọc</h2><span className="hint">Không phải phê duyệt sản xuất</span></div>
   {!outcome?<div className="empty"><div className="placeholder">✦</div><h3>Chưa chạy phân tích</h3><p>Điều chỉnh thông số hoặc dùng công thức minh họa, sau đó chọn “Phân tích”.</p></div>:<>
    <div className="resultbox"><span>Khối lượng thực</span><b>{f(outcome.raw_material_mass_percent)}%</b><span>Trạng thái kỹ thuật</span><b>{outcome.scientific_compatibility_status==="REVIEW_REQUIRED"?"Cần đánh giá R&D":"Chưa đánh giá đủ"}</b><span>Pháp lý</span><b>Chưa đánh giá</b></div>
    <p className="muted">Nguồn grade sử dụng: {outcome.v43_grade_evidence?.length||0}; quan sát kỹ thuật liên quan: {outcome.v43_observation_count_used||0}.</p><h3>Kiểm tra cấu trúc nhóm</h3><p className="muted">{outcome.v41_group_validation?(outcome.v41_group_validation.passed_structural_check?"Đạt ràng buộc mẫu V4.1 đã chọn (chưa đánh giá pháp lý).":"Mẫu V4.1 có nhóm cần sửa — xem cảnh báo bên dưới."):"Chưa chọn mẫu nhóm tham chiếu."}</p><h3>Tỷ lệ nhóm nguyên liệu</h3>{Object.entries(outcome.primary_groups_raw_material_percent).map(([g,v])=><div className="group" key={g}><div><span>{g}</span><b>{f(v)}%</b></div><div className="track"><div style={{width:`${Math.max(0,Math.min(100,v))}%`}}/></div></div>)}
    <h3>Cảnh báo và dữ liệu còn thiếu ({outcome.issues.length})</h3>{outcome.issues.map((x,i)=><article key={i} className={`finding ${x.severity}`}><b>{x.inci?x.inci+" · ":""}{x.code}</b><p>{x.message_vi}</p>{x.source_id&&<small>Nguồn: {x.source_id}</small>}</article>)}
    <p className="muted caveat">Giới hạn pháp lý, hiệu quả bảo quản, độ bền nhũ và an toàn thành phẩm phải được xác minh riêng.</p>
   </>}
  </section></div><footer>Dữ liệu nguồn V4.1: 190 INCI ứng viên, chưa phải danh mục được phê duyệt. V4.3 bổ sung 11 grade, 22 quan sát kỹ thuật theo nguồn. Chưa xác nhận công thức an toàn, ổn định hoặc hợp pháp.</footer>
 </main>
}
