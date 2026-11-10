"""HTTP MCP gateway, gated by a bearer token; use behind HTTPS or Secure MCP Tunnel.

Starts only if mcp extra is installed. Strict bearer auth is required even for listing tools.
"""
from __future__ import annotations
import os, secrets
from contextlib import asynccontextmanager
from starlette.responses import JSONResponse
from mcp_server import mcp
from workspace_db import initialize_database

@asynccontextmanager
async def lifespan(app):
    initialize_database()
    async with mcp.session_manager.run():
        yield

# Starlette's ASGI semantics allow auth before MCP session negotiation.
inner=mcp.streamable_http_app(json_response=True, stateless_http=True)

class BearerGate:
    def __init__(self, app):
        self.app=app
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            token=os.getenv('MCP_BEARER_TOKEN','')
            authorization=next((v.decode('latin1') for k,v in scope.get('headers',[]) if k.lower()==b'authorization'),'')
            expected=f'Bearer {token}'
            if not token:
                return await JSONResponse({'detail':'MCP_BEARER_TOKEN chưa được cấu hình'},status_code=503)(scope,receive,send)
            if not secrets.compare_digest(authorization,expected):
                return await JSONResponse({'detail':'Unauthorized'},status_code=401,headers={'WWW-Authenticate':'Bearer'})(scope,receive,send)
        return await self.app(scope,receive,send)

# SDK streamable_http_app generally handles the /mcp path itself.
# Wrap lifespan through a Starlette instance so that session manager is started.
from starlette.applications import Starlette
app=Starlette(lifespan=lifespan)
app.mount('/',BearerGate(inner))
