"""CLI V4.5: demo DoE and open study (no lab measurements are invented)."""
import argparse,json
from formula_group_service import Catalog
from experimental_validation_v45 import build_doe
from experimental_repository_v45 import Repository

parser=argparse.ArgumentParser(description='Formula Intelligence V4.5')
parser.add_argument('mode',choices=['doe','new-study','report'])
parser.add_argument('path_or_study_id')
parser.add_argument('--db',default=None)
a=parser.parse_args()
if a.mode=='doe':
    body=json.load(open(a.path_or_study_id,encoding='utf8'))
    out=build_doe(body,Catalog() if body['scenario'].get('product_id') else None)
elif a.mode=='new-study':out=Repository(a.db).create_study(json.load(open(a.path_or_study_id,encoding='utf8')))
else:out=Repository(a.db).report(a.path_or_study_id)
print(json.dumps(out,ensure_ascii=False,indent=2))
