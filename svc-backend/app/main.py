from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, admin, inventario, busqueda, publicaciones, comunidades, chat

app = FastAPI(
    title="SVC — Sistema de Vinculación para el Comercio (Backend API)",
    description="API RESTful oficial para la plataforma SaaS B2B SVC.",
    version="0.5.0"
)

# Configuración de CORS robusta para desarrollo local y file:///
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # En "*" allow_credentials debe ser False para que los navegadores no rechacen el header
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

@app.get("/", tags=["Diagnóstico y Salud"])
def root():
    return {
        "sistema": "SVC — Sistema de Vinculación para el Comercio",
        "version": "0.5.0",
        "sprint": "Sprint 5 (WPT-04: Central de Negociación y Notificaciones)",
        "estado": "Operativo"
    }