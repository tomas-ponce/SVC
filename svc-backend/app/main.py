from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(
    title="SVC - Sistema de Vinculación para el Comercio",
    description="API RESTful Backend para la plataforma B2B de vinculación comercial.",
    version="1.0.0"
)

# Configuración CORS para habilitar peticiones desde el cliente frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión del router del Sprint 1
app.include_router(auth.router)

@app.get("/", tags=["Estado del Sistema"])
def read_root():
    return {
        "estado": "operativo",
        "sistema": "Sistema de Vinculación para el Comercio (SVC)",
        "modelo": "ASP (SaaS)",
        "version": "1.0.0"
    }