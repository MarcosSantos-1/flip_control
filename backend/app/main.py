"""Aplicação FastAPI principal."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import sacs, cnc, acic, upload, indicadores, roteiros

app = FastAPI(
    title="ADC/FLIP API",
    description="API para sistema de controle ADC/FLIP - Limpebras Lote III",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])
app.include_router(sacs.router, prefix=settings.API_V1_PREFIX, tags=["sacs"])
app.include_router(cnc.router, prefix=settings.API_V1_PREFIX, tags=["cnc"])
app.include_router(acic.router, prefix=settings.API_V1_PREFIX, tags=["acic"])
app.include_router(indicadores.router, prefix=settings.API_V1_PREFIX, tags=["indicadores"])
app.include_router(roteiros.router, prefix=settings.API_V1_PREFIX, tags=["roteiros"])


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "ADC/FLIP API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}

