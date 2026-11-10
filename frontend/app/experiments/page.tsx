'use client';

import { useEffect, useMemo, useState } from 'react';
import './experiments.css';
import lipDemo from './sample_study.json';
import padDemo from './sample_pad.json';
import FormulaEditor from '../../components/FormulaEditor';
import ProtocolEditor from '../../components/ProtocolEditor';
import BatchTraceabilityEditor from '../../components/BatchTraceabilityEditor';
import { formulaErrors, protocolErrors, type FormulaScenario, type Protocol } from '../../lib/form-model';

type AnyObject = Record<string, any>;
const BASE_URL = '/backend';
const lipScenario = lipDemo.scenario as AnyObject;
const demoProtocol = lipDemo.protocol as AnyObject;
const padScenario = padDemo as AnyObject;

async function api(path: string, init?: RequestInit) {
  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) } });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  return body;
}

export default function ExperimentsPage() {
  const [scenarioText, setScenarioText] = useState(JSON.stringify(lipScenario, null, 2));
  const [protocolText, setProtocolText] = useState(JSON.stringify(demoProtocol, null, 2));
  const [studyTitle, setStudyTitle] = useState(lipDemo.title);
  const [researcher, setResearcher] = useState('');
  const [factorA, setFactorA] = useState('beeswax');
  const [factorB, setFactorB] = useState('jojoba_oil');
  const [minA, setMinA] = useState('16'); const [maxA, setMaxA] = useState('20');
  const [minB, setMinB] = useState('30'); const [maxB, setMaxB] = useState('38');
  const [balanceItem, setBalanceItem] = useState('base_premix');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('Biểu mẫu R&D V4.5.2: các tỷ lệ mục tiêu và tiêu chí mẫu chỉ là giả định, số đo phải được ghi nhận thực tế.');
  const [design, setDesign] = useState<AnyObject | null>(null);
  const [designRequest, setDesignRequest] = useState<AnyObject | null>(null);
  const [draftReview, setDraftReview] = useState<AnyObject | null>(null);
  const [study, setStudy] = useState<AnyObject | null>(null);
  const [batch, setBatch] = useState<AnyObject | null>(null);
  const [metric, setMetric] = useState('HARDNESS');
  const [day, setDay] = useState('0');
  const [value, setValue] = useState('');
  const [method, setMethod] = useState('');
  const [instrument, setInstrument] = useState('');
  const [evidence, setEvidence] = useState('');
  const [assessment, setAssessment] = useState<AnyObject | null>(null);
  const [dataKind, setDataKind] = useState<'MEASURED' | 'DEMO_SYNTHETIC'>('MEASURED');
  const [activeTab, setActiveTab] = useState<'doe' | 'lab'>('doe');
  const [studies, setStudies] = useState<AnyObject[]>([]);
  const [selectedStudyId, setSelectedStudyId] = useState('');
  const [batches, setBatches] = useState<AnyObject[]>([]);
  const [measurements, setMeasurements] = useState<AnyObject[]>([]);
  const [connection, setConnection] = useState<'checking' | 'online' | 'offline'>('checking');

  async function refreshStudies() {
    const existing = await api('/api/v4.5/studies');
    setStudies(Array.isArray(existing) ? existing : []);
  }
  async function openStudy(id: string) {
    const record = await api(`/api/v4.5/studies/${encodeURIComponent(id)}`);
    const [batchRows, observations] = await Promise.all([
      api(`/api/v4.5/studies/${encodeURIComponent(id)}/batches`),
      api(`/api/v4.5/studies/${encodeURIComponent(id)}/measurements`)
    ]);
    setStudy({ ...record, study_id: record.id });setSelectedStudyId(record.id);
    setScenarioText(JSON.stringify(record.scenario, null, 2));
    setProtocolText(JSON.stringify(record.protocol, null, 2));
    setStudyTitle(record.title); setResearcher(record.created_by);
    setBatches(batchRows); setMeasurements(observations);
    setBatch(batchRows.length ? { ...batchRows[batchRows.length - 1], batch_id: batchRows[batchRows.length - 1].id } : null);
    setMetric(record.protocol?.metrics?.[0]?.code || 'HARDNESS');
    setAssessment(null);setActiveTab('lab');
    setNotice(`Đã mở nghiên cứu ${record.title}. Các số liệu đã lưu không bị ghi đè.`);
  }
  async function refreshBatches(studyId: string) {
    const rows = await api(`/api/v4.5/studies/${encodeURIComponent(studyId)}/batches`);
    setBatches(rows);
  }
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        await api('/health/v4.5');
        if (!alive) return;
        setConnection('online');
        await refreshStudies();
      } catch { if (alive) setConnection('offline'); }
    })();
    return () => { alive = false; };
  }, []);


  const scenario = useMemo(() => { try { return JSON.parse(scenarioText) as AnyObject; } catch { return null; } }, [scenarioText]);
  const protocol = useMemo(() => { try { return JSON.parse(protocolText) as AnyObject; } catch { return null; } }, [protocolText]);
  const scenarioIssues = useMemo(() => formulaErrors(scenario as FormulaScenario | null), [scenario]);
  const protocolIssues = useMemo(() => protocolErrors(protocol as Protocol | null), [protocol]);
  const itemIds = useMemo(() => (scenario?.items || []).map((it: AnyObject) => String(it.item_id)), [scenario]);
  const metricSpec = useMemo(() => (protocol?.metrics || []).find((m: AnyObject) => m.code === metric), [protocol, metric]);
  const timepoints = metricSpec?.timepoints_days || [0];

  async function runTask(fn: () => Promise<void>) {
    setBusy(true); setNotice('Đang thực hiện thao tác...');
    try { await fn(); } catch (err: any) { setNotice(`Không thành công: ${err?.message || err}`); }
    finally { setBusy(false); }
  }
  const newStudy = () => {
    setStudy(null);setSelectedStudyId('');setBatches([]);setBatch(null);setMeasurements([]);setAssessment(null);setDesign(null);setDesignRequest(null);setDraftReview(null);
    setNotice('Đã mở biểu mẫu nghiên cứu mới. Các nghiên cứu đã lưu vẫn được giữ nguyên.');
  };
  const loadDemo = (kind: 'lip' | 'pad') => {
    const next = kind === 'lip' ? lipScenario : padScenario;
    setScenarioText(JSON.stringify(next, null, 2));
    setDesign(null);setDesignRequest(null); setDraftReview(null);setAssessment(null); setStudy(null); setSelectedStudyId(''); setBatch(null); setBatches([]); setMeasurements([]);
    if (kind === 'lip') {
      setFactorA('beeswax');setFactorB('jojoba_oil');setBalanceItem('base_premix');
      setMinA('16');setMaxA('20');setMinB('30');setMaxB('38');
      setProtocolText(JSON.stringify(demoProtocol, null, 2));
      setNotice('Đã nạp kịch bản Lip Balm mẫu; mọi chỉ tiêu quy cách là giá trị giả định của R&D.');
    } else {
      setFactorA('tea'); setFactorB(''); setBalanceItem('aqua');
      setMinA('0.5'); setMaxA('3');
      setNotice('Claim PAD còn hai cách hiểu. Phải chọn cách hiểu và bỏ ambiguous_claims trước khi khóa mẻ thử.');
    }
  };

  return (
    <main className="lab-root">
      <header className="lab-header">
        <div><p className="lab-eyebrow">FORMULA INTELLIGENCE / V4.5.2</p><h1>Thiết kế & xác minh thí nghiệm</h1>
          <p className="lab-muted">Từ mô phỏng nồng độ đến số liệu R&D có thể truy vết. Không thay thế kiểm nghiệm hoặc đánh giá pháp lý.</p></div>
        <div className="lab-head-actions"><a href="/optimizer">Bộ tối ưu V4.4</a><a href="/">Trang chủ</a></div>
      </header>
      <div className="lab-alert" role="status">{notice} <span className="lab-connection">API: {connection==='online'?'Đã kết nối':connection==='offline'?'Chưa kết nối':'Đang kiểm tra'}</span></div>
      <section className="lab-card lab-open-study">
        <div><h2>Nghiên cứu đã lưu</h2><p className="lab-muted">Mở lại mẻ và số đo từ cơ sở dữ liệu, không phải nhập lại từ đầu.</p></div>
        <div className="lab-open-controls">
          <select aria-label="Chọn nghiên cứu đã lưu" value={selectedStudyId} id="existing-study" onChange={e=>{ if(e.target.value)runTask(async()=>openStudy(e.target.value)); else newStudy(); }}>
            <option value="">Chọn nghiên cứu để tiếp tục...</option>
            {studies.map(s=><option key={s.id} value={s.id}>{s.title} ({s.id})</option>)}
          </select>
          <button type="button" className="secondary" disabled={busy} onClick={()=>runTask(refreshStudies)}>Làm mới</button>
          <button type="button" className="secondary" onClick={newStudy}>Nghiên cứu mới</button>
        </div>
      </section>
      <div className="lab-tabs"><button className={activeTab==='doe'?'active':''} onClick={()=>setActiveTab('doe')}>1. Thiết kế thí nghiệm</button>
        <button className={activeTab==='lab'?'active':''} onClick={()=>setActiveTab('lab')}>2. Mẻ thử & dữ liệu đo</button></div>
      <section className="lab-grid">
        <div className="lab-main">
          <article className="lab-card">
            <div className="lab-line"><h2>Snapshot công thức</h2><div className="lab-actions"><button className="secondary" onClick={()=>loadDemo('lip')}>Mẫu Lip Balm</button><button className="secondary" onClick={()=>loadDemo('pad')}>Mẫu PAD/AHA</button></div></div>
            <p className="lab-muted">Chỉnh nguyên liệu và khoảng % trực tiếp trong bảng; dữ liệu premix chưa rõ vẫn được giữ nguyên. Snapshot nghiên cứu đã lưu luôn ở chế độ chỉ đọc.</p>
            {scenario && Array.isArray(scenario.items) ? <FormulaEditor value={scenario as FormulaScenario} onChange={v=>{setScenarioText(JSON.stringify(v,null,2));setDesign(null);setDesignRequest(null);setDraftReview(null);}} locked={Boolean(study)} onError={setNotice}/> : <p className="lab-warning">JSON kịch bản không hợp lệ. Hãy khôi phục bằng mẫu hoặc chỉnh ở chế độ nâng cao.</p>}
            <details className="lab-advanced"><summary>Chế độ nâng cao: xem / chỉnh JSON công thức</summary>
              <textarea className="codearea" spellCheck={false} aria-label="JSON công thức" readOnly={Boolean(study)} value={scenarioText} onChange={e=>{setScenarioText(e.target.value);setDesign(null);setDesignRequest(null);}} rows={12}/></details>
            <div className="lab-small">{scenario ? `${itemIds.length} nguyên liệu đầu vào • ${scenario.product_type || 'Chưa phân loại'}` : 'JSON không hợp lệ'}</div>
            <div className="lab-actions lab-review-actions"><button className="secondary" disabled={busy||scenarioIssues.length>0} onClick={()=>runTask(async()=>{const r=await api('/api/v4.5/review-draft',{method:'POST',body:JSON.stringify({scenario})});setDraftReview(r);setNotice('Đã kiểm tra nháp bằng bộ giải V4.4; chưa phê duyệt công thức.');})}>Kiểm tra nháp & khoảng khả thi</button></div>
            {draftReview&&<div className="lab-draft-result"><strong>Kiểm tra nháp: {draftReview.status==='FEASIBLE'?'Có nghiệm số học':draftReview.status==='REQUIRES_CLAIM_RESOLUTION'?'Cần xác minh claim':'Chưa có nghiệm phù hợp'}</strong><p className="lab-muted">{draftReview.unresolved_grade_item_ids?.length || 0} grade chưa rõ cấu tử • Chưa đánh giá an toàn/pháp lý/độ ổn định</p>{draftReview.notes?.map((note:string,i:number)=><p key={i}>{note}</p>)}</div>}
          </article>
          {activeTab==='doe' ? <article className="lab-card">
            <h2>Biến khảo sát và cân bằng 100%</h2>
            <p className="lab-muted">Mỗi biến dùng hai mức thấp/cao. Các thành phần còn lại được cố định tại nghiệm mẫu; một nguyên liệu được chỉ định để cân bằng tổng.</p>
            <div className="lab-formgrid"><label>Biến thứ nhất<select value={factorA} onChange={e=>setFactorA(e.target.value)}>{itemIds.map((id:string)=><option key={id}>{id}</option>)}</select></label>
              <label>Mức thấp (%)<input type="number" value={minA} onChange={e=>setMinA(e.target.value)}/></label>
              <label>Mức cao (%)<input type="number" value={maxA} onChange={e=>setMaxA(e.target.value)}/></label>
              <label>Biến thứ hai (tùy chọn)<select value={factorB} onChange={e=>setFactorB(e.target.value)}><option value="">Không sử dụng</option>{itemIds.map((id:string)=><option key={id}>{id}</option>)}</select></label>
              <label>Mức thấp (%)<input type="number" value={minB} onChange={e=>setMinB(e.target.value)}/></label>
              <label>Mức cao (%)<input type="number" value={maxB} onChange={e=>setMaxB(e.target.value)}/></label>
              <label>Nguyên liệu cân bằng<select value={balanceItem} onChange={e=>setBalanceItem(e.target.value)}>{itemIds.map((id:string)=><option key={id}>{id}</option>)}</select></label></div>
            <button disabled={busy || !scenario} onClick={()=>runTask(async()=>{
              if(scenarioIssues.length)throw new Error('Công thức còn lỗi: '+scenarioIssues[0]);
              if(!factorA || factorA===balanceItem || factorB===balanceItem || (factorB && factorB===factorA))throw new Error('Chọn biến DoE và nguyên liệu cân bằng khác nhau.');
              if([minA,maxA,...(factorB?[minB,maxB]:[])].some(s=>!s.trim()||!Number.isFinite(Number(s))))throw new Error('Điền đủ các mức DoE hợp lệ.');
              const vars=[{item_id:factorA,low:Number(minA),high:Number(maxA)}];
              if(factorB)vars.push({item_id:factorB,low:Number(minB),high:Number(maxB)});
              const request={scenario,variables:vars,balance_item_id:balanceItem};
              const r=await api('/api/v4.5/design-experiments',{method:'POST',body:JSON.stringify(request)});
              setDesignRequest(request);setDesign(r); setNotice(`Đã tạo ${r.candidate_count} phương án, trong đó ${r.feasible_count} có nghiệm khả thi.`);
            })}>Tạo thiết kế DoE</button>
          </article> : <article className="lab-card">
            <h2>Protocol xác minh</h2><p className="lab-muted">Định nghĩa chỉ tiêu, thời điểm đo và khoảng chấp nhận trong biểu mẫu. Nguồn quy cách phải được R&D xác nhận.</p>
            {protocol && Array.isArray(protocol.metrics) ? <ProtocolEditor value={protocol as Protocol} locked={Boolean(study)} onChange={v=>setProtocolText(JSON.stringify(v,null,2))}/> : <p className="lab-warning">JSON protocol không hợp lệ. Nạp lại mẫu hoặc chỉnh trong chế độ nâng cao.</p>}
            <details className="lab-advanced"><summary>Chế độ nâng cao: xem / chỉnh JSON protocol</summary>
              <textarea className="codearea" spellCheck={false} aria-label="JSON protocol" readOnly={Boolean(study)} value={protocolText} onChange={e=>setProtocolText(e.target.value)} rows={12}/></details>
            <div className="lab-formgrid"><label>Tên nghiên cứu<input value={studyTitle} onChange={e=>setStudyTitle(e.target.value)}/></label>
              <label>Người phụ trách<input value={researcher} onChange={e=>setResearcher(e.target.value)} placeholder="Mã người nghiên cứu"/></label></div>
            <button disabled={busy || !scenario || !protocol || Boolean(study)} onClick={()=>runTask(async()=>{
              if (scenarioIssues.length)throw new Error('Công thức còn lỗi: '+scenarioIssues[0]);
              if (protocolIssues.length)throw new Error('Protocol còn lỗi: '+protocolIssues[0]);
              if (!scenario) throw new Error('Chưa có công thức để khóa nghiên cứu.');
              if (scenario.ambiguous_claims?.length)throw new Error('Claim còn nhiều cách hiểu, cần xác minh trước khi khóa nghiên cứu.');
              if(!studyTitle.trim()||!researcher.trim())throw new Error('Điền tên nghiên cứu và người phụ trách.');
              const r=await api('/api/v4.5/studies',{method:'POST',body:JSON.stringify({title:studyTitle,created_by:researcher,scenario,protocol,
                ...(design && designRequest ? {doe_design:designRequest}: {})})});
              setStudy(r);setSelectedStudyId(r.study_id);setBatch(null);setBatches([]);setMeasurements([]);setAssessment(null);await refreshStudies();setNotice('Đã khóa snapshot công thức và tạo protocol. Chưa có dữ liệu thử nghiệm.');
            })}>Tạo nghiên cứu từ snapshot</button>
            {study && <div className="lab-summary"><strong>Mã nghiên cứu: {study.study_id}</strong><span>SHA-256: {study.formula_sha256}</span></div>}
            {study && <><h3>Ghi nhận mẻ thử theo phương án DoE</h3>
              <BatchTraceabilityEditor key={study.study_id} studyId={study.study_id} defaultOperator={researcher}
                onError={message=>setNotice(`Không thành công: ${message}`)}
                onCreated={async b=>{setBatch(b);await refreshBatches(study.study_id);setNotice(`Đã lưu mẻ ${b.lot_code}: ${b.traceability_status}.`);}}/>
            </>}
            {study && batches.length > 0 && <div className="lab-formgrid"><label>Chọn mẻ để nhập đo
              <select value={batch?.batch_id || ''} onChange={e=>{const b=batches.find(x=>x.id===e.target.value);setBatch(b?{...b,batch_id:b.id}:null);}}>
                <option value="">Chọn mẻ...</option>{batches.map(b=><option value={b.id} key={b.id}>{b.lot_code}</option>)}
              </select></label></div>}
            {study && batch && <><h3>Nhập số liệu thực nghiệm</h3><p className="lab-muted">Giá trị không được tự tạo. Bản DEMO_SYNTHETIC luôn bị loại khỏi kết quả xác minh.</p>
              <div className="lab-formgrid">
                <label>Chỉ tiêu<select value={metric} onChange={e=>{setMetric(e.target.value);setDay('0');}}>{(protocol?.metrics||[]).map((m:AnyObject)=><option key={m.code} value={m.code}>{m.name || m.code}</option>)}</select></label>
                <label>Ngày đo<select value={day} onChange={e=>setDay(e.target.value)}>{timepoints.map((d:number)=><option key={d} value={d}>{d}</option>)}</select></label>
                <label>Giá trị {metricSpec?.kind==='categorical'?<select value={value} onChange={e=>setValue(e.target.value)}><option value="">Chọn kết quả...</option>{(metricSpec?.acceptable_values||[]).map((v:string)=><option value={v} key={v}>{v}</option>)}</select>:<input type="number" step="any" value={value} onChange={e=>setValue(e.target.value)} placeholder={`Đơn vị ${metricSpec?.unit || ''}`}/>}</label>
                <label>Phương pháp<input value={method} onChange={e=>setMethod(e.target.value)} placeholder="SOP nội bộ"/></label>
                <label>Mã thiết bị / nguồn quan sát<input value={instrument} onChange={e=>setInstrument(e.target.value)} placeholder="INSTR-01 / visual"/></label>
                <label>Đường dẫn bằng chứng<input value={evidence} onChange={e=>setEvidence(e.target.value)} placeholder="labbook://..."/></label>
                <label>Loại dữ liệu<select value={dataKind} onChange={e=>setDataKind(e.target.value as 'MEASURED'|'DEMO_SYNTHETIC')}><option value="MEASURED">Đo thực tế</option><option value="DEMO_SYNTHETIC">Giả lập minh họa (không tính)</option></select></label>
              </div>
              <button disabled={busy} onClick={()=>runTask(async()=>{
                if (!value.trim()) throw new Error('Cần nhập giá trị đo, không tự coi ô trống là 0.');
                if (metricSpec?.kind==='numeric' && !Number.isFinite(Number(value))) throw new Error('Giá trị phải là số hữu hạn.');
                if(dataKind==='MEASURED' && (!method.trim()||!instrument.trim()||!evidence.trim())) throw new Error('Dữ liệu đo thực tế cần phương pháp, thiết bị/nguồn và liên kết bằng chứng.');
                const v=metricSpec?.kind==='numeric'?Number(value):value;
                await api(`/api/v4.5/studies/${study.study_id}/measurements`,{method:'POST',body:JSON.stringify({batch_id:batch.batch_id,metric_code:metric,day:Number(day),value:v,unit:metricSpec?.unit || '',method,instrument_id:instrument,operator:researcher,evidence_uri:evidence,data_kind:dataKind})});
                setNotice('Đã thêm quan sát mới vào nhật ký bất biến.');setValue('');setMeasurements(await api(`/api/v4.5/studies/${study.study_id}/measurements`));
              })}>Lưu số liệu và nguồn</button></>}
            {study && <><button className="secondary" disabled={busy} onClick={()=>runTask(async()=>{const r=await api(`/api/v4.5/studies/${study.study_id}/assessment`);setAssessment(r);setNotice('Đã cập nhật báo cáo đối chiếu với giới hạn do R&D thiết lập.');})}>Đánh giá dữ liệu thí nghiệm</button>
            <p className="lab-muted">Số quan sát đã lưu: {measurements.length}. Các quan sát demo bị loại khỏi tính toán R&D.</p>
            {measurements.length>0&&<div className="lab-scroll"><table><thead><tr><th>Mẻ</th><th>Chỉ tiêu</th><th>Ngày</th><th>Giá trị</th><th>Nguồn</th></tr></thead><tbody>{measurements.slice(-20).reverse().map((m:AnyObject)=><tr key={m.id}><td>{m.batch_id?.slice?.(0,12)}</td><td>{m.metric_code}</td><td>{m.day}</td><td>{m.value_numeric ?? m.value_text}</td><td>{m.data_kind==='MEASURED'?'Đo':'Demo'}</td></tr>)}</tbody></table></div>}</>}
          </article>}
        </div>
        <aside className="lab-side">
          <article className="lab-card"><h2>Kết quả V4.5</h2>
            {activeTab==='doe' && design ? <><div className="lab-kpis"><div><b>{design.candidate_count}</b><small>Phương án</small></div><div><b>{design.feasible_count}</b><small>Có nghiệm</small></div></div>
              <div className="lab-scroll"><table><thead><tr><th>Mẻ đề xuất</th><th>Cân bằng</th><th>Trạng thái</th></tr></thead><tbody>{design.results?.map((r:AnyObject)=><tr key={r.candidate_id}><td>{r.candidate_id}<small>{r.design_point}</small></td><td>{r.balance_percent?.toFixed?.(2) ?? r.balance_percent}%</td><td>{r.status==='FEASIBLE'?'Khả thi':'Cần sửa'}</td></tr>)}</tbody></table></div>
              <p className="lab-muted">Nghiệm chỉ thể hiện khả thi toán học; chưa đo tính chất sản phẩm.</p></> : null}
            {activeTab==='lab' && assessment ? <><div className="lab-kpis"><div><b>{assessment.data_coverage_percent}%</b><small>Độ phủ dữ liệu đo</small></div><div><b>{assessment.out_of_user_spec_count}</b><small>Ngoài quy cách</small></div></div>
              <p><strong>Trạng thái dữ liệu đo:</strong> {assessment.status}</p><p className="lab-muted">Truy vết mẻ: {assessment.traceability?.linked_batches ?? 0}/{assessment.traceability?.total_batches ?? 0}. {assessment.traceability?.review_readiness === 'INCOMPLETE' ? 'Có mẻ chưa có hồ sơ cân hoặc phương án.' : 'Trạng thái truy vết được hiển thị riêng.'}</p><p className="lab-muted">Đã ghi: {assessment.completed_slots}/{assessment.required_slots} chỉ tiêu–thời điểm–mẻ.</p>
              {assessment.metric_trends?.filter((t:AnyObject)=>t.mean_of_batch_means!==null).map((t:AnyObject)=><div key={`${t.metric_code}-${t.day}`} className="lab-metric"><strong>{t.metric_code}</strong><span>Ngày {t.day}: {t.mean_of_batch_means} {t.unit}</span><small>{t.independent_batches} mẻ độc lập</small></div>)}
              </> : null}
            {!design && !assessment && <p className="lab-muted">Chưa có kết quả. Chạy DoE hoặc tạo nghiên cứu và nhập số liệu đo để xem báo cáo.</p>}
          </article>
          <article className="lab-card"><h2>Kiểm soát bằng chứng</h2><ul className="lab-list"><li>Không suy diễn số đo từ % nguyên liệu.</li><li>Chỉ số đo có nguồn mới được dùng đánh giá.</li><li>Ghi lại công thức bằng SHA-256.</li><li>Phân biệt DEMO và MEASURED.</li><li>Không tự động xác nhận đủ điều kiện sản xuất.</li></ul></article>
        </aside>
      </section>
    </main>
  );
}
