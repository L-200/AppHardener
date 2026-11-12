"""Ponto de entrada FastAPI do AppHardener (Módulo P1 - Backend e Dados)."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.config import HOST, PORT
from backend.database import init_db
from backend.routers import apps, findings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Inicializa o schema SQLite na inicialização da aplicação."""
    init_db()
    yield


app = FastAPI(
    title="AppHardener API",
    description="API local de diagnóstico de segurança e hardening de aplicações web.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Adiciona cabeçalhos de segurança defensivos em todas as respostas da API."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Verifica a disponibilidade da API."""
    return {"status": "ok"}


app.include_router(apps.router)
app.include_router(findings.router)


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)
