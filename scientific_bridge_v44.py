"""Non-authoritative V4.4 → V4.3 scientific SCREENING adapter.
Runs on an illustrative feasible raw-material scenario, not on a validated formula.
"""
from scientific_engine_v43 import ScientificEngineV43


def screen_representative(input_data, optimized_result):
    if optimized_result.get('status')!='FEASIBLE':
        return {'status':'NOT_RUN','reason':'No feasible representative formula'}
    out_items=[]
    input_by_id={str(x['item_id']):x for x in input_data['items']}
    for item in optimized_result['items']:
        row=input_by_id[item['item_id']]
        mapped={'inci':row.get('inci') or '', 'percent':item['percent_example'],
                'group_code':row['group_code']}
        if row.get('ingredient_id'):mapped['ingredient_id']=row['ingredient_id']
        if row.get('grade_id'):mapped['grade_id']=row['grade_id']
        out_items.append(mapped)
    # V4.3 accepts 100% with tight numerical tolerance; reconcile display rounding only.
    if out_items:
        out_items[-1]['percent']=round(100.0-sum(it['percent'] for it in out_items[:-1]),5)
    scenario={'product_type':input_data.get('product_type','Chưa xác định'),
              'physical_form':input_data.get('physical_form','unknown'),
              'items':out_items,'preservation_evidence':bool(input_data.get('preservation_evidence',False)),
              'solubilizer_system_confirmed':bool(input_data.get('solubilizer_system_confirmed',False))}
    for key in ('pH','water_phase_percent','process_temperature_c','process_intent'):
        if input_data.get(key) is not None: scenario[key]=input_data[key]
    # V4.3 uses old group assignment checks, which may not match a new optimizer template.
    # Evaluate grade/scientific screening independently; V4.4 handles group constraints.
    sci=ScientificEngineV43().evaluate(scenario)
    return {'status':'SCREENING_ONLY','based_on':'V4.4 illustrative representative solution',
            'scientific_engine_version':'4.3.0','issues':sci['issues'],
            'scientific_compatibility_status':sci['scientific_compatibility_status'],
            'preservation_status':'NOT_VALIDATED','stability_status':'NOT_TESTED','regulatory_status':'NOT_ASSESSED',
            'approved_for_manufacturing':False}
