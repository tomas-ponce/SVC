from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, admin

app = FastAPI(
    title="SVC - Sistema de Vinculación para el Comercio",
    description="API Backend transaccional B2B (Seminario de Integración Profesional 2026)",
    version="1.0.0"
)

# Configuración de CORS para desarrollo local y producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro modular de routers
app.include_router(auth.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "sistema": "Sistema de Vinculación para el Comercio (SVC)",
        "estado": "En línea",
        "entorno": "Desarrollo Local / AWS ASP",
        "version": "1.0.0"
    }