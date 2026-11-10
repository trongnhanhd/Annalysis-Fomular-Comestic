"""Exercise MCP tool business logic with a stub server when mcp 2.x is unavailable locally.
This is NOT a transport handshake test and must not be represented as one.
"""
import importlib, sys, types
from pathlib import Path


def test_mcp_tools_use_preserved_engine(monkeypatch):
    fake = types.ModuleType('mcp')
    server = types.ModuleType('mcp.server')
    class MCPServer:
        def __init__(self, name): self.name=name
        def tool(self): return lambda fn:fn
    server.MCPServer=MCPServer
    monkeypatch.setitem(sys.modules,'mcp', fake)
    monkeypatch.setitem(sys.modules,'mcp.server', server)
    sys.modules.pop('mcp_server',None)
    m=importlib.import_module('mcp_server')
    r=m.analyze_inci('Aqua, Niacinamide',market='EU')
    assert r['status']=='feasible'
    ni=next(x for x in r['results'] if x['ingredient']=='Niacinamide')
    assert ni['estimated_pct'] is None
    assert m.compare_regulatory_references('Niacinamide',market='CN')['coverage']=='partial'
    r2=m.analyze_confirmed_ingredient_percentage('Aqua, Niacinamide','Niacinamide',5,'Tài liệu được xác minh', 'EU')
    assert next(x for x in r2['results'] if x['ingredient']=='Niacinamide')['min_pct']==5
    sys.modules.pop('mcp_server',None)
