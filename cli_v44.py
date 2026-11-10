"""Usage: python cli_v44.py examples/lip_balm_optimizer_v44.json [--compare]"""
from argparse import ArgumentParser
from pathlib import Path
import json
from optimizer_v44 import solve_scenario,solve_claim_alternatives
from formula_group_service import Catalog

def main():
    p=ArgumentParser();p.add_argument('input');p.add_argument('--compare',action='store_true');p.add_argument('--out')
    a=p.parse_args();data=json.loads(Path(a.input).read_text(encoding='utf-8'))
    catalog=Catalog() if data.get('product_id') is not None else None
    result=(solve_claim_alternatives(data,catalog) if a.compare else solve_scenario(data,catalog))
    txt=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.out:Path(a.out).write_text(txt,encoding='utf-8')
    else:print(txt)
if __name__=='__main__':main()
