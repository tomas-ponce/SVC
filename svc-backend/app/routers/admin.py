import math
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.schemas.usuario_schema import (
    AdminRegistroCreate, 
    AdminRegistroResponse,
    InhabilitarCuentaRequest,
    PaginacionUsuariosResponse
)
from app.core.security import (
    get_password_hash, 
    get_current_admin
)
from app.core.email_service import (
    enviar_correo_bienvenida_admin,
    enviar_correo_inhabilitacion_comerciante,
    enviar_correo_inhabilitacion_admin,
    enviar_correo_reactivacion_comerciante,
    enviar_correo_reactivacion_admin
)
from app.db.supabase_client import supabase

router = APIRouter(prefix="/admin", tags=["Módulo de Administración Global (Sprint 1)"])

# ==============================================================================
# 1. CdU08 - LISTADO DE COMERCIANTES PAGINADO
# ==============================================================================
@router.get(
    "/usuarios", 
    response_model=PaginacionUsuariosResponse,
    summary="Listado general paginado de comerciantes con filtros (CdU08)"
)
def listar_comerciantes(
    pagina: int = Query(1, ge=1),
    limite: int = Query(8, ge=1, le=50),
    estado: Optional[str] = Query(None),
    rubro: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None),
    admin_actual: dict = Depends(get_current_admin)
):
    offset = (pagina - 1) * limite
    query = supabase.table("comerciantes").select("*", count="exact")

    if estado and estado.strip():
        query = query.eq("estado", estado.strip())
    if rubro and rubro.strip():
        query = query.eq("rubro_comercial", rubro.strip())
    if busqueda and busqueda.strip():
        termino = f"%{busqueda.strip()}%"
        query = query.or_(f"nombre_razon_social.ilike.{termino},cuit_cuil.ilike.{termino},email.ilike.{termino}")

    res = query.order("creado_el", desc=True).range(offset, offset + limite - 1).execute()
    total_registros = res.count if res.count is not None else len(res.data)
    total_paginas = math.ceil(total_registros / limite) if total_registros > 0 else 1

    return {
        "total": total_registros,
        "pagina": pagina,
        "limite": limite,
        "total_paginas": total_paginas,
        "usuarios": res.data
    }

# ==============================================================================
# 2. CdU08 - LISTADO DE ADMINISTRADORES
# ==============================================================================
@router.get(
    "/administradores", 
    summary="Listado de administradores registrados (CdU08)"
)
def listar_administradores(admin_actual: dict = Depends(get_current_admin)):
    res = supabase.table("administradores").select("id, email, nombre_completo, rol, estado, creado_el").order("creado_el", desc=True).execute()
    return {"administradores": res.data}

# ==============================================================================
# 3. CdU07 - INHABILITAR COMERCIANTE CON NOTIFICACIÓN ESPECÍFICA
# ==============================================================================
@router.put(
    "/usuarios/{usuario_id}/inhabilitar",
    summary="Inhabilitar cuenta de comerciante (CdU07)"
)
def inhabilitar_cuenta_comerciante(
    usuario_id: str,
    datos: InhabilitarCuentaRequest,
    admin_actual: dict = Depends(get_current_admin)
):
    user_res = supabase.table("comerciantes").select("*").eq("id", usuario_id).execute()
    if not user_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comerciante no encontrado.")

    usuario = user_res.data[0]
    if usuario.get("estado") == "inhabilitado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta ya está inhabilitada.")

    update_res = supabase.table("comerciantes").update({
        "estado": "inhabilitado",
        "actualizado_el": "now()"
    }).eq("id", usuario_id).execute()

    if not update_res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al inhabilitar comerciante.")

    log_data = {
        "administrador_id": admin_actual["id"],
        "accion": "INHABILITAR_COMERCIANTE",
        "entidad_afectada": "comerciantes",
        "entidad_id": usuario_id,
        "justificacion": datos.motivo_justificacion.strip()
    }
    supabase.table("logs_auditoria").insert(log_data).execute()

    try:
        enviar_correo_inhabilitacion_comerciante(
            destinatario=usuario["email"],
            razon_social=usuario["nombre_razon_social"],
            motivo=datos.motivo_justificacion.strip()
        )
    except Exception as e:
        print(f"Aviso: Fallo envio SMTP inhabilitacion comerciante: {str(e)}")

    return {"mensaje": f"Cuenta de '{usuario['nombre_razon_social']}' inhabilitada.", "estado": "cuenta_inhabilitada_success"}

# ==============================================================================
# 4. CdU07 - INHABILITAR ADMINISTRADOR CON NOTIFICACIÓN ESPECÍFICA
# ==============================================================================
@router.put(
    "/administradores/{admin_id}/inhabilitar",
    summary="Inhabilitar cuenta de administrador (CdU07)"
)
def inhabilitar_cuenta_administrador(
    admin_id: str,
    datos: InhabilitarCuentaRequest,
    admin_actual: dict = Depends(get_current_admin)
):
    if admin_id == admin_actual["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Operación inválida: No puede inhabilitar su propia cuenta en sesión."
        )

    adm_res = supabase.table("administradores").select("*").eq("id", admin_id).execute()
    if not adm_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrador no encontrado.")

    admin_target = adm_res.data[0]
    if admin_target["email"] == "svc.team.oficial@gmail.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operación denegada: La cuenta del Administrador Raíz Principal no puede ser suspendida."
        )

    if admin_target.get("estado") == "inhabilitado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El administrador ya está inhabilitado.")

    update_res = supabase.table("administradores").update({
        "estado": "inhabilitado",
        "actualizado_el": "now()"
    }).eq("id", admin_id).execute()

    if not update_res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al inhabilitar administrador.")

    log_data = {
        "administrador_id": admin_actual["id"],
        "accion": "INHABILITAR_ADMINISTRADOR",
        "entidad_afectada": "administradores",
        "entidad_id": admin_id,
        "justificacion": datos.motivo_justificacion.strip()
    }
    supabase.table("logs_auditoria").insert(log_data).execute()

    try:
        enviar_correo_inhabilitacion_admin(
            destinatario=admin_target["email"],
            nombre_completo=admin_target["nombre_completo"],
            motivo=datos.motivo_justificacion.strip()
        )
    except Exception as e:
        print(f"Aviso: Fallo envio SMTP inhabilitacion admin: {str(e)}")

    return {"mensaje": f"El administrador '{admin_target['nombre_completo']}' ha sido inhabilitado.", "estado": "admin_inhabilitado_success"}

# ==============================================================================
# 5. REACTIVAR COMERCIANTE CON NOTIFICACIÓN ESPECÍFICA
# ==============================================================================
@router.put(
    "/usuarios/{usuario_id}/reactivar",
    summary="Reactivar cuenta de comerciante y notificar por correo"
)
def reactivar_cuenta_comerciante(
    usuario_id: str,
    admin_actual: dict = Depends(get_current_admin)
):
    user_res = supabase.table("comerciantes").select("*").eq("id", usuario_id).execute()
    if not user_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    usuario = user_res.data[0]
    if usuario.get("estado") != "inhabilitado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta no se encuentra inhabilitada.")

    update_res = supabase.table("comerciantes").update({
        "estado": "activo",
        "actualizado_el": "now()"
    }).eq("id", usuario_id).execute()

    if not update_res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al reactivar cuenta.")

    log_data = {
        "administrador_id": admin_actual["id"],
        "accion": "REACTIVAR_COMERCIANTE",
        "entidad_afectada": "comerciantes",
        "entidad_id": usuario_id,
        "justificacion": f"Reactivación dispuesta por {admin_actual['email']}"
    }
    supabase.table("logs_auditoria").insert(log_data).execute()

    try:
        enviar_correo_reactivacion_comerciante(
            destinatario=usuario["email"],
            razon_social=usuario["nombre_razon_social"]
        )
    except Exception as e:
        print(f"Aviso: Fallo envio SMTP reactivacion comerciante: {str(e)}")

    return {"mensaje": f"La cuenta de '{usuario['nombre_razon_social']}' ha sido reactivada.", "estado": "cuenta_reactivada_success"}

# ==============================================================================
# 6. REACTIVAR ADMINISTRADOR CON NOTIFICACIÓN ESPECÍFICA
# ==============================================================================
@router.put(
    "/administradores/{admin_id}/reactivar",
    summary="Reactivar cuenta de administrador y notificar por correo"
)
def reactivar_cuenta_administrador(
    admin_id: str,
    admin_actual: dict = Depends(get_current_admin)
):
    adm_res = supabase.table("administradores").select("*").eq("id", admin_id).execute()
    if not adm_res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrador no encontrado.")

    admin_target = adm_res.data[0]
    if admin_target.get("estado") != "inhabilitado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El administrador no está inhabilitado.")

    update_res = supabase.table("administradores").update({
        "estado": "activo",
        "actualizado_el": "now()"
    }).eq("id", admin_id).execute()

    if not update_res.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al reactivar administrador.")

    log_data = {
        "administrador_id": admin_actual["id"],
        "accion": "REACTIVAR_ADMINISTRADOR",
        "entidad_afectada": "administradores",
        "entidad_id": admin_id,
        "justificacion": f"Reactivación administrativa por {admin_actual['email']}"
    }
    supabase.table("logs_auditoria").insert(log_data).execute()

    try:
        enviar_correo_reactivacion_admin(
            destinatario=admin_target["email"],
            nombre_completo=admin_target["nombre_completo"]
        )
    except Exception as e:
        print(f"Aviso: Fallo envio SMTP reactivacion admin: {str(e)}")

    return {"mensaje": f"El administrador '{admin_target['nombre_completo']}' ha sido reactivado.", "estado": "admin_reactivado_success"}

# ==============================================================================
# 7. CdU05 - REGISTRAR NUEVO ADMINISTRADOR
# ==============================================================================
@router.post(
    "/usuarios/administrador", 
    response_model=AdminRegistroResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo gestor con rol Administrador (CdU05)"
)
def registrar_nuevo_administrador(
    datos: AdminRegistroCreate, 
    admin_actual: dict = Depends(get_current_admin)
):
    adm_check = supabase.table("administradores").select("id").eq("email", datos.email).execute()
    if adm_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya pertenece a una cuenta administrativa registrada."
        )

    com_check = supabase.table("comerciantes").select("id").eq("email", datos.email).neq("estado", "baja").execute()
    if com_check.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ingresado ya se encuentra en uso por un perfil comercial activo."
        )

    hashed_pwd = get_password_hash(datos.password_provisoria)

    nuevo_admin = {
        "email": datos.email,
        "password_hash": hashed_pwd,
        "nombre_completo": datos.nombre_completo,
        "rol": "administrador",
        "estado": "activo"
    }

    resultado = supabase.table("administradores").insert(nuevo_admin).execute()
    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al persistir la cuenta administrativa en la base de datos."
        )

    admin_creado = resultado.data[0]

    log_data = {
        "administrador_id": admin_actual["id"],
        "accion": "ALTA_ADMINISTRADOR",
        "entidad_afectada": "administradores",
        "entidad_id": admin_creado["id"],
        "justificacion": f"Alta otorgada por el administrador {admin_actual['email']}"
    }
    supabase.table("logs_auditoria").insert(log_data).execute()

    try:
        enviar_correo_bienvenida_admin(datos.email, datos.nombre_completo, datos.password_provisoria)
    except Exception as e:
        print(f"Aviso: Fallo envio SMTP bienvenida admin: {str(e)}")

    return admin_creado