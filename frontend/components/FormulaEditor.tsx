'use client';
import { useState } from 'react';
import { balanceFormula, formulaErrors, formulaTotal, newIngredient, type FormulaScenario, type FormulaItem } from '../lib/form-model';

const groups = [
  ['b_lip','Nền lipid'],['lip','Dầu và bơ'],['cons','Tạo cấu trúc'],['antiox','Chống oxy hóa'],
  ['flavour','Hương liệu'],['active','Hoạt chất'],['solvent','Dung môi'],['carrier','Chất mang'],
  ['acid','Acid'],['pH_adjuster','Điều chỉnh pH'],['preservative','Bảo quản'],['humectant','Giữ ẩm'],
  ['thickener','Tạo đặc']
];
export default function FormulaEditor({ value, onChange, locked, onError }: {value: FormulaScenario; onChange: (x: FormulaScenario) => void; locked: boolean; onError: (message: string) => void}) {
  const [balanceId,setBalanceId]=useState('');
  const issues = formulaErrors(value);
  const total = formulaTotal(value);
  function patch(index: number, next: Partial<FormulaItem>) {
    const items = value.items.map((it,i) => i===index ? {...it,...next} : it);
    onChange({...value,items});
  }
  function patchBounds(index:number, key:'min'|'max', n:number) {
    patch(index, {percent_bounds:{...value.items[index].percent_bounds,[key]:n}});
  }
  function remove(index:number) { onChange({...value,items:value.items.filter((_,i)=>i!==index)}); }
  function add() {
    const existing=new Set(value.items.map(it=>it.item_id)); let i=value.items.length+1;
    while(existing.has(`material_${i}`))i++;
    onChange({...value,items:[...value.items,newIngredient(i)]});
  }
  return <div className="lab-editor">
    <div className="lab-formgrid lab-formgrid-two">
      <label>Tên công thức / kịch bản<input disabled={locked} value={value.title || ''} onChange={e=>onChange({...value,title:e.target.value})}/></label>
      <label>Loại sản phẩm<input disabled={locked} value={value.product_type || ''} onChange={e=>onChange({...value,product_type:e.target.value})} placeholder="Ví dụ: lip_balm" /></label>
      <label>Dạng bào chế<select disabled={locked} value={value.physical_form || ''} onChange={e=>onChange({...value,physical_form:e.target.value})}>
        <option value="">Chưa xác định</option><option value="anhydrous">Hệ khan</option><option value="aqueous">Hệ nước</option><option value="emulsion">Nhũ tương</option><option value="other">Khác</option>
      </select></label>
      <label>Áp dụng khoảng nhóm<select disabled={locked} value={value.template_mode || 'advisory'} onChange={e=>onChange({...value,template_mode:e.target.value})}><option value="advisory">Tham chiếu (mềm)</option><option value="strict">Bắt buộc (R&D chọn)</option></select></label>
    </div>
    <div className="lab-edit-title"><strong>Nguyên liệu và tỷ lệ mục tiêu</strong><span>Chỉ là giá trị mô phỏng, chưa phải công thức đã kiểm nghiệm</span></div>
    <div className="lab-ingredient-scroll">
      <table className="lab-edit-table"><thead><tr><th style={{minWidth:145}}>Mã</th><th style={{minWidth:190}}>Tên INCI / nguyên liệu</th><th style={{minWidth:140}}>Nhóm</th><th style={{minWidth:82}}>Min %</th><th style={{minWidth:82}}>Max %</th><th style={{minWidth:95}}>Mục tiêu %</th><th style={{minWidth:165}}>Thành phần grade</th><th></th></tr></thead>
      <tbody>{value.items.map((it,index)=><tr key={index}>
        <td><input disabled={locked} aria-label={`Mã nguyên liệu ${index+1}`} value={it.item_id} onChange={e=>patch(index,{item_id:e.target.value})}/></td>
        <td><input disabled={locked} aria-label={`Tên nguyên liệu ${index+1}`} value={it.inci} onChange={e=>patch(index,{inci:e.target.value})}/></td>
        <td><select disabled={locked} aria-label={`Nhóm ${index+1}`} value={it.group_code} onChange={e=>patch(index,{group_code:e.target.value})}>
          {(!groups.some(g=>g[0]===it.group_code))&&<option value={it.group_code}>{it.group_code}</option>}
          {groups.map(([id,name])=><option value={id} key={id}>{name}</option>)}
        </select></td>
        <td><input type="number" min={0} max={100} step="any" disabled={locked} aria-label={`Min ${index+1}`} value={it.percent_bounds?.min ?? ''} onChange={e=>patchBounds(index,'min',e.target.value===''?NaN:Number(e.target.value))}/></td>
        <td><input type="number" min={0} max={100} step="any" disabled={locked} aria-label={`Max ${index+1}`} value={it.percent_bounds?.max ?? ''} onChange={e=>patchBounds(index,'max',e.target.value===''?NaN:Number(e.target.value))}/></td>
        <td><input type="number" min={0} max={100} step="any" disabled={locked} aria-label={`Tỷ lệ ${index+1}`} value={it.prior_percent ?? ''} onChange={e=>patch(index,{prior_percent:e.target.value===''?NaN:Number(e.target.value)})}/></td>
        <td><span className={'lab-status lab-status-'+(it.composition?.complete?'assumed':'unknown')}>{it.composition?.complete?'Đã khai báo thành phần':'Chưa đủ cấu tử'}</span>{it.grade_id&&<small>{it.grade_id}</small>}</td>
        <td><button type="button" className="secondary lab-mini" disabled={locked || value.items.length===1} aria-label={`Xóa ${it.item_id}`} onClick={()=>remove(index)}>×</button></td>
      </tr>)}</tbody></table>
    </div>
    <div className="lab-editor-footer">
      <div><strong className={Math.abs(total-100)<0.00001?'lab-good':'lab-bad'}>Tổng mục tiêu: {total.toLocaleString('vi-VN')}%</strong><p className="lab-muted">Tổng 100% là điều kiện số học; premix chưa rõ không được tự phân rã.</p></div>
      {!locked&&<div className="lab-actions"><button type="button" className="secondary" onClick={add}>+ Thêm nguyên liệu</button>
        <select aria-label="Nguyên liệu cân bằng" value={value.items.some(it=>it.item_id===balanceId)?balanceId:''} onChange={e=>setBalanceId(e.target.value)}><option value="">Chọn nguyên liệu cân bằng</option>{value.items.map(it=><option value={it.item_id} key={it.item_id}>{it.item_id}</option>)}</select>
        <button type="button" className="secondary" onClick={()=>{try{onChange(balanceFormula(value,balanceId));}catch(err){onError(String((err as Error).message));}}}>Cân bằng 100%</button>
      </div>}
    </div>
    {!!value.ambiguous_claims?.length&&<div className="lab-warning">Có claim chưa rõ cách tính. Chọn và xác minh cơ sở claim trước khi lưu mẻ thí nghiệm; hệ thống không tự chọn cách hiểu.</div>}
    {!!issues.length&&<div className="lab-issues"><strong>Cần sửa ({issues.length}):</strong><ul>{issues.slice(0,8).map((m,i)=><li key={i}>{m}</li>)}</ul></div>}
  </div>;
}
