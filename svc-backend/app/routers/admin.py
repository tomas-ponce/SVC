from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from app.core.security import get_current_user_id, get_password_hash
from app.core.email_service import (
    enviar_correo_bienvenida_admin,
    enviar_correo_inhabilitacion_comerciante,
    enviar_correo_inhabilitacion_admin,
    enviar_correo_reactivacion_comerciante,
    enviar_correo_reactivacion_admin
)
from app.db.supabase_client import supabase

router = APIRouter(prefix="/admin", tags=["Módulo de Administración y Auditoría (Sprint 1 / CdU05, CdU07, CdU08)"])

# ==============================================================================
# ESQUEMAS PYDANTIC ADMINISTRATIVOS
# ==============================================================================

class AdminRegistroInput(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=150, description="Nombre y apellido del nuevo administrador")
    email: EmailStr = Field(..., description="Correo electrónico institucional")
    password_provisoria: str = Field(..., min_length=8, description="Contraseña provisoria de acceso")

class InhabilitarUsuarioInput(BaseModel):
    tipo_usuario: str = Field(..., pattern="^(comerciante|administrador)$", description="Tipo de cuenta a sancionar")
    motivo_inhabilitacion: str = Field(..., min_length=5, max_length=500, description="Justificación obligatoria de la medida")

class ReactivarUsuarioInput(BaseModel):
    tipo_usuario: str = Field(..., pattern="^(comerciante|administrador)$")
    motivo_reactivacion: Optional[str] = Field(None, max_length=500)

# ==============================================================================
# VALIDACIÓN DE SEGURIDAD Y CONTROL DE ACCESO BASADO EN ROLES (RBAC)
# ==============================================================================
def verificar_admin_activo(admin_id: str) -> dict:
    res = supabase.table("administradores").select("*").eq("id", admin_id).execute()
    if not res.data or res.data[0].get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren privilegios de Administrador activo en SVC."
        )
    return res.data[0]

# ==============================================================================
# 1. CdU08 - CONSULTAR LISTADO GENERAL DE USUARIOS (COMERCIANTES Y ADMINS)
# ==============================================================================
@router.get(
    "/usuarios",
    summary="Listado general y auditoría de comerciantes y administradores (CdU08)"
)
def listar_usuarios(
    tipo: Optional[str] = "comerciante",
    busqueda: Optional[str] = None,
    estado: Optional[str] = None,
    rubro: Optional[str] = None,
    admin_id: str = Depends(get_current_user_id)
):
    verificar_admin_activo(admin_id)

    if tipo == "administrador":
        query = supabase.table("administradores").select("id, nombre_completo, email, rol, estado, creado_el").order("creado_el", desc=True)
        res = query.execute()
        usuarios = res.data or []
        
        if busqueda:
            b = busqueda.lower().strip()
            usuarios = [u for u in usuarios if b in u.get("nombre_completo", "").lower() or b in u.get("email", "").lower()]
        if estado and estado != "todos":
            usuarios = [u for u in usuarios if u.get("estado", "").lower() == estado.lower()]
            
        return {"total": len(usuarios), "usuarios": usuarios}
    else:
        query = supabase.table("comerciantes").select(
            "id, nombre_razon_social, cuit_cuil, rubro_comercial, subrubro_comercial, direccion, provincia, ciudad_localidad, telefono, email, estado, creado_el"
        ).order("creado_el", desc=True)
        res = query.execute()
        usuarios = res.data or []
        
        if busqueda:
            b = busqueda.lower().strip()
            usuarios = [
                u for u in usuarios 
                if b in u.get("nombre_razon_social", "").lower() 
                or b in u.get("email", "").lower() 
                or b in u.get("cuit_cuil", "").lower()
            ]
        if estado and estado != "todos":
            usuarios = [u for u in usuarios if u.get("estado", "").lower() == estado.lower()]
        if rubro and rubro != "todos":
            usuarios = [u for u in usuarios if u.get("rubro_comercial", "").lower() == rubro.lower()]
            
        return {"total": len(usuarios), "usuarios": usuarios}

# ==============================================================================
# 2. CdU05 - REGISTRAR NUEVO ADMINISTRADOR
# ==============================================================================
@router.post(
    "/nuevo-administrador",
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta a un nuevo miembro del equipo de administración (CdU05)"
)
def registrar_nuevo_administrador(
    datos: AdminRegistroInput,
    admin_id: str = Depends(get_current_user_id)
):
    admin_ejecutor = verificar_admin_activo(admin_id)
    email_clean = datos.email.lower().strip()

    # Validar unicidad del correo electrónico
    if supabase.table("administradores").select("id").eq("email", email_clean).execute().data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ingresado ya se encuentra registrado en el equipo de administración."
        )

    if supabase.table("comerciantes").select("id").eq("email", email_clean).neq("estado", "baja").execute().data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ingresado pertenece a un comerciante registrado."
        )

    nuevo_admin = {
        "nombre_completo": datos.nombre_completo.strip(),
        "email": email_clean,
        "password_hash": get_password_hash(datos.password_provisoria),
        "rol": "administrador",
        "estado": "activo"
    }

    res = supabase.table("administradores").insert(nuevo_admin).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al persistir el nuevo administrador en la base de datos."
        )

    nuevo_id = res.data[0]["id"]

    # Registro de auditoría inmutable
    try:
        supabase.table("logs_auditoria").insert({
            "administrador_id": admin_id,
            "accion": "ALTA_ADMINISTRADOR",
            "usuario_afectado_id": nuevo_id,
            "usuario_afectado_tipo": "administrador",
            "justificacion": f"Alta institucional creada por {admin_ejecutor.get('email', 'Admin')}."
        }).execute()
    except Exception:
        pass

    enviar_correo_bienvenida_admin(email_clean, datos.nombre_completo, datos.password_provisoria)

    return {
        "mensaje": "Nuevo administrador registrado exitosamente. Se han enviado las credenciales provisorias por correo.",
        "admin_id": nuevo_id
    }

# ==============================================================================
# 3. CdU07 - INHABILITAR CUENTA CON JUSTIFICACIÓN Y AUDITORÍA
# ==============================================================================
@router.put(
    "/usuarios/{usuario_id}/inhabilitar",
    summary="Inhabilitar cuenta con justificación obligatoria y auditoría (CdU07)"
)
def inhabilitar_usuario(
    usuario_id: str,
    datos: InhabilitarUsuarioInput,
    admin_id: str = Depends(get_current_user_id)
):
    admin_ejecutor = verificar_admin_activo(admin_id)

    if datos.tipo_usuario == "administrador":
        if usuario_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No es posible auto-inhabilitar la cuenta administrativa en uso."
            )
        target_res = supabase.table("administradores").select("*").eq("id", usuario_id).execute()
        if not target_res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrador no encontrado.")
        
        target = target_res.data[0]
        supabase.table("administradores").update({"estado": "inhabilitado", "actualizado_el": "now()"}).eq("id", usuario_id).execute()
        enviar_correo_inhabilitacion_admin(target["email"], target["nombre_completo"], datos.motivo_inhabilitacion)
    else:
        target_res = supabase.table("comerciantes").select("*").eq("id", usuario_id).execute()
        if not target_res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comerciante no encontrado.")
        
        target = target_res.data[0]
        supabase.table("comerciantes").update({"estado": "inhabilitado", "actualizado_el": "now()"}).eq("id", usuario_id).execute()
        
        # Pausar existencias de inventario para retirar ofertas de la vista pública
        try:
            supabase.table("inventario_items").update({"estado": "sin_stock"}).eq("comerciante_id", usuario_id).execute()
        except Exception:
            pass
        
        enviar_correo_inhabilitacion_comerciante(target["email"], target.get("nombre_razon_social", "Comercio"), datos.motivo_inhabilitacion)

    # Registro de auditoría inmutable
    try:
        supabase.table("logs_auditoria").insert({
            "administrador_id": admin_id,
            "accion": "INHABILITAR_USUARIO",
            "usuario_afectado_id": usuario_id,
            "usuario_afectado_tipo": datos.tipo_usuario,
            "justificacion": datos.motivo_inhabilitacion
        }).execute()
    except Exception:
        pass

    return {
        "mensaje": f"La cuenta de {datos.tipo_usuario} ha sido inhabilitada exitosamente.",
        "estado": "inhabilitado"
    }

# ==============================================================================
# 4. CdU07 - REACTIVAR CUENTA DE USUARIO
# ==============================================================================
@router.put(
    "/usuarios/{usuario_id}/reactivar",
    summary="Reactivar cuenta de usuario previamente suspendida"
)
def reactivar_usuario(
    usuario_id: str,
    datos: ReactivarUsuarioInput,
    admin_id: str = Depends(get_current_user_id)
):
    admin_ejecutor = verificar_admin_activo(admin_id)

    if datos.tipo_usuario == "administrador":
        target_res = supabase.table("administradores").select("*").eq("id", usuario_id).execute()
        if not target_res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrador no encontrado.")
        
        target = target_res.data[0]
        supabase.table("administradores").update({"estado": "activo", "actualizado_el": "now()"}).eq("id", usuario_id).execute()
        enviar_correo_reactivacion_admin(target["email"], target["nombre_completo"])
    else:
        target_res = supabase.table("comerciantes").select("*").eq("id", usuario_id).execute()
        if not target_res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comerciante no encontrado.")
        
        target = target_res.data[0]
        supabase.table("comerciantes").update({"estado": "activo", "actualizado_el": "now()"}).eq("id", usuario_id).execute()
        enviar_correo_reactivacion_comerciante(target["email"], target.get("nombre_razon_social", "Comercio"))

    try:
        supabase.table("logs_auditoria").insert({
            "administrador_id": admin_id,
            "accion": "REACTIVAR_USUARIO",
            "usuario_afectado_id": usuario_id,
            "usuario_afectado_tipo": datos.tipo_usuario,
            "justificacion": datos.motivo_reactivacion or "Reactivación formal de cuenta autorizada."
        }).execute()
    except Exception:
        pass

    return {
        "mensaje": f"La cuenta de {datos.tipo_usuario} ha sido reactivada exitosamente.",
        "estado": "activo"
    }