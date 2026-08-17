import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.usuario_schema import (
    ComercianteRegistroCreate, 
    ComercianteRegistroResponse,
    LoginRequest,
    LoginResponse,
    ComerciantePerfilUpdate,
    RecuperarPasswordRequest,
    RestablecerPasswordRequest
)
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user_id
)
from app.core.email_service import enviar_correo_recuperacion
from app.db.supabase_client import supabase

router = APIRouter(prefix="/auth", tags=["Gestión de Identidad (Sprint 1)"])

@router.post("/registro", response_model=ComercianteRegistroResponse, status_code=status.HTTP_201_CREATED)
def registrar_comerciante(datos: ComercianteRegistroCreate):
    email_check = supabase.table("comerciantes").select("id").eq("email", datos.email).execute()
    if email_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ingresado ya se encuentra registrado en SVC."
        )

    cuit_check = supabase.table("comerciantes").select("id").eq("cuit_cuil", datos.cuit_cuil).execute()
    if cuit_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El CUIT/CUIL ingresado ya se encuentra registrado en SVC."
        )

    alcances_validos = ["Regional", "Nacional", "Internacional"]
    if datos.zona_alcance_logistico not in alcances_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zona de alcance logístico no válida."
        )

    hashed_pwd = get_password_hash(datos.password)

    nuevo_comerciante = {
        "email": datos.email,
        "password_hash": hashed_pwd,
        "nombre_razon_social": datos.nombre_razon_social,
        "cuit_cuil": datos.cuit_cuil,
        "telefono": datos.telefono,
        "rubro_comercial": datos.rubro_comercial,
        "subrubro_comercial": datos.subrubro_comercial,
        "rubros_interes": [datos.rubro_comercial, datos.subrubro_comercial],
        "direccion": datos.direccion,
        "pais": datos.pais,
        "provincia": datos.provincia,
        "ciudad_localidad": datos.ciudad_localidad,
        "zona_alcance_logistico": datos.zona_alcance_logistico,
        "rol": "comerciante",
        "estado": "activo"
    }

    resultado = supabase.table("comerciantes").insert(nuevo_comerciante).execute()
    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar la cuenta comercial en la base de datos."
        )

    return resultado.data[0]

@router.post("/login", response_model=LoginResponse)
def iniciar_sesion(datos: LoginRequest):
    res = supabase.table("comerciantes").select("*").eq("email", datos.email).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas."
        )

    usuario = res.data[0]

    if usuario.get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta se encuentra inhabilitada o suspendida por la administración."
        )

    if not verify_password(datos.password, usuario["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas."
        )

    token = create_access_token({
        "sub": usuario["id"],
        "email": usuario["email"],
        "rol": usuario["rol"]
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario
    }

@router.get("/me", response_model=ComercianteRegistroResponse)
def obtener_perfil_actual(user_id: str = Depends(get_current_user_id)):
    res = supabase.table("comerciantes").select("*").eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return res.data[0]

@router.put("/perfil", response_model=ComercianteRegistroResponse)
def modificar_perfil(datos: ComerciantePerfilUpdate, user_id: str = Depends(get_current_user_id)):
    alcances_validos = ["Regional", "Nacional", "Internacional"]
    if datos.zona_alcance_logistico not in alcances_validos:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zona de alcance no válida.")

    actualizacion = {
        "nombre_razon_social": datos.nombre_razon_social,
        "telefono": datos.telefono,
        "rubro_comercial": datos.rubro_comercial,
        "subrubro_comercial": datos.subrubro_comercial,
        "rubros_interes": [datos.rubro_comercial, datos.subrubro_comercial],
        "direccion": datos.direccion,
        "provincia": datos.provincia,
        "ciudad_localidad": datos.ciudad_localidad,
        "zona_alcance_logistico": datos.zona_alcance_logistico,
        "actualizado_el": "now()"
    }

    res = supabase.table("comerciantes").update(actualizacion).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo actualizar el perfil.")

    return res.data[0]

@router.post("/logout")
def cerrar_sesion(user_id: str = Depends(get_current_user_id)):
    return {"mensaje": "Sesión finalizada correctamente.", "estado": "logout_success"}

# ── CdU03: Recuperar Contraseña de Acceso ──────────────────────────────
@router.post("/solicitar-recuperacion")
def solicitar_recuperacion_password(datos: RecuperarPasswordRequest):
    # 1. Validar que el correo pertenezca a un comerciante activo en Supabase
    user_res = supabase.table("comerciantes").select("id, email, estado").eq("email", datos.email).execute()
    if not user_res.data or user_res.data[0]["estado"] != "activo":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El correo ingresado no pertenece a ninguna cuenta activa de SVC."
        )

    # 2. Generar token único con expiración estricta de 30 minutos (ERS Secc. 4.4 CdU03)
    token_str = secrets.token_urlsafe(32)
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=30)

    registro_token = {
        "email": datos.email,
        "token": token_str,
        "expiracion": expiracion.isoformat(),
        "usado": False
    }

    token_res = supabase.table("tokens_recuperacion").insert(registro_token).execute()
    if not token_res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar el token de recuperación en la base de datos."
        )

    # 3. Despacho SMTP
    try:
        enviar_correo_recuperacion(datos.email, token_str)
    except Exception as e:
        supabase.table("tokens_recuperacion").delete().eq("token", token_str).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo en el servidor SMTP al despachar el correo: {str(e)}"
        )

    return {
        "mensaje": "Se ha enviado un enlace de recuperación a su casilla de correo electrónico.",
        "estado": "email_sent_success"
    }

@router.post("/restablecer-password")
def restablecer_password(datos: RestablecerPasswordRequest):
    # 1. Validar token existente y no usado
    token_query = supabase.table("tokens_recuperacion").select("*").eq("token", datos.token).eq("usado", False).execute()
    if not token_query.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación es inválido o ya ha sido utilizado."
        )

    token_record = token_query.data[0]
    expiracion_dt = datetime.fromisoformat(token_record["expiracion"].replace("Z", "+00:00"))

    # 2. Validar ventana de expiración de 30 minutos
    if datetime.now(timezone.utc) > expiracion_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación ha expirado (límite: 30 minutos). Solicite uno nuevo."
        )

    # 3. Cifrar la nueva contraseña con bcrypt nativo
    nuevo_hash = get_password_hash(datos.nueva_password)

    # 4. Actualizar contraseña del comerciante
    update_res = supabase.table("comerciantes").update({
        "password_hash": nuevo_hash,
        "actualizado_el": "now()"
    }).eq("email", token_record["email"]).execute()

    if not update_res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la contraseña en la base de datos."
        )

    # 5. Invalidar el token utilizado
    supabase.table("tokens_recuperacion").update({"usado": True}).eq("id", token_record["id"]).execute()

    return {
        "mensaje": "Contraseña restablecida exitosamente. Ya puede iniciar sesión con su nueva clave.",
        "estado": "password_reset_success"
    }