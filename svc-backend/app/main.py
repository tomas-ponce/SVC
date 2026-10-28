from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth,
    admin,
    inventario,
    busqueda,
    publicaciones,
    comunidades,
    chat,
    integraciones,
    transacciones,
    calificaciones
)

app = FastAPI(
    title="SVC — Sistema de Vinculación para el Comercio (Backend API)",
    description="API RESTful oficial para la plataforma SaaS B2B SVC.",
    version="0.6.2"
)

# Configuración de CORS robusta para desarrollo local y file:///
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de Routers Modulares
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(inventario.router)
app.include_router(busqueda.router)
app.include_router(publicaciones.router)
app.include_router(comunidades.router)
app.include_router(chat.router)
app.include_router(integraciones.router)
app.include_router(transacciones.router)
app.include_router(calificaciones.router)

@app.get("/", tags=["Diagnóstico y Salud"])
def root():
    return {
        "sistema": "SVC — Sistema de Vinculación para el Comercio",
        "version": "0.6.2",
        "sprint": "Sprint 6 (WPT-06: Checkout & WPT-07: Reputación y Reseñas B2B)",
        "estado": "Operativo"
    }
