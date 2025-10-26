from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
 
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
 
# Security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
        
    resp.headers["Content-Security-Policy"] = (
      "default-src 'self'; frame-ancestors 'none'; object-src 'none'; "
      "base-uri 'self'; img-src 'self' data:; script-src 'self'; style-src 'self';"
    )
    return resp

#  in-memory rate-limit
WINDOW = 10       # сек
MAX_REQ = 50      # запросов на IP за окно
_buckets = defaultdict(list)

class RateLimitMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next):
    now = time.time()
    ip = request.client.host if request.client else "unknown"
    q = _buckets[ip]

    while q and q[0] <= now - WINDOW:
      q.pop(0)
      if len(q) >= MAX_REQ:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    q.append(now)
    return await call_next(request)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: str = ""):
    # намеренно простая страница, отражающая ввод
    # (для DAST это даст находки типа отражений/хедеров)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "q": q}
    )

@app.get("/healthz")
def healthz():
    return PlainTextResponse("OK")

@app.get("/echo", response_class=HTMLResponse)
def echo(x: str = ""):
    # намеренно без экранирования - упрощённая цель для ZAP
    return HTMLResponse(f"<h1>ECHO</h1><div>you said: {x}</div>")
