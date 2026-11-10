'use client';

import {useEffect,useMemo,useState} from 'react';

type Candidate = {
  candidate_id: string;
  candidate_sha256: string;
  composition_percent: Record<string,number>;
  design: Record<string,unknown>;
};
type CreatedBatch = {batch_id:string;study_id:string;lot_code:string;traceability_status:string};

type Props={
  studyId:string;
  defaultOperator:string;
  onCreated:(value:CreatedBatch)=>Promise<void>;
  onError:(message:string)=>void;
};

/** All weighing fields start blank: never convert simulation targets into claimed actual measurements. */
export default function BatchTraceabilityEditor({studyId,defaultOperator,onCreated,onError}:Props){
  const [candidates,setCandidates]=useState<Candidate[]>([]);
  const [selected,setSelected]=useState('');
  const [lotCode,setLotCode]=useState('');
  const [operator,setOperator]=useState(defaultOperator);
  const [procedure,setProcedure]=useState('');
  const [weights,setWeights]=useState<Record<string,string>>({});
  const [lots,setLots]=useState<Record<string,string>>({});
  const [saving,setSaving]=useState(false);
  const [loading,setLoading]=useState(true);
  useEffect(()=>{
    let open=true;
    setLoading(true);setCandidates([]);setSelected('');setWeights({});setLots({});
    fetch(`/backend/api/v4.5/studies/${encodeURIComponent(studyId)}/candidates`)
      .then(async res=>{const data=await res.json();if(!res.ok) throw new Error(data.detail||'Không tải được phương án');return data;})
      .then(data=>{if(open){setCandidates(Array.isArray(data)?data:[]);setSelected(data?.[0]?.candidate_id||'');}})
      .catch(e=>{if(open)onError(String(e?.message||e));})
      .finally(()=>{if(open)setLoading(false);});
    return ()=>{open=false;};
  },[studyId]);
  const candidate=useMemo(()=>candidates.find(c=>c.candidate_id===selected),[candidates,selected]);
  const items=Object.entries(candidate?.composition_percent||{});
  const total=items.reduce((sum,[id])=>sum+(weights[id]?.trim()?Number(weights[id]):0),0);
  async function submit(){
    if(!candidate || !lotCode.trim() || !operator.trim() || !procedure.trim()){
      onError('Cần chọn phương án, mã mẻ, người thao tác và mã quy trình');return;
    }
    const actual_weights_g:Record<string,number>={};
    const raw_material_lots:Record<string,string>={};
    for(const [id] of items){
      const w=weights[id]?.trim(), lot=lots[id]?.trim();
      if(!w || !lot || !Number.isFinite(Number(w)) || Number(w)<0){
        onError(`Cần khối lượng cân thực và mã lô hợp lệ cho ${id}`);return;
      }
      actual_weights_g[id]=Number(w);
      raw_material_lots[id]=lot;
    }
    if(total<=0){onError('Tổng khối lượng thực phải lớn hơn 0');return;}
    setSaving(true);
    try{
      const response=await fetch(`/backend/api/v4.5/studies/${encodeURIComponent(studyId)}/batches`,{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({lot_code:lotCode.trim(),operator:operator.trim(),candidate_id:selected,
          actual_weights_g,raw_material_lots,weighed_by:operator.trim(),process:{procedure_ref:procedure.trim()}})
      });
      const result=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(result.detail||`HTTP ${response.status}`);
      await onCreated(result as CreatedBatch);
      setLotCode('');setWeights({});setLots({});
    }catch(e:any){onError(String(e?.message||e));}finally{setSaving(false);}
  }
  return <section className="lab-editor" aria-label="Truy vết mẻ thử">
    <p className="lab-muted">Chọn phương án DoE đã khóa, nhập <strong>khối lượng thực cân</strong> và mã lô cho từng nguyên liệu. Số % bên cạnh là mục tiêu mô phỏng, không phải số đo.</p>
    {loading?<p className="lab-muted">Đang tải các phương án đã khóa…</p>:candidates.length===0?<p className="lab-warning">Nghiên cứu cũ chưa có phương án được khóa. Không tạo mẻ mới từ công thức chưa truy vết.</p>:<>
      <div className="lab-formgrid">
        <label>Phương án DoE / Baseline
          <select value={selected} onChange={e=>{setSelected(e.target.value);setWeights({});setLots({});}}>
            {candidates.map(c=><option key={c.candidate_id} value={c.candidate_id}>{c.candidate_id}</option>)}
          </select>
        </label>
        <label>Mã mẻ thử<input value={lotCode} onChange={e=>setLotCode(e.target.value)} placeholder="LAB-001"/></label>
        <label>Người thực cân<input value={operator} onChange={e=>setOperator(e.target.value)}/></label>
        <label>Mã SOP / quy trình<input value={procedure} onChange={e=>setProcedure(e.target.value)} placeholder="LAB-SOP-001"/></label>
      </div>
      <div className="lab-ingredient-scroll"><table className="lab-edit-table">
        <thead><tr><th>Nguyên liệu / mã</th><th>Mục tiêu (%)</th><th>Cân thực (g)</th><th>Lô nguyên liệu</th></tr></thead>
        <tbody>{items.map(([id,p])=><tr key={id}>
          <td>{id}</td><td>{Number(p).toLocaleString('vi-VN',{maximumFractionDigits:4})}</td>
          <td><input aria-label={`Khối lượng thực ${id}`} type="number" min="0" step="any" value={weights[id]||''} placeholder="Nhập sau khi cân" onChange={e=>setWeights(v=>({...v,[id]:e.target.value}))}/></td>
          <td><input aria-label={`Mã lô ${id}`} value={lots[id]||''} placeholder="LOT-..." onChange={e=>setLots(v=>({...v,[id]:e.target.value}))}/></td>
        </tr>)}</tbody>
      </table></div>
      <p className="lab-muted">Tổng lượng đã nhập: {Number.isFinite(total)?total.toLocaleString('vi-VN',{maximumFractionDigits:4}):'Không hợp lệ'} g • SHA256 phương án: {candidate?.candidate_sha256.slice(0,18)}…</p>
      <button type="button" disabled={saving||loading} onClick={submit}>{saving?'Đang lưu…':'Lưu mẻ và bảng cân có truy vết'}</button>
    </>}
  </section>;
}
