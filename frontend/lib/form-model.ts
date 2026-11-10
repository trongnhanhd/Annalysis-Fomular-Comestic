/* V4.5.2 — Pure helpers, no React dependency. Keep source claims, snapshots and
 * unknown commercial composition intact unless a human intentionally edits them. */
export type Obj = Record<string, any>;
export type FormulaItem = Obj & {
  item_id: string;
  inci: string;
  group_code: string;
  grade_id?: string;
  percent_bounds: { min: number; max: number };
  prior_percent?: number;
  composition?: Obj;
};
export type FormulaScenario = Obj & { items: FormulaItem[] };
export type MetricSpec = Obj & {
  code: string; name: string; kind: 'numeric' | 'categorical'; unit: string;
  timepoints_days: number[];
  target_min?: number | null; target_max?: number | null;
  acceptable_values?: string[];
};
export type Protocol = Obj & { metrics: MetricSpec[] };

export const finite = (n: unknown): n is number => typeof n === 'number' && Number.isFinite(n);
export const round = (v: number, digits = 4) => Number(v.toFixed(digits));
export function formulaTotal(formula: FormulaScenario): number {
  return round((formula.items || []).reduce((a, x) => a + (finite(x.prior_percent) ? x.prior_percent! : 0), 0));
}
export function formulaErrors(formula: FormulaScenario | null): string[] {
  if (!formula || !Array.isArray(formula.items) || !formula.items.length) return ['Cần nhập ít nhất một nguyên liệu.'];
  const problems: string[] = []; const identifiers = new Set<string>();
  for (let i = 0; i < formula.items.length; i++) {
    const row = formula.items[i]; const name = `Dòng ${i + 1}`;
    if (!row.item_id?.trim() || !/^[a-zA-Z0-9_-]+$/.test(row.item_id)) problems.push(`${name}: mã nguyên liệu chỉ được gồm chữ, số, _ hoặc -.`);
    if (identifiers.has(row.item_id)) problems.push(`${name}: mã nguyên liệu bị trùng.`);
    identifiers.add(row.item_id);
    if (!row.inci?.trim()) problems.push(`${name}: thiếu tên INCI/grade.`);
    if (!row.group_code?.trim()) problems.push(`${name}: thiếu mã nhóm chức năng.`);
    const lo = row.percent_bounds?.min, hi = row.percent_bounds?.max;
    if (!finite(lo) || !finite(hi) || lo < 0 || hi > 100 || lo > hi) problems.push(`${name}: khoảng phần trăm không hợp lệ.`);
    if (!finite(row.prior_percent) || row.prior_percent! < 0 || row.prior_percent! > 100) problems.push(`${name}: tỷ lệ mục tiêu không hợp lệ.`);
    if (finite(lo) && finite(hi) && finite(row.prior_percent) && (row.prior_percent! < lo - 1e-8 || row.prior_percent! > hi + 1e-8))
      problems.push(`${name}: tỷ lệ mục tiêu nằm ngoài khoảng min/max.`);
  }
  if (formula.items.length > 100) problems.push('Chỉ hỗ trợ tối đa 100 nguyên liệu trong trình biên tập.');
  return problems;
}
export function protocolErrors(protocol: Protocol | null): string[] {
  if (!protocol || !Array.isArray(protocol.metrics) || protocol.metrics.length === 0) return ['Cần ít nhất một chỉ tiêu kiểm tra.'];
  const problems: string[] = []; const seen = new Set<string>();
  protocol.metrics.forEach((m, i) => {
    const tag = `Chỉ tiêu ${i + 1}`;
    if (!/^[A-Z0-9_]{1,48}$/.test(m.code || '')) problems.push(`${tag}: mã chỉ tiêu cần chữ in hoa, số hoặc dấu _.`);
    if (seen.has(m.code)) problems.push(`${tag}: mã chỉ tiêu bị trùng.`);
    seen.add(m.code);
    if (!m.name?.trim()) problems.push(`${tag}: cần tên chỉ tiêu.`);
    if (!['numeric', 'categorical'].includes(m.kind)) problems.push(`${tag}: loại dữ liệu không hợp lệ.`);
    if (m.kind === 'numeric' && !m.unit?.trim()) problems.push(`${tag}: chỉ tiêu định lượng cần đơn vị.`);
    if (m.kind === 'categorical' && (!Array.isArray(m.acceptable_values) || !m.acceptable_values.length || m.acceptable_values.some(v => !v.trim()))) problems.push(`${tag}: nhập các giá trị được chấp nhận.`);
    const days = m.timepoints_days || [];
    if (!days.length || days.length > 32 || days.some(d => !Number.isInteger(d) || d < 0 || d > 3650) || new Set(days).size !== days.length)
      problems.push(`${tag}: ngày đo phải là danh sách số nguyên từ 0 đến 3650, không trùng.`);
    if (m.target_min != null && !finite(m.target_min)) problems.push(`${tag}: giá trị min không hợp lệ.`);
    if (m.target_max != null && !finite(m.target_max)) problems.push(`${tag}: giá trị max không hợp lệ.`);
    if (finite(m.target_min) && finite(m.target_max) && m.target_min > m.target_max) problems.push(`${tag}: min lớn hơn max.`);
  });
  if (protocol.metrics.length > 24) problems.push('Tối đa 24 chỉ tiêu thử nghiệm.');
  return problems;
}

export function balanceFormula(formula: FormulaScenario, balanceId: string): FormulaScenario {
  const idx = formula.items.findIndex(it => it.item_id === balanceId);
  if (idx < 0) throw new Error('Hãy chọn nguyên liệu cân bằng hợp lệ.');
  if (formulaErrors(formula).length) throw new Error('Hãy sửa lỗi nguyên liệu trước khi cân bằng.');
  const next = structuredClone(formula);
  const target = round(100 - next.items.reduce((sum, x, i) => i === idx ? sum : sum + x.prior_percent!, 0));
  const lo = next.items[idx].percent_bounds.min, hi = next.items[idx].percent_bounds.max;
  if (target < lo - 1e-8 || target > hi + 1e-8)
    throw new Error(`Không thể cân bằng: ${balanceId} cần ${target}%, ngoài khoảng ${lo}–${hi}%.`);
  next.items[idx].prior_percent = target;
  return next;
}
export function newIngredient(index: number): FormulaItem {
  return {item_id: `material_${index}`, inci: '', group_code: 'active', percent_bounds: {min: 0, max: 10}, prior_percent: 0,
    composition: {status:'unknown', complete:false, components:[]}};
}
export function newMetric(index: number): MetricSpec {
  return {code:`METRIC_${index}`,name:'',kind:'numeric',unit:'',timepoints_days:[0,7,28],target_min:null,target_max:null,
    acceptable_values:[],criteria_source:'USER_DEFINED',method:'',condition:''};
}
