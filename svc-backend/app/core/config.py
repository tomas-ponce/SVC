import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "SVC - Sistema de Vinculación para el Comercio"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Servidor y JWT
    PORT: int = int(os.getenv("PORT", 8000))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "svc_clave_secreta_desarrollo_seminario_2026_x987123")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))
    
    # Credenciales de Supabase (SaaS / BaaS)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Instanciación explícita exportada hacia app/main.py y app/db/supabase_client.py
settings = Settings()