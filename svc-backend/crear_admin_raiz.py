"""
Script de Inicialización del Administrador Raíz de SVC (CdU02 / CdU05).
Genera el hash bcrypt nativo y persiste la cuenta en Supabase.
"""
import os
from dotenv import load_dotenv
from app.core.security import get_password_hash
from app.db.supabase_client import supabase

load_dotenv()

EMAIL_ADMIN = "svc.team.oficial@gmail.com"
PASSWORD_PLANA = "Admin1234!"
NOMBRE_COMPLETO = "Administrador Principal SVC"

def sembrar_admin_raiz():
    print(f"[*] Generando hash bcrypt nativo para '{EMAIL_ADMIN}'...")
    pwd_hash = get_password_hash(PASSWORD_PLANA)
    
    # 1. Verificar si ya existe en Supabase
    check_res = supabase.table("administradores").select("id").eq("email", EMAIL_ADMIN).execute()
    
    admin_data = {
        "email": EMAIL_ADMIN,
        "password_hash": pwd_hash,
        "nombre_completo": NOMBRE_COMPLETO,
        "rol": "administrador",
        "estado": "activo"
    }

    if check_res.data:
        # Actualizar hash existente
        admin_id = check_res.data[0]["id"]
        res = supabase.table("administradores").update(admin_data).eq("id", admin_id).execute()
        print(f"[+] Contraseña y hash actualizados exitosamente para el Administrador Raíz (ID: {admin_id}).")
    else:
        # Insertar nuevo registro
        res = supabase.table("administradores").insert(admin_data).execute()
        print(f"[+] Administrador Raíz creado exitosamente en Supabase (ID: {res.data[0]['id']}).")

    print("\n--- CREDENCIALES ADMINISTRATIVAS OFICIALES ---")
    print(f"URL: login.html (Apartado Acceso Corporativo)")
    print(f"Usuario: {EMAIL_ADMIN}")
    print(f"Contraseña: {PASSWORD_PLANA}")
    print("----------------------------------------------\n")

if __name__ == "__main__":
    sembrar_admin_raiz()