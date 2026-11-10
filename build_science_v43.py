from __future__ import annotations
import csv, json, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
def write_csv(name,rows,fields):
    with (DATA/name).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def readcsv(p):return list(csv.DictReader(open(p,encoding='utf-8-sig')))
master={r['inci_name_candidate'].casefold():r for r in readcsv(DATA/'ingredients.csv')}

def iid(inci):return master.get(inci.casefold(),{}).get('ingredient_id', 'NEW-INCI-0001' if inci=='Oryza Sativa Bran Cera' else '')

sources=[
('S43-KAHL-WAX','KAHL World — Technical data sheets, product reference','https://www.kahlworld.com/news/download-category/technical-data-sheets/','supplier_product_web','Waxes, melting point and recommended use for exact grades'),
('S43-KAHL-2442L','KAHL World — KahlWax 2442L Carnauba','https://www.kahlworld.com/divi_overlay/kahlwax-2442l-carnauba/','supplier_product_web','Carnauba grade 2442L'),
('S43-KAHL-PRODUCTS','KAHL World — Product catalogue','https://www.kahlworld.com/products/','supplier_product_web','Rice wax, hydrogenated castor oil, KahlBase 4074 and qualitative INCI'),
('S43-LUB-1342','Lubrizol — Carbopol 1342','https://www.lubrizol.com/solutions/products/beauty/detail-pages/carbopol-1342-polymer','supplier_product_web','Carbopol 1342 grade, as supplied'),
('S43-ASH-NATROSOL','Ashland — Natrosol HEC (personal care/oral care)','https://origin-www.ashland.com/industries/personal-and-home-care/oral-care/natrosol-hydroxyethylcellulose','supplier_product_web','Hydroxyethylcellulose grade family, non-ionic, water solubility'),
('S43-CLAR-VELSAN','Clariant — Velsan CLC','https://www.clariant.com/en/Products/Velsan-CLC','supplier_product_web','Caprylyl Glycol specific grade with good water solubility, preservation booster'),
('S43-CLAR-NIP','Clariant — Nipaguard PE 9010','https://www.clariant.com/en/products/nipaguard-pe-9010-1','supplier_product_web','Phenoxyethanol/Ethylhexylglycerin blend; stability up to pH 12'),
('V42-LEGACY','Formula Intelligence V4.2 inherited internal dataset','', 'prior_dataset','190 candidate INCI; 4 supplier-scoped properties inherited; original sources remain in source_registry.csv')
]
write_csv('scientific_sources_v43.csv',[{'source_id':a,'source_title':b,'source_url':c,'source_type':d,'scope':e,'checked_date':'2026-11-09','evidence_status':'supplier_page_checked' if c else 'prior_dataset_only'} for a,b,c,d,e in sources],['source_id','source_title','source_url','source_type','scope','checked_date','evidence_status'])
source_url={a:c for a,b,c,d,e in sources}

# Every grade is exact supplier named product; generic INCI master is not upgraded to universal physical data.
grades=[
('S43-G-K8109','KahlWax 8109 Yellow Pharma Beeswax','Cera Alba','KAHL','lip_care;solid_cosmetic','S43-KAHL-WAX','single_inci_name_not_assay_verified'),
('S43-G-K2039L','KahlWax 2039L Candelilla','Euphorbia Cerifera Cera','KAHL','lip_care;solid_cosmetic','S43-KAHL-WAX','single_inci_name_not_assay_verified'),
('S43-G-K2442L','KahlWax 2442L Carnauba','Copernicia Cerifera Cera','KAHL','lip_care;color_cosmetic','S43-KAHL-2442L','single_inci_name_not_assay_verified'),
('S43-G-K2811','KahlWax 2811 Rice','Oryza Sativa Bran Cera','KAHL','lip_care;solid_cosmetic','S43-KAHL-PRODUCTS','single_inci_name_not_assay_verified'),
('S43-G-K2178','KahlWax 2178 Castor','Hydrogenated Castor Oil','KAHL','solid_cosmetic;emulsion','S43-KAHL-WAX','single_inci_name_not_assay_verified'),
('S43-G-K8139','KahlWax 8139 Organic Beeswax','Cera Alba','KAHL','lip_care;solid_cosmetic','S43-KAHL-WAX','single_inci_name_not_assay_verified'),
('S43-G-C1342','Carbopol 1342 polymer','Acrylates/C10-30 Alkyl Acrylate Crosspolymer','Lubrizol','aqueous;emulsion','S43-LUB-1342','single_inci_name_not_assay_verified'),
('S43-G-NATROSOL','Natrosol hydroxyethylcellulose (family)','Hydroxyethylcellulose','Ashland','aqueous;oral_care','S43-ASH-NATROSOL','grade_family_not_a_unique_grade'),
('S43-G-VCLC','Velsan CLC','Caprylyl Glycol','Clariant','emulsion;aqueous','S43-CLAR-VELSAN','single_inci_name_not_assay_verified'),
('S43-G-NIP9010','Nipaguard PE 9010','Phenoxyethanol;Ethylhexylglycerin','Clariant','aqueous;emulsion','S43-CLAR-NIP','blend_components_qualitative_only'),
('S43-G-K4074','KahlBase 4074 Natural Matte Lipstick','Multi-INCI (see composition)','KAHL','lipstick','S43-KAHL-PRODUCTS','blend_components_qualitative_only')
]
write_csv('supplier_grade_reference_v43.csv',[{'grade_id':a,'grade_name':b,'inci_declared':c,'supplier':d,'use_context':e,'source_id':f,'source_url':source_url[f],'composition_status':g,'coa_verified':'false','regulatory_approved':'false'} for a,b,c,d,e,f,g in grades],['grade_id','grade_name','inci_declared','supplier','use_context','source_id','source_url','composition_status','coa_verified','regulatory_approved'])

observations=[]
def obs(grade,inci,key,lo='',hi='',unit='',qual='',source='',context='',applicability='',note=''):
    observations.append({'observation_id':f'OBS-{len(observations)+1:04d}','ingredient_id':iid(inci),'inci_candidate':inci,'grade_id':grade,'property_key':key,'value_min':lo,'value_max':hi,'unit':unit,'qualitative_value':qual,'test_conditions_or_scope':context,'applies_to':applicability,'source_id':source,'source_url':source_url.get(source,''),'evidence_status':'supplier_grade_reference','not_a_legal_limit':'true','note_vi':note})

for grade,inci,melt_min,melt_max,use_min,use_max,src in [
('S43-G-K8109','Cera Alba',61,66,1,20,'S43-KAHL-WAX'),
('S43-G-K2039L','Euphorbia Cerifera Cera',68,73,1,15,'S43-KAHL-WAX'),
('S43-G-K2442L','Copernicia Cerifera Cera',82,86,1,15,'S43-KAHL-2442L'),
('S43-G-K2811','Oryza Sativa Bran Cera',75,80,1,15,'S43-KAHL-PRODUCTS'),
('S43-G-K2178','Hydrogenated Castor Oil',85,88,1,10,'S43-KAHL-WAX'),
('S43-G-K8139','Cera Alba',62,65,1,20,'S43-KAHL-WAX')]:
    obs(grade,inci,'melting_point',melt_min,melt_max,'degC',source=src,context='Supplier catalog specification for named KAHL grade',applicability='material_grade',note='Không phải nhiệt độ gia công tối ưu và không tự động áp dụng cho các grade khác')
    obs(grade,inci,'recommended_use',use_min,use_max,'percent_w_w_as_supplied',source=src,context='Supplier recommended use range for named grade',applicability='formulation',note='Khoảng khuyến nghị không phải giới hạn pháp lý')

obs('S43-G-C1342','Acrylates/C10-30 Alkyl Acrylate Crosspolymer','recommended_use',0.1,1.0,'percent_w_w_as_supplied',source='S43-LUB-1342',context='Carbopol 1342 grade, as supplied',applicability='formulation',note='Không áp sang Carbomer hoặc polymer khác')
obs('S43-G-C1342','Acrylates/C10-30 Alkyl Acrylate Crosspolymer','functional_behavior',qual='Rheology modifier; thickener; suspending agent; improved electrolyte tolerance',source='S43-LUB-1342',context='aqueous systems and suspensions',applicability='formulation')
obs('S43-G-NATROSOL','Hydroxyethylcellulose','water_solubility',qual='water soluble, cold and hot water',source='S43-ASH-NATROSOL',context='Natrosol HEC grade family; no % solubility threshold provided',applicability='water_phase',note='Không suy ra nồng độ sử dụng tối đa')
obs('S43-G-NATROSOL','Hydroxyethylcellulose','polymer_class',qual='nonionic rheology modifier; shear thinning',source='S43-ASH-NATROSOL',context='Natrosol family only',applicability='formulation')
obs('S43-G-VCLC','Caprylyl Glycol','water_solubility',qual='very good water solubility for Velsan CLC supplier grade',source='S43-CLAR-VELSAN',context='Velsan CLC only, supplier description; no numeric solubility in source',applicability='aqueous;emulsion')
obs('S43-G-VCLC','Caprylyl Glycol','function',qual='preservation booster; moisturising; conditioning',source='S43-CLAR-VELSAN',context='Velsan CLC supplier product',applicability='formulation',note='Không thay thế challenge test')
obs('S43-G-NIP9010','Phenoxyethanol','pH_stability_max',hi=12,unit='pH',source='S43-CLAR-NIP',context='Clariant Nipaguard PE 9010 finished blend supplier description',applicability='preservative_blend',note='Không suy ra pH tối thiểu và không áp dụng cho Phenoxyethanol nguyên chất')
obs('S43-G-NIP9010','Phenoxyethanol','blend_identity',qual='Phenoxyethanol and Ethylhexylglycerin',source='S43-CLAR-NIP',context='Qualitative INCI only, unknown mass fractions',applicability='blend',note='Không phân rã định lượng do chưa có COA')
obs('S43-G-K4074','(KahlBase 4074 premix)','recommended_use',85,90,'percent_w_w_as_supplied',source='S43-KAHL-PRODUCTS',context='KahlBase 4074, a complete matte lipstick base; for lipstick formulas',applicability='lipstick',note='Không áp dụng cho son dưỡng môi nói chung hoặc cho jojoba oil riêng lẻ')
obs('S43-G-K4074','(KahlBase 4074 premix)','melting_point',67,73,'degC',source='S43-KAHL-PRODUCTS',context='Melting point of KahlBase 4074 premix (not individual Jojoba oil)',applicability='premix')
write_csv('scientific_property_observations_v43.csv',observations,list(observations[0].keys()))

components=[]
for g,names in [
('S43-G-NIP9010',['Phenoxyethanol','Ethylhexylglycerin']),
('S43-G-K4074',['Simmondsia Chinensis Seed Oil','Ricinus Communis Seed Oil','Rhus Verniciflua Peel Cera','Kaolin','Caprylic/Capric Triglyceride','Copernicia Cerifera Cera','Euphorbia Cerifera Cera','Helianthus Annuus Seed Cera','Tocopherol','Helianthus Annuus Seed Oil'])]:
    for pos,n in enumerate(names,1):
        components.append({'grade_id':g,'component_order':pos,'component_inci_candidate':n,'mass_fraction_min':'','mass_fraction_max':'','concentration_basis':'unknown','status':'qualitative_composition_only','must_not_allocate_mass':True,'supplier_source_id':'S43-CLAR-NIP' if g.endswith('NIP9010') else 'S43-KAHL-PRODUCTS'})
write_csv('grade_components_qualitative_v43.csv',components,list(components[0].keys()))

missing=[{'ingredient_id':k['ingredient_id'],'inci_candidate':k['inci_name_candidate'],'property_coverage_v42':k['property_status'],'target_priorities':'COA/TDS/grade, solubility, processing stability, pH scope; legal references','scientific_status':'no_new_grade_fact_for_this_inci' if k['inci_name_candidate'].lower() not in {o['inci_candidate'].lower() for o in observations} else 'supplier_grade_fact_available_not_generic','verification_required':'true'} for k in readcsv(DATA/'ingredient_properties.csv')]
write_csv('ingredient_evidence_coverage_v43.csv',missing,list(missing[0].keys()))

(DATA/'v43_build_summary.json').write_text(json.dumps({'inherited_master_inci':len(missing),'new_inci_candidates_not_in_master':['Oryza Sativa Bran Cera'],'supplier_grade_reference_count':len(grades),'property_observations':len(observations),'qualitative_premix_components':len(components),'evidence_model':'grade-specific; no global numeric ranges; no legal status inferred'},ensure_ascii=False,indent=2),encoding='utf8')
print((DATA/'v43_build_summary.json').read_text())
