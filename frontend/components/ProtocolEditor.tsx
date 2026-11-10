'use client';
import {useEffect,useState} from 'react';
import {newMetric,protocolErrors, type Protocol, type MetricSpec} from '../lib/form-model';
function DayListEditor({days,disabled,onCommit}:{days:number[];disabled:boolean;onCommit:(v:number[])=>void}) {
  const [draft,setDraft]=useState(days.join(', '));
  const [invalid,setInvalid]=useState(false);
  useEffect(()=>setDraft(days.join(', ')),[days.join(',')]);
  function commit(){
    const parts=draft.split(',').map(s=>s.trim());
    if(!parts.length || parts.some(s=>!/^\d+$/.test(s))){setInvalid(true);onCommit([]);return;}
    const values=parts.map(Number);
    if(values.some(n=>n>3650)||new Set(values).size!==values.length){setInvalid(true);onCommit([]);return;}
    setInvalid(false);onCommit(values);
  }
  return <><input disabled={disabled} aria-invalid={invalid} value={draft} onChange={e=>{setDraft(e.target.value);setInvalid(false);}} onBlur={commit} placeholder="0, 7, 28" />{invalid&&<small className="lab-field-error">Nhập ngày nguyên không trùng, cách nhau bằng dấu phẩy.</small>}</>;
}

export default function ProtocolEditor({value,onChange,locked}:{value:Protocol;onChange:(v:Protocol)=>void;locked:boolean}){
  const problems=protocolErrors(value);
  const patch=(i:number, fields:Partial<MetricSpec>) => onChange({...value,metrics:value.metrics.map((m,j)=>i===j?{...m,...fields}:m)});
  return <div className="lab-editor">
    <p className="lab-muted">Thiết lập chỉ tiêu, thời điểm, phương pháp và quy cách **do R&D định nghĩa**. Không mặc định là yêu cầu pháp lý hay ISO.</p>
    <div className="lab-metrics">
      {value.metrics.map((m,i)=><div className="lab-metric-editor" key={i}>
        <div className="lab-line"><strong>Chỉ tiêu {i+1}</strong><button type="button" className="secondary lab-mini" disabled={locked||value.metrics.length===1} onClick={()=>onChange({...value,metrics:value.metrics.filter((_,j)=>j!==i)})}>Xóa</button></div>
        <div className="lab-formgrid">
          <label>Mã chỉ tiêu<input disabled={locked} value={m.code} onChange={e=>patch(i,{code:e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g,'')})}/></label>
          <label>Tên chỉ tiêu<input disabled={locked} value={m.name} onChange={e=>patch(i,{name:e.target.value})}/></label>
          <label>Loại đo<select disabled={locked} value={m.kind} onChange={e=>patch(i,{kind:e.target.value as 'numeric'|'categorical'})}><option value="numeric">Số định lượng</option><option value="categorical">Đánh giá phân loại</option></select></label>
          {m.kind==='numeric'?<>
            <label>Đơn vị<input disabled={locked} value={m.unit} onChange={e=>patch(i,{unit:e.target.value})} placeholder="Ví dụ: pH, N, °C"/></label>
            <label>Giới hạn dưới<input type="number" step="any" disabled={locked} value={m.target_min??''} onChange={e=>patch(i,{target_min:e.target.value===''?null:Number(e.target.value)})}/></label>
            <label>Giới hạn trên<input type="number" step="any" disabled={locked} value={m.target_max??''} onChange={e=>patch(i,{target_max:e.target.value===''?null:Number(e.target.value)})}/></label>
          </>:<label className="lab-span-two">Giá trị chấp nhận (ngăn cách dấu ;)<input disabled={locked} value={(m.acceptable_values||[]).join('; ')} onChange={e=>patch(i,{acceptable_values:e.target.value.split(';').map(s=>s.trim()).filter(Boolean)})}/></label>}
          <label>Ngày đo (ngăn cách dấu ,)<DayListEditor days={m.timepoints_days||[]} disabled={locked} onCommit={days=>patch(i,{timepoints_days:days})}/></label>
          <label>Phương pháp đo<input disabled={locked} value={m.method||''} onChange={e=>patch(i,{method:e.target.value})} placeholder="SOP R&D nội bộ"/></label>
          <label>Điều kiện đo<input disabled={locked} value={m.condition||''} onChange={e=>patch(i,{condition:e.target.value})} placeholder="Ví dụ 25°C"/></label>
          <label className="lab-span-two">Nguồn quy cách<input disabled={locked} value={m.criteria_source||''} onChange={e=>patch(i,{criteria_source:e.target.value})} placeholder="USER_DEFINED / tài liệu có mã"/></label>
        </div>
      </div>)}
    </div>
    {!locked&&<button type="button" className="secondary" disabled={value.metrics.length>=24} onClick={()=>onChange({...value,metrics:[...value.metrics,newMetric(value.metrics.length+1)]})}>+ Thêm chỉ tiêu</button>}
    {!!problems.length&&<div className="lab-issues"><strong>Cần sửa ({problems.length}):</strong><ul>{problems.slice(0,8).map((msg,i)=><li key={i}>{msg}</li>)}</ul></div>}
  </div>;
}
