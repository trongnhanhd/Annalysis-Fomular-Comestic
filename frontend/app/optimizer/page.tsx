"use client";

import { useMemo, useState } from "react";
import lip from "./data/lip_balm_optimizer_v44.json";
import pad from "./data/pad_claim_ambiguity_v44.json";
import "./optimizer.css";

type RawItem = {
  item_id: string; inci?: string; grade_id?: string; group_code: string;
  percent_bounds: { min: number; max: number }; prior_percent?: number;
  composition?: { status: string; complete: boolean; components: { inci: string; fraction_min: number; fraction_max: number }[] };
};
type Scenario = {
  title?: string; product_id?: number; template_mode: string; product_type: string;
  physical_form: string; items: RawItem[];
  claims?: { basis: string; inci?: string; item_id?: string; percent: number }[];
  ambiguous_claims?: { percent: number; interpretations: { basis: string; inci?: string; item_id?: string }[] }[];
  include_scientific_screening?: boolean;
};
type Issue = { code: string; severity: string; message_vi: string; details?: Record<string, unknown> };
type Group = { group_code: string; percent_example: number; feasible_interval_percent: number[]; raw_material_count: number };
type Item = { item_id: string; group_code: string; display_inci?: string; percent_example: number; feasible_interval_percent: number[]; complete_composition: boolean };
type SolverResult = {
  status: string; raw_material_total_percent?: number; unresolved_composition_percent_example?: number;
  fully_resolved_inci?: boolean; groups?: Group[]; items?: Item[]; issues?: Issue[];
  label_order_screening?: { status: string }; scientific_screening?: { issues: Issue[] };
  representative_method?: { evidence_status: string }; diagnostic_single_constraint_removals?: string[];
};
type Comparison = { scenarios: { scenario_id: string; interpretation_summary: { basis: string; percent: number }[]; result: SolverResult }[] };
const API = "/backend";
const fmt=(x:number|undefined)=>typeof x === "number" ? x.toLocaleString("vi-VN",{minimumFractionDigits:2,maximumFractionDigits:3}) : "—";
const groupLabels: Record<string,string> = {
  b_lip:"Nền lipid thương mại", lip:"Dầu và bơ", cons:"Sáp / tạo cấu trúc", antiox:"Chống oxy hóa", flavour:"Hương liệu", active:"Hoạt chất", solvent:"Dung môi", acid:"AHA/BHA", carrier:"Pha nước", pH_adjuster:"Điều chỉnh pH"
};
const displayGroup=(k:string)=>groupLabels[k] || k.replaceAll("_"," ");
const clone = (x:Scenario) => JSON.parse(JSON.stringify(x)) as Scenario;

export default function OptimizerPage(){
  const [preset,setPreset]=useState<"lip"|"pad">("lip");
  const [scenario,setScenario]=useState<Scenario>(clone(lip as Scenario));
  const [runResult,setRunResult]=useState<SolverResult|Comparison|null>(null);
  const [selectedResult,setSelectedResult]=useState(0);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");
  const [advanced,setAdvanced]=useState(false);
  const [jsonDraft,setJsonDraft]=useState("");
  const isCompare=Boolean(scenario.ambiguous_claims?.length);
  const results = runResult && "scenarios" in runResult ? runResult.scenarios : [];
  const output: SolverResult | null = runResult ? ("scenarios" in runResult ? results[selectedResult]?.result || null : runResult) : null;
  const issues=output?.issues || [];
  const report=useMemo(()=>{
    if(!output?.groups)return [];
    return [...output.groups].sort((a,b)=>b.percent_example-a.percent_example);
  },[output]);
  const switchPreset=(v:"lip"|"pad")=>{
    setPreset(v);setScenario(clone((v==="lip" ? lip : pad) as Scenario));
    setError("");setRunResult(null);setSelectedResult(0);setAdvanced(false);setJsonDraft("");
  };
  const modify=(idx:number,key:"min"|"max"|"prior_percent",value:string)=>{
    setScenario(prev=>{
      const next=clone(prev);const n=Number(value);
      if(key==="prior_percent")next.items[idx].prior_percent=n;
      else next.items[idx].percent_bounds[key]=n;
      return next;
    });
  };
  const run=async()=>{
    setLoading(true);setError("");setRunResult(null);setSelectedResult(0);
    try{
      const endpoint=isCompare?"compare-claims":"optimize";
      const response=await fetch(`${API}/api/v4.4/${endpoint}`,{
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(scenario)
      });
      const body=await response.json();
      if(!response.ok) throw new Error(typeof body?.detail==="string"?body.detail:"Yêu cầu không hợp lệ, hãy kiểm tra thông số.");
      setRunResult(body);
    }catch(e){setError(e instanceof Error?e.message:"Không kết nối được backend FastAPI.");}
    finally{setLoading(false);}
  };
  const exportReport=()=>{
    if(!runResult)return;
    const blob=new Blob([JSON.stringify({input:scenario,result:runResult},null,2)],{type:"application/json"});
    const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="formula-intelligence-v44-result.json";a.click();URL.revokeObjectURL(url);
  };
  const activeClaim=scenario.ambiguous_claims?.[0];
  return <main className="opt-app">
    <div className="opt-container">
      <header className="opt-header">
        <div className="opt-brand"><span className="opt-mark">F</span><div><strong>Formula Intelligence</strong><small>CONCENTRATION OPTIMIZER · V4.4</small></div></div>
        <nav><a href="/">Phân tích tương thích</a><span className="opt-current">Tối ưu tỷ lệ %</span></nav>
      </header>
      <section className="opt-intro">
        <div><div className="opt-kicker">CÔNG CỤ R&D · MÔ PHỎNG CÓ KIỂM SOÁT</div><h1>Tối ưu cấu trúc công thức</h1>
          <p>Phân nhóm nguyên liệu, giải các ràng buộc cân bằng 100% và xác định khoảng % khả thi — tách bạch dữ liệu công bố, grade thương mại và giả định mô phỏng.</p></div>
        <div className="opt-pill">Không phải phê duyệt sản xuất</div>
      </section>
      <section className="opt-main">
        <div className="opt-column">
          <article className="opt-panel">
            <div className="opt-panel-title"><div><span className="opt-step">01</span><h2>Cấu hình mô phỏng</h2></div><span className="opt-panel-badge">Mẫu tham chiếu</span></div>
            <div className="opt-presets">
              <button type="button" className={preset==="lip"?"selected":""} onClick={()=>switchPreset("lip")}>Son dưỡng môi · Lip Balm</button>
              <button type="button" className={preset==="pad"?"selected":""} onClick={()=>switchPreset("pad")}>Serum Mandelic Acid / PAD</button>
            </div>
            <div className="opt-settings">
              <label>Mức áp dụng khoảng nhóm
                <select value={scenario.template_mode} onChange={e=>setScenario(s=>({...s,template_mode:e.target.value}))}>
                  <option value="advisory">Tham khảo · chỉ cảnh báo</option><option value="strict">Bắt buộc · dùng để giải</option>
                </select>
              </label>
              <label className="opt-switch"><input type="checkbox" checked={Boolean(scenario.include_scientific_screening)} onChange={e=>setScenario(s=>({...s,include_scientific_screening:e.target.checked}))}/> Kèm sàng lọc tính chất V4.3</label>
            </div>
            {activeClaim && <div className="opt-claim"><div><b>Claim đang phân tích</b><small>Hai cách hiểu sẽ được giải riêng, không tự chọn phương án đúng</small></div>
              <label>PAD công bố (%) <input type="number" min="0" max="100" step="0.1" value={activeClaim.percent} onChange={e=>setScenario(s=>({...s,ambiguous_claims:[{...s.ambiguous_claims![0],percent:Number(e.target.value)}]}))}/></label>
            </div>}
          </article>
          <article className="opt-panel">
            <div className="opt-panel-title"><div><span className="opt-step">02</span><h2>Danh sách nguyên liệu</h2></div><span className="opt-panel-badge">{scenario.items.length} nguyên liệu</span></div>
            <p className="opt-help">Chỉnh khoảng % cân nguyên liệu và giá trị mục tiêu. Nghiệm mẫu sử dụng giá trị mục tiêu làm tham chiếu mềm; các ràng buộc cứng vẫn được ưu tiên.</p>
            <div className="opt-tablewrap"><table className="opt-input-table"><thead><tr><th>Nguyên liệu / nhóm</th><th>Min %</th><th>Max %</th><th>Mục tiêu %</th></tr></thead><tbody>
              {scenario.items.map((r,i)=><tr key={r.item_id}><td><b title={r.inci}>{r.inci||r.item_id}</b><small>{displayGroup(r.group_code)}{r.grade_id?` · ${r.grade_id}`:""}</small></td>
                <td><input type="number" min="0" max="100" step="0.01" aria-label={`Min ${r.item_id}`} value={r.percent_bounds.min} onChange={e=>modify(i,"min",e.target.value)}/></td>
                <td><input type="number" min="0" max="100" step="0.01" aria-label={`Max ${r.item_id}`} value={r.percent_bounds.max} onChange={e=>modify(i,"max",e.target.value)}/></td>
                <td><input type="number" min="0" max="100" step="0.01" aria-label={`Mục tiêu ${r.item_id}`} value={r.prior_percent??0} onChange={e=>modify(i,"prior_percent",e.target.value)}/></td></tr>)}
            </tbody></table></div>
            <button className="opt-advanced-link" onClick={()=>{setAdvanced(!advanced);setJsonDraft(JSON.stringify(scenario,null,2));}}>{advanced?"Ẩn cấu hình JSON":"Chỉnh cấu trúc grade / INCI nâng cao"}</button>
            {advanced&&<div className="opt-json"><label>Cấu hình JSON bao gồm tỷ phần premix, claim và thứ tự INCI</label>
              <textarea spellCheck={false} value={jsonDraft} onChange={e=>setJsonDraft(e.target.value)} rows={13}/>
              <button type="button" onClick={()=>{try{const val=JSON.parse(jsonDraft);if(!Array.isArray(val.items))throw Error("Thiếu items");setScenario(val);setError("");}catch(e){setError(e instanceof Error?e.message:"JSON không hợp lệ");}}}>Áp dụng JSON đã chỉnh</button>
            </div>}
            <div className="opt-actions"><button className="opt-run" onClick={run} disabled={loading}>{loading?"Đang giải bài toán...":isCompare?"So sánh 2 cách hiểu claim":"Tính khoảng % khả thi"}</button>
              <span>Không ghi đè dữ liệu gốc • Chỉ phân tích mô phỏng</span></div>
            {error&&<div role="alert" className="opt-error">{error}</div>}
          </article>
        </div>
        <aside className="opt-column">
          <article className="opt-panel opt-results">
            <div className="opt-panel-title"><div><span className="opt-step">03</span><h2>Kết quả phân tích</h2></div><span className="opt-panel-badge">Bộ giải tuyến tính</span></div>
            {!output&&<div className="opt-empty"><div className="opt-empty-icon">∑</div><h3>Chưa chạy mô phỏng</h3><p>Chọn mẫu, cập nhật khoảng % và bắt đầu giải để xem phân bổ nhóm cùng các cảnh báo.</p></div>}
            {output&&<>
              {results.length>0&&<div className="opt-result-tabs">{results.map((r,i)=><button key={r.scenario_id} className={selectedResult===i?"selected":""} onClick={()=>setSelectedResult(i)}>{r.interpretation_summary.slice(-1)[0]?.basis==="finished_inci"?"8% INCI thực":"8% nguyên liệu"}</button>)}</div>}
              <div className="opt-status"><span className={output.status==="FEASIBLE"?"opt-status-ok":"opt-status-err"}>{output.status==="FEASIBLE"?"Có nghiệm khả thi":output.status==="INFEASIBLE"?"Không có nghiệm":"Thiếu thông tin để giải"}</span>
                <span>Trạng thái: mô phỏng, chưa kiểm định</span></div>
              {output.status==="FEASIBLE"&&<>
                <div className="opt-kpis"><div><span>Tổng cân nguyên liệu</span><strong>{fmt(output.raw_material_total_percent)}%</strong></div><div><span>Thành phần premix chưa rõ</span><strong>{fmt(output.unresolved_composition_percent_example)}%</strong></div></div>
                <h3>Phân bố theo nhóm</h3>
                <p className="opt-subtitle">Thanh biểu diễn nghiệm minh họa. Khoảng min–max là các biên khả thi tính trên toàn hệ ràng buộc.</p>
                <div className="opt-group-list">{report.map(g=><div className="opt-group" key={g.group_code}><div><b>{displayGroup(g.group_code)}</b><b>{fmt(g.percent_example)}%</b></div><div className="opt-bar"><div style={{width:`${Math.max(0,Math.min(100,g.percent_example))}%`}}/></div><small>Khoảng khả thi {fmt(g.feasible_interval_percent[0])}% – {fmt(g.feasible_interval_percent[1])}% · {g.raw_material_count} nguyên liệu</small></div>)}</div>
                <h3>Ước lượng từng nguyên liệu</h3>
                <div className="opt-tablewrap"><table className="opt-output-table"><thead><tr><th>Nguyên liệu</th><th>Ví dụ</th><th>Khoảng khả thi</th></tr></thead><tbody>{output.items?.map(i=><tr key={i.item_id}><td>{i.display_inci||i.item_id}{!i.complete_composition&&<small>Premix chưa rõ tỷ phần</small>}</td><td><b>{fmt(i.percent_example)}%</b></td><td>{fmt(i.feasible_interval_percent[0])} – {fmt(i.feasible_interval_percent[1])}%</td></tr>)}</tbody></table></div>
              </>}
              {output.diagnostic_single_constraint_removals?.length ? <div className="opt-diagnostics"><b>Các ràng buộc cần kiểm tra</b><p>{output.diagnostic_single_constraint_removals.join(", ")}</p><small>Đây là gợi ý nới lỏng từng ràng buộc, không phải chứng minh mâu thuẫn tối thiểu.</small></div>:null}
              <h3>Cảnh báo và chứng cứ</h3>
              <div className="opt-findings">{issues.length===0?<p>Chưa có cảnh báo riêng; không đồng nghĩa an toàn hoặc hợp pháp.</p>:issues.slice(0,14).map((it,i)=><div className={`opt-finding ${it.severity}`} key={i}><b>{it.code}</b><p>{it.message_vi}</p></div>)}</div>
              {output.scientific_screening && <div className="opt-diagnostics"><b>Sàng lọc tính chất V4.3</b><p>{output.scientific_screening.issues.length} ghi nhận, chỉ phục vụ rà soát R&D.</p></div>}
              <button className="opt-export" onClick={exportReport}>Xuất JSON có dấu vết tính toán</button>
            </>}
          </article>
          <div className="opt-warning"><strong>Nguyên tắc tính toán</strong><p>Không cộng hai lần tỷ trọng nền và thành phần premix. Claim không rõ cơ sở tính sẽ được phân tích theo từng giả thuyết. Mọi kết quả đều cần hồ sơ grade, thử nghiệm và rà soát pháp lý độc lập.</p></div>
        </aside>
      </section>
      <footer className="opt-footer">Formula Intelligence V4.4 · Giao diện nghiên cứu và kiểm tra mô hình · Không phải hồ sơ công bố, đánh giá an toàn hoặc chứng nhận lưu hành mỹ phẩm.</footer>
    </div>
  </main>;
}
