"""One development application: professional editor and Python core share an origin.

The historical FRAME Pages beta remains untouched; this server is an isolated
integration candidate. It requires a real backend host before any public rollout.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from .api import app as core_api

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title='FRAME Unified Development Studio', version='integration-0.1')
app.mount('/api', core_api)

@app.get('/', include_in_schema=False)
def editor():
    return FileResponse(ROOT/'web'/'index.html', media_type='text/html')

@app.get('/core-bridge.js', include_in_schema=False)
def bridge():
    return FileResponse(ROOT/'web'/'core-bridge.js', media_type='application/javascript')

@app.get('/favicon.ico', include_in_schema=False)
def icon():
    from fastapi.responses import Response
    return Response(status_code=204)
