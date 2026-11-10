"""Formula Intelligence V4.4: transparent linear concentration feasibility / interval engine.

All percentages are mass % of finished product. No chemical/legal/safety approval.
A commercial raw material is an x variable, its resolved INCI components are z flows.
Unknown grade composition remains an unresolved mass variable, never invented INCI.
Only explicitly modeled components are used to infer finished INCI concentrations.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from collections import defaultdict
from typing import Any
import math
import json
from scipy.optimize import linprog

EPS=1e-7
MAX_ITEMS=60

class InputError(ValueError): pass

def finite(value, title):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise InputError(f'{title}: yêu cầu số hữu hạn')
    return float(value)

def issue(code, severity, message, details=None):
    return {'code':code,'severity':severity,'message_vi':message,'details':details or {}}

@dataclass
class LinearRow:
    vector: list[float]
    rhs: float
    code: str
    description: str

class LinearModel:
    def __init__(self, n):
        self.n=n
        self.bounds=[(0.,None)]*n
        self.eq=[]
        self.ub=[]
    def add(self, terms, op, rhs, code, desc):
        v=[0.0]*self.n
        for idx, coef in terms.items(): v[idx]+=coef
        row=LinearRow(v,float(rhs),code,desc)
        if op=='eq':self.eq.append(row)
        elif op=='le':self.ub.append(row)
        elif op=='ge':self.ub.append(LinearRow([-x for x in v],-float(rhs),code,desc))
        else: raise ValueError(op)
    def solve(self,objective=None,omit_codes=frozenset()):
        eq=[r for r in self.eq if r.code not in omit_codes]
        ub=[r for r in self.ub if r.code not in omit_codes]
        return linprog(
            objective if objective is not None else [0.0]*self.n,
            A_eq=[r.vector for r in eq] or None,b_eq=[r.rhs for r in eq] or None,
            A_ub=[r.vector for r in ub] or None,b_ub=[r.rhs for r in ub] or None,
            bounds=self.bounds,method='highs',options={'dual_feasibility_tolerance':1e-7,'primal_feasibility_tolerance':1e-7})

def _scalar_bounds(spec, default_low, default_high, name):
    if spec is None:spec={}
    if isinstance(spec,(int,float)): spec={'min':spec,'max':spec}
    if not isinstance(spec,dict):raise InputError(f'{name}: khoảng phải là object')
    lo=finite(spec.get('min',default_low),f'{name}.min')
    hi=finite(spec.get('max',default_high),f'{name}.max')
    if not 0<=lo<=hi<=default_high+EPS:raise InputError(f'{name}: khoảng không hợp lệ ({lo};{hi})')
    return (lo,hi)

def prepare_scenario(data:dict, catalog=None):
    if not isinstance(data,dict):raise InputError('Dữ liệu đầu vào phải là object')
    items=data.get('items')
    if not isinstance(items,list) or not 1<=len(items)<=MAX_ITEMS:raise InputError('Cần 1–60 nguyên liệu đầu vào')
    mode=data.get('template_mode','advisory')
    if mode not in ('advisory','strict'):raise InputError('template_mode phải là advisory hoặc strict')
    keys=set();issues=[];by_group=defaultdict(list);comp_items=[]
    for i,r in enumerate(items):
        if not isinstance(r,dict):raise InputError('Mỗi nguyên liệu phải là object')
        key=str(r.get('item_id','')).strip()
        if not key or key in keys:raise InputError(f'item_id rỗng hoặc trùng: {key}')
        keys.add(key)
        group=str(r.get('group_code','')).strip()
        if not group:raise InputError(f'{key}: thiếu group_code')
        bounds=_scalar_bounds(r.get('percent_bounds'),0,100,f'{key}.percent_bounds')
        if r.get('selected',True) is False:raise InputError(f'{key}: không đưa item chưa chọn vào solver')
        if bounds[1]<=0:raise InputError(f'{key}: nguyên liệu đã chọn cần max_percent > 0')
        # An item counted as selected must contribute actual mass in all candidate solutions.
        if bounds[0]==0:bounds=(1e-5,bounds[1])
        comps=r.get('composition')
        if comps is None:
            comps={'status':'unknown','complete':False,'components':[]}
        if not isinstance(comps,dict):raise InputError(f'{key}: composition phải là object')
        status=comps.get('status','unknown')
        if status not in ('verified','supplier_range','user_assumption','unknown'):
            raise InputError(f'{key}: composition.status không hợp lệ')
        complete=bool(comps.get('complete',False))
        rows=comps.get('components',[])
        if not isinstance(rows,list) or len(rows)>35:raise InputError(f'{key}: danh sách components không hợp lệ')
        seen=set();parts=[]
        for c in rows:
            name=str(c.get('inci','')).strip()
            if not name or name.casefold() in seen:raise InputError(f'{key}: INCI rỗng hoặc lặp trong composition')
            seen.add(name.casefold())
            a=finite(c.get('fraction_min',0),f'{key}:{name}.fraction_min')
            b=finite(c.get('fraction_max',1),f'{key}:{name}.fraction_max')
            if not 0<=a<=b<=1:raise InputError(f'{key}:{name}: fraction không thuộc 0..1')
            parts.append({'inci':name,'lo':a,'hi':b})
        if complete:
            if not parts or sum(c['lo'] for c in parts)>1+EPS or sum(c['hi'] for c in parts)<1-EPS:
                raise InputError(f'{key}: composition.complete không thể cân bằng 100%')
        else:
            if sum(c['lo'] for c in parts)>1+EPS:raise InputError(f'{key}: tổng cận dưới cấu tử > 100%')
        if status=='verified' and not r.get('composition_source_url'):
            issues.append(issue('VERIFIED_LABEL_WITHOUT_SOURCE','review',f'{key}: đánh dấu verified nhưng chưa có URL bằng chứng.'))
        if status!='verified':
            issues.append(issue('COMPONENT_MODEL_NOT_VERIFIED','info',f'{key}: dữ liệu cấu tử chưa được xác minh theo COA/grade.',{'status':status}))
        if not complete:
            issues.append(issue('PREMIX_COMPOSITION_UNRESOLVED','review',f'{key}: còn phần thành phần chưa được định lượng, không suy luận INCI hoàn chỉnh.'))
        if catalog is not None and (int(data['product_id']),group) not in catalog.product_rules:
            issues.append(issue('GROUP_NOT_IN_PRODUCT_TEMPLATE','review',f'{group} chưa thuộc mẫu nhóm loại sản phẩm này.'))
        by_group[group].append(i)
        comp_items.append({'id':key,'group':group,'bounds':bounds,'parts':parts,'complete':complete,'status':status,'prior':r.get('prior_percent'), 'inci':r.get('inci'), 'grade_id':r.get('grade_id')})
    return comp_items, by_group, issues

def _build(data, catalog):
    items, groups, issues=prepare_scenario(data,catalog)
    n_raw=len(items)
    flow_specs=[]
    for i,item in enumerate(items):
        for part in item['parts']:
            flow_specs.append({'item_index':i,**part,'unresolved':False})
        if not item['complete']:
            flow_specs.append({'item_index':i,'inci':f'UNRESOLVED::{item["id"]}','lo':0.,'hi':1.,'unresolved':True})
    n=n_raw+len(flow_specs)
    model=LinearModel(n)
    for i,item in enumerate(items):model.bounds[i]=item['bounds']
    inci_indices=defaultdict(list);unresolved_indices=[]
    for j,f in enumerate(flow_specs):
        z=n_raw+j; i=f['item_index']
        if f['lo']>0:model.add({z:-1,i:f['lo']},'le',0,f'FRAC_LOW:{items[i]["id"]}:{f["inci"]}','Cận dưới thành phần')
        model.add({z:1,i:-f['hi']},'le',0,f'FRAC_HIGH:{items[i]["id"]}:{f["inci"]}','Cận trên thành phần')
        if f['unresolved']:unresolved_indices.append(z)
        else:inci_indices[f['inci'].casefold()].append(z)
    for i,item in enumerate(items):
        flow={j+n_raw:1. for j,f in enumerate(flow_specs) if f['item_index']==i}
        flow[i]=-1.
        model.add(flow,'eq',0,f'COMP_MASS:{item["id"]}','Phân rã grade phải đủ khối lượng')
    model.add({i:1. for i in range(n_raw)},'eq',100,'MASS_100','Cân bằng 100% khối lượng nguyên liệu cân')

    rules={}
    if catalog is not None and data.get('product_id') is not None:
        rules={g:r for (p,g),r in catalog.product_rules.items() if p==int(data['product_id'])}
    custom=data.get('group_limits',[])
    if not isinstance(custom,list):raise InputError('group_limits phải là danh sách')
    controls={};group_context=[]
    for group,idxs in groups.items():
        tr=rules.get(group)
        if tr:
            lo=float(tr.get('min_percent') or 0);hi=float(tr.get('max_percent') or 100)
            role=tr.get('role')
            min_count=int(tr.get('min_ingredients') or 0); max_count=int(tr.get('max_ingredients') or 99)
            if len(idxs)>max_count:
                issues.append(issue('GROUP_COUNT_ABOVE_TEMPLATE','review',f'{group}: chọn {len(idxs)} > {max_count} nguyên liệu (dải tham chiếu).'))
            if len(idxs)<min_count:
                issues.append(issue('GROUP_COUNT_BELOW_TEMPLATE','review',f'{group}: chọn {len(idxs)} < {min_count} nguyên liệu (dải tham chiếu).'))
            group_context.append({'group_code':group,'source':'screenshot_reference','minimum':lo,'maximum':hi,'count_min':min_count,'count_max':max_count,'role':role,'hard':data.get('template_mode')=='strict'})
            if mode_is_strict(data):
                terms={i:1. for i in idxs}
                model.add(terms,'ge',lo,f'TEMPLATE_MIN:{group}','Ngưỡng dưới mẫu ảnh (strict)')
                model.add(terms,'le',hi,f'TEMPLATE_MAX:{group}','Ngưỡng trên mẫu ảnh (strict)')
        else:
            group_context.append({'group_code':group,'source':'unmapped','minimum':None,'maximum':None,'hard':False})
    if mode_is_strict(data) and catalog is not None:
        for g, r in rules.items():
            if r.get('role')=='carrier_selector' and g not in groups:
                # UI shows virtual 100% base. It is not a weighed material.
                issues.append(issue('UI_BASE_PLACEHOLDER_IGNORED','info','Nền 100% của màn hình gốc là placeholder, không cộng vào khối lượng.'))
                continue
            minimum=int(r.get('min_ingredients') or 0)
            if minimum>0 and len(groups.get(g,[]))<minimum:
                issues.append(issue('REQUIRED_GROUP_NOT_SELECTED','error',f'Mẫu yêu cầu nhóm {g} tối thiểu {minimum} nguyên liệu.'))
    for row in custom:
        group=str(row.get('group_code','')).strip()
        if not group or group in controls:raise InputError('group_limits trùng hoặc thiếu group_code')
        controls[group]=row
        if group not in groups:
            issues.append(issue('USER_GROUP_NOT_SELECTED','error',f'Nhóm {group} có ràng buộc nhưng chưa chọn nguyên liệu.'))
            continue
        lo,hi=_scalar_bounds({'min':row.get('min_percent',0),'max':row.get('max_percent',100)},0,100,f'group:{group}')
        if row.get('enforce',True):
            terms={i:1. for i in groups[group]}
            model.add(terms,'ge',lo,f'USER_MIN:{group}','Ngưỡng dưới người dùng')
            model.add(terms,'le',hi,f'USER_MAX:{group}','Ngưỡng trên người dùng')
        group_context.append({'group_code':group,'source':'user_defined','minimum':lo,'maximum':hi,'hard':bool(row.get('enforce',True)),'target':row.get('target_percent')})
    claims=data.get('claims',[])
    if not isinstance(claims,list):raise InputError('claims phải là danh sách')
    claim_applied=[]
    raw_by_id={x['id']:i for i,x in enumerate(items)}
    for j,c in enumerate(claims):
        val=finite(c.get('percent'),f'claim{j}.percent')
        if not 0<=val<=100:raise InputError(f'claim {j} ngoài 0..100')
        basis=c.get('basis')
        if basis=='raw_material':
            key=c.get('item_id')
            if key not in raw_by_id:raise InputError(f'claim {j}: thiếu item_id hợp lệ')
            model.add({raw_by_id[key]:1},'eq',val,f'CLAIM_RAW:{j}','% cân nguyên liệu (claim basis)')
            claim_applied.append({'basis':basis,'target':key,'value':val,'enforced':True})
        elif basis=='finished_inci':
            key=str(c.get('inci','')).casefold().strip()
            if not key:raise InputError(f'claim {j}: thiếu INCI')
            if unresolved_indices:
                issues.append(issue('FINISHED_CLAIM_INDETERMINATE','error','Không thể kiểm chứng % INCI công bố khi còn premix có phần cấu tử chưa biết.',{'inci':key}))
                claim_applied.append({'basis':basis,'target':key,'value':val,'enforced':False})
            elif key not in inci_indices:
                issues.append(issue('FINISHED_CLAIM_NOT_MODELED','error','INCI trong claim không xuất hiện trong các cấu tử đã mô hình hóa.',{'inci':key}))
                claim_applied.append({'basis':basis,'target':key,'value':val,'enforced':False})
            else:
                model.add({i:1 for i in inci_indices[key]},'eq',val,f'CLAIM_INCI:{j}','Claim % INCI thành phẩm')
                claim_applied.append({'basis':basis,'target':key,'value':val,'enforced':True})
        else:raise InputError(f'claim {j}: basis phải là raw_material hoặc finished_inci')
    if data.get('label_order_known_above_one'):
        labels=data['label_order_known_above_one']
        if not isinstance(labels,list) or len(labels)>100:raise InputError('label_order_known_above_one không hợp lệ')
        if unresolved_indices:
            issues.append(issue('LABEL_ORDER_NOT_ENFORCED','review','Còn premix chưa rõ INCI, không thể ràng buộc đầy đủ thứ tự nhãn.'))
        else:
            for j,label in enumerate(labels):
                key=label.casefold().strip()
                if key not in inci_indices:raise InputError(f'INCI không có trong mô hình: {label}')
                model.add({idx:1 for idx in inci_indices[key]},'ge',1,f'LABEL_THRESHOLD:{j}','Người dùng xác nhận >1%')
                if j>0:
                    prev=labels[j-1].casefold().strip()
                    terms=defaultdict(float)
                    for z in inci_indices[prev]:terms[z]-=1
                    for z in inci_indices[key]:terms[z]+=1
                    model.add(dict(terms),'le',0,f'LABEL_ORDER:{j}','Thứ tự INCI trên 1%')
    return model,items,groups,inci_indices,unresolved_indices,flow_specs,issues,group_context,claim_applied

def mode_is_strict(data): return data.get('template_mode','advisory')=='strict'

def _round(n):return round(float(n),5)

def _range(model,objective):
    lo=model.solve(objective)
    hi=model.solve([-x for x in objective])
    if not lo.success or not hi.success:raise RuntimeError('Unexpected optimized interval failure')
    return [_round(lo.fun),_round(-hi.fun)]

def _check_template_refs(groups, totals, group_context, issues):
    for ctx in group_context:
        if ctx['source']!='screenshot_reference' or ctx['hard']:continue
        group=ctx['group_code']; total=totals.get(group,0)
        if total<ctx['minimum']-1e-5 or total>ctx['maximum']+1e-5:
            issues.append(issue('OUTSIDE_SCREENSHOT_REFERENCE','review',f'{group}: {total:.3f}% ngoài dải tham khảo {ctx["minimum"]}–{ctx["maximum"]}%.',{'group_code':group,'percent':_round(total)}))

def _representative(model,items,groups,data):
    """L1 objective around explicit priors only; without priors use equal-share synthetic anchor.
    Solves an extended LP; never confuses a chosen point with a recovered real formula.
    """
    n=model.n
    reference=[]
    for i,item in enumerate(items):
        prior=item['prior']
        if prior is None:
            reference.append((i,100/len(items),0.03,'equal_share_synthetic'))
        else:
            val=finite(prior,f'{item["id"]}.prior_percent')
            if not 0<=val<=100:raise InputError('prior_percent ngoài 0..100')
            reference.append((i,val,1.0,'user_prior'))
    for group in data.get('group_limits',[]):
        if group.get('target_percent') is not None and group.get('group_code') in groups:
            val=finite(group['target_percent'],'target_percent')
            if not 0<=val<=100:raise InputError('target_percent ngoài 0..100')
            reference.append(([i for i in groups[group['group_code']]],val,1.3,'user_group_target'))
    # two slack vars per prior x - dev_plus + dev_minus = target
    m=len(reference);ext=LinearModel(n+2*m)
    ext.bounds=model.bounds+[(0,None)]*(2*m)
    ext.eq=[LinearRow(r.vector+[0.]*(2*m),r.rhs,r.code,r.description) for r in model.eq]
    ext.ub=[LinearRow(r.vector+[0.]*(2*m),r.rhs,r.code,r.description) for r in model.ub]
    obj=[0.0]*ext.n
    for k,(idxs,target,weight,_) in enumerate(reference):
        terms={idx:1. for idx in (idxs if isinstance(idxs,list) else [idxs])}
        terms[n+2*k]=-1.;terms[n+2*k+1]=1.
        ext.add(terms,'eq',target,f'PRIOR:{k}','Tham chiếu không phải dữ liệu thật')
        obj[n+2*k]=weight;obj[n+2*k+1]=weight
    res=ext.solve(obj)
    if not res.success:raise RuntimeError('No representative although feasible')
    return res.x[:n],{'mode':'weighted_L1_priors','user_prior_count':sum(p[3]=='user_prior' for p in reference),'synthetic_anchor_count':sum(p[3]=='equal_share_synthetic' for p in reference),'evidence_status':'ILLUSTRATIVE_ONLY'}

def _diagnose(model):
    candidates=[]
    for r in model.eq+model.ub:
        if r.code not in ('MASS_100',) and (r.code.startswith(('USER_','TEMPLATE_','CLAIM_','LABEL_'))):
            candidates.append(r.code)
    candidates=list(dict.fromkeys(candidates))[:80]
    hints=[]
    for code in candidates:
        if model.solve(omit_codes={code}).success:
            hints.append(code)
        if len(hints)>=12:break
    return hints

def _label_check(labels,inci_totals,unresolved):
    if not labels:return {'status':'NOT_PROVIDED'}
    if unresolved>1e-6:return {'status':'INDETERMINATE_UNKNOWN_PREMIX'}
    known={k.casefold():v for k,v in inci_totals.items()}
    names=[str(name) for name in labels]
    missing=[name for name in names if name.casefold() not in known]
    if missing:return {'status':'INDETERMINATE_UNMODELED_INCI','missing':missing}
    vals=[known[name.casefold()] for name in names]
    wrong=[]
    # Compare all clearly above-1% ingredients. Once <=1 begins, >1 later is suspicious.
    for i in range(len(names)):
        for j in range(i+1,len(names)):
            if vals[j]>1+1e-6 and vals[i]+1e-6<vals[j]:wrong.append([names[i],names[j]])
    return {'status':'WARNING_ORDER_CONFLICT' if wrong else 'CONSISTENT_WITH_BASIC_ORDER','conflicts':wrong[:15], 'note':'Chưa xử lý riêng chất màu/ngoại lệ ghi nhãn; chỉ kiểm tra sơ bộ.'}

def solve_scenario(data, catalog=None):
    model,items,groups,inci_idxs,unres_idxs,flows,issues,g_context,claim_applied=_build(data,catalog)
    early_errors=[x for x in issues if x['severity']=='error']
    if early_errors:
        return {'engine_version':'4.4.0','status':'INSUFFICIENT_DATA_OR_SELECTION','issues':issues,
                'claims':claim_applied,'approved_for_manufacturing':False,'regulatory_status':'NOT_ASSESSED'}
    r=model.solve()
    if not r.success:
        return {'engine_version':'4.4.0','status':'INFEASIBLE','issues':issues+[issue('NO_FEASIBLE_SOLUTION','error','Không tồn tại nghiệm cân bằng 100% thỏa mãn các ràng buộc hiện có. Đề nghị kiểm tra các nhóm điều kiện được gợi ý.')],
                'diagnostic_single_constraint_removals':_diagnose(model),'mass_balance_target':100,
                'approved_for_manufacturing':False,'regulatory_status':'NOT_ASSESSED'}
    rep,method=_representative(model,items,groups,data)
    n_raw=len(items)
    result_items=[];result_groups=[];result_inci=[]
    raw_total=0.;group_totals={}
    for i,item in enumerate(items):
        objective=[0.]*model.n;objective[i]=1
        pct=_round(rep[i]);raw_total+=pct
        result_items.append({'item_id':item['id'],'group_code':item['group'],'grade_id':item['grade_id'], 'display_inci':item['inci'],
                             'percent_example':pct,'feasible_interval_percent':_range(model,objective),
                             'composition_status':item['status'],'complete_composition':item['complete']})
    for g,idx in sorted(groups.items()):
        objective=[0.]*model.n
        for i in idx:objective[i]=1
        total=_round(sum(rep[i] for i in idx));group_totals[g]=total
        result_groups.append({'group_code':g,'percent_example':total,'feasible_interval_percent':_range(model,objective),'raw_material_count':len(idx)})
    for inci,ids in sorted(inci_idxs.items()):
        objective=[0.]*model.n
        for i in ids:objective[i]=1
        val=_round(sum(rep[i] for i in ids))
        result_inci.append({'inci':inci,'percent_example_known_contribution':val,
                            'feasible_known_contribution_interval_percent':_range(model,objective),
                            'basis':'complete_inci' if not unres_idxs else 'known_contributions_only'})
    unresolved=_round(sum(rep[i] for i in unres_idxs))
    unres_obj=[0.]*model.n
    for i in unres_idxs:unres_obj[i]=1
    unresolved_interval=_range(model,unres_obj) if unres_idxs else [0,0]
    _check_template_refs(groups,group_totals,g_context,issues)
    if any(i['status']!='verified' for i in items):
        issues.append(issue('RESULT_DEPENDS_ON_ASSUMPTIONS','review','Ít nhất một sơ đồ cấu tử INCI còn giả định hoặc thiếu nguồn chứng thực.'))
    if not any(x['prior'] is not None for x in items):
        issues.append(issue('REPRESENTATIVE_IS_SYNTHETIC','info','Nghiệm minh họa dùng tham chiếu phân bổ đều, không suy ngược được tỷ lệ gốc từ INCI.'))
    if abs(sum(rep[:n_raw])-100)>1e-5:raise RuntimeError('Mass balance solver failure')
    incitot={x['inci']:x['percent_example_known_contribution'] for x in result_inci}
    label_check=_label_check(data.get('label_inci_order',[]),incitot,unresolved)
    if label_check['status'].startswith('WARNING'):
        issues.append(issue('LABEL_ORDER_SCREENING_WARNING','review','Nghiệm minh họa không phù hợp thứ tự INCI trên 1% trong nhãn cung cấp.'))
    return {'engine_version':'4.4.0','status':'FEASIBLE','claim_interpretations':claim_applied,
            'raw_material_total_percent':_round(sum(rep[:n_raw])),'items':result_items,'groups':result_groups,
            'inci_known_contributions':result_inci,'unresolved_composition_percent_example':unresolved,
            'unresolved_composition_feasible_interval_percent':unresolved_interval,
            'fully_resolved_inci':not unres_idxs,'label_order_screening':label_check,
            'group_range_references':g_context, 'representative_method':method,'issues':issues,
            'approved_for_manufacturing':False,'regulatory_status':'NOT_ASSESSED','stability_status':'NOT_TESTED',
            'range_interpretation':'Feasible under stated assumptions, NOT a measured or market typical concentration.'}

def solve_claim_alternatives(data, catalog=None):
    """One ambiguous marketing claim can branch into raw-material vs final INCI interpretations.
    All other constraints are kept unchanged. Cap at 8 combos.
    """
    candidates=data.get('ambiguous_claims',[])
    if not isinstance(candidates,list) or len(candidates)>3:raise InputError('ambiguous_claims: tối đa 3 claim')
    variants=[('base',deepcopy(data))]
    for j,c in enumerate(candidates):
        alts=c.get('interpretations',[])
        if not 1<=len(alts)<=2:raise InputError('Mỗi ambiguous_claim cần 1–2 interpretations')
        nxt=[]
        for name,sc in variants:
            for k,alternative in enumerate(alts):
                updated=deepcopy(sc)
                updated.setdefault('claims',[]).append({**alternative,'percent':c['percent']})
                nxt.append((f'{name}/claim{j+1}:{k+1}',updated))
        variants=nxt
    output=[]
    for label,sc in variants:
        sc.pop('ambiguous_claims',None)
        output.append({'scenario_id':label,'interpretation_summary':sc.get('claims',[]),'result':solve_scenario(sc,catalog)})
    return {'engine_version':'4.4.0','scenario_count':len(output),'scenarios':output,'approved_for_manufacturing':False}
