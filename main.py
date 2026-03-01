from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analyze, portfolio, assets, auth, export

app = FastAPI(
    title="Inverso API",
    description="Backend de análisis de activos financieros con IA para el mercado argentino",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción reemplazar con tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/auth",      tags=["Autenticación"])
app.include_router(assets.router,    prefix="/assets",    tags=["Activos"])
app.include_router(analyze.router,   prefix="/analyze",   tags=["Análisis"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["Simulador"])
app.include_router(export.router,    prefix="/export",    tags=["Exportación"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Inverso API v1.0 funcionando"}

@app.get("/health")
def health():
    return {"status": "healthy"}
