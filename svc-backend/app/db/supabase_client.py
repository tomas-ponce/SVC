import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Las credenciales de Supabase no están correctamente configuradas en el archivo .env")

# Instanciación del cliente de Supabase para operaciones del backend
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)