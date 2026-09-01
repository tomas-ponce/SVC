from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, admin, inventario

app = FastAPI(
    title="SVC — Sistema de Vinculación para el Comercio (Backend API)",
    description="API RESTful oficial para la plataforma SaaS B2B SVC.",
    version="0.2.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de Routers Modulares
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(inventario.router)

@app.get("/", tags=["Diagnóstico y Salud"])
def root():
    return {
        "sistema": "SVC — Sistema de Vinculación para el Comercio",
        "version": "0.2.0",
        "sprint": "Sprint 2 (WPT-02)",
        "estado": "Operativo"
    }