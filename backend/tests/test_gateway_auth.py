"""ASGI bearer gate unit test with a fake MCP app (not a real protocol handshake)."""
import importlib,sys,types
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


def test_gateway_requires_token(monkeypatch):
    class DummyManager:
        @asynccontextmanager
        async def run(self):
            yield
    class FakeServer:
        session_manager=DummyManager()
        def streamable_http_app(self,**kwargs):
            async def endpoint(request):return JSONResponse({'ok':True})
            return Starlette(routes=[Route('/mcp',endpoint)])
    fake=types.ModuleType('mcp_server');fake.mcp=FakeServer()
    monkeypatch.setitem(sys.modules,'mcp_server',fake)
    sys.modules.pop('mcp_gateway',None)
    module=importlib.import_module('mcp_gateway')
    monkeypatch.delenv('MCP_BEARER_TOKEN',raising=False)
    with TestClient(module.app) as client:
        assert client.get('/mcp').status_code==503
        monkeypatch.setenv('MCP_BEARER_TOKEN','private-token')
        assert client.get('/mcp').status_code==401
        assert client.get('/mcp',headers={'Authorization':'Bearer private-token'}).json()=={'ok':True}
    sys.modules.pop('mcp_gateway',None)
