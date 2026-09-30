from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
import re
from app.schemas.comunidad_schema import (
    ComunidadCreateInput, 
    ComunidadUpdateInput, 
    ComunidadResponse,
    ComunidadDetalleResponse,
    ComunidadListItemResponse,
    BusquedaComunidadesResponse,
    SolicitudIngresoResponse,
    SolicitudDetalleItem,
    EvaluarSolicitudInput,
    EvaluarSolicitudResponse,
    AbandonarComunidadResponse,
    ExpulsarIntegranteInput,
    ExpulsarIntegranteResponse,
    AsignarModeradorResponse,
    RevocarModeradorResponse,
    SolicitarEliminacionComunidadInput,
    SolicitarEliminacionComunidadResponse,
    SolicitudEliminacionAdminItem,
    EvaluarEliminacionComunidadInput,
    EvaluarEliminacionComunidadResponse
)
from app.core.security import get_current_user_id, get_current_admin
from app.core.email_service import (
    enviar_correo_cambio_nombre_comunidad,
    enviar_correo_nueva_solicitud_comunidad,
    enviar_correo_resolucion_solicitud_comunidad,
    enviar_correo_expulsion_comunidad,
    enviar_correo_asignacion_moderador_comunidad,
    enviar_correo_revocacion_moderador_comunidad,
    enviar_correo_solicitud_eliminacion_comunidad,
    enviar_correo_resolucion_eliminacion_comunidad
)
from app.db.supabase_client import supabase

router = APIRouter(prefix="/comunidades", tags=["Red de Comunidades B2B (Sprint 4 / CdU13 al CdU24)"])

# ==============================================================================
# 0. CdU13 & CdU14 - BUSCAR Y FILTRAR COMUNIDADES ACTIVAS
# ==============================================================================
@router.get(
    "/buscar",
    response_model=BusquedaComunidadesResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar comunidades por nombre/palabra clave y filtrar por rubro (CdU13 / CdU14)"
)
def buscar_y_filtrar_comunidades(
    q: Optional[str] = Query(None, description="Término de búsqueda o palabra clave (CdU13)"),
    rubro: Optional[str] = Query(None, description="Rubro temático comercial (CdU14)"),
    user_id: str = Depends(get_current_user_id)
):
    termino_limpio = q.strip() if q else None
    rubro_limpio = rubro.strip() if (rubro and rubro != "todos") else None

    try:
        query = supabase.table("comunidades").select("*").eq("estado", "Activa")

        if rubro_limpio:
            query = query.eq("rubro", rubro_limpio)

        if termino_limpio:
            filtro_or = f"nombre.ilike.%{termino_limpio}%,descripcion.ilike.%{termino_limpio}%"
            query = query.or_(filtro_or)

        res_comunidades = query.order("creado_el", desc=True).execute()
        comunidades_data = res_comunidades.data or []

        membresias_res = (
            supabase.table("comunidad_miembros")
            .select("comunidad_id, rol")
            .eq("comerciante_id", user_id)
            .eq("estado", "activo")
            .execute()
        )
        membresias_map = {m["comunidad_id"]: m["rol"] for m in (membresias_res.data or [])}

        solicitudes_res = (
            supabase.table("comunidad_solicitudes")
            .select("comunidad_id, estado")
            .eq("comerciante_id", user_id)
            .execute()
        )
        solicitudes_map = {s["comunidad_id"]: s["estado"] for s in (solicitudes_res.data or [])}

        lista_formateada: List[dict] = []
        for c in comunidades_data:
            c_id = c["id"]
            rol = membresias_map.get(c_id)
            solicitud_estado = solicitudes_map.get(c_id)

            count_query = (
                supabase.table("comunidad_miembros")
                .select("id", count="exact")
                .eq("comunidad_id", c_id)
                .eq("estado", "activo")
                .execute()
            )
            total_m = count_query.count if count_query.count is not None else 1

            lista_formateada.append({
                "id": c_id,
                "nombre": c["nombre"],
                "descripcion": c.get("descripcion"),
                "rubro": c["rubro"],
                "creador_id": c["creador_id"],
                "estado": c["estado"],
                "total_miembros": total_m,
                "rol_usuario_actual": rol,
                "estado_solicitud": solicitud_estado,
                "es_moderador_o_creador": (rol in ["Creador", "Moderador"]),
                "creado_el": c["creado_el"]
            })

        return {
            "termino_busqueda": termino_limpio,
            "rubro_filtro": rubro_limpio,
            "total_coincidencias": len(lista_formateada),
            "comunidades": lista_formateada
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar la búsqueda de comunidades: {str(e)}"
        )

# ==============================================================================
# 1. LISTAR TODAS LAS COMUNIDADES ACTIVAS
# ==============================================================================
@router.get(
    "/todas",
    response_model=List[ComunidadListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las comunidades activas con el estado de membresía del usuario"
)
def listar_todas_las_comunidades(user_id: str = Depends(get_current_user_id)):
    com_res = (
        supabase.table("comunidades")
        .select("*")
        .eq("estado", "Activa")
        .order("creado_el", desc=True)
        .execute()
    )
    comunidades = com_res.data or []

    membresias_res = (
        supabase.table("comunidad_miembros")
        .select("comunidad_id, rol, estado")
        .eq("comerciante_id", user_id)
        .eq("estado", "activo")
        .execute()
    )
    membresias_map = {m["comunidad_id"]: m["rol"] for m in (membresias_res.data or [])}

    solicitudes_res = (
        supabase.table("comunidad_solicitudes")
        .select("comunidad_id, estado")
        .eq("comerciante_id", user_id)
        .execute()
    )
    solicitudes_map = {s["comunidad_id"]: s["estado"] for s in (solicitudes_res.data or [])}

    resultado: List[dict] = []
    for c in comunidades:
        c_id = c["id"]
        rol = membresias_map.get(c_id)
        solicitud_estado = solicitudes_map.get(c_id)
        
        count_query = (
            supabase.table("comunidad_miembros")
            .select("id", count="exact")
            .eq("comunidad_id", c_id)
            .eq("estado", "activo")
            .execute()
        )
        total_m = count_query.count if count_query.count is not None else 1

        resultado.append({
            "id": c_id,
            "nombre": c["nombre"],
            "descripcion": c.get("descripcion"),
            "rubro": c["rubro"],
            "creador_id": c["creador_id"],
            "estado": c["estado"],
            "total_miembros": total_m,
            "rol_usuario_actual": rol,
            "estado_solicitud": solicitud_estado,
            "es_moderador_o_creador": (rol in ["Creador", "Moderador"]),
            "creado_el": c["creado_el"]
        })

    return resultado

# ==============================================================================
# 2. CdU15 - CREAR NUEVA COMUNIDAD POR RUBRO
# ==============================================================================
@router.post(
    "/nueva",
    response_model=ComunidadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva comunidad con rubro fijo del perfil del usuario (CdU15)"
)
def crear_nueva_comunidad(
    datos: ComunidadCreateInput,
    user_id: str = Depends(get_current_user_id)
):
    nombre_limpio = datos.nombre.strip()
    descripcion_limpia = datos.descripcion.strip() if datos.descripcion else None

    if not nombre_limpio or len(nombre_limpio) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de la comunidad debe contener al menos 3 caracteres."
        )

    com_res = supabase.table("comerciantes").select("rubro_comercial, estado").eq("id", user_id).execute()
    if not com_res.data or com_res.data[0].get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo comerciantes con cuenta activa pueden fundar comunidades comerciales."
        )

    rubro_oficial = com_res.data[0].get("rubro_comercial")
    if not rubro_oficial:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Su perfil comercial no posee un rubro definido para asignar a la comunidad."
        )

    try:
        rpc_res = supabase.rpc(
            "fn_crear_comunidad_con_creador",
            {
                "p_comerciante_id": user_id,
                "p_nombre": nombre_limpio,
                "p_descripcion": descripcion_limpia,
                "p_rubro": rubro_oficial
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo respuesta de la transacción en base de datos.")

        return resultado

    except Exception as e:
        err_msg = str(e)
        if "ya se encuentra en uso por otra comunidad" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre ingresado ya se encuentra en uso por otra comunidad activa en la plataforma."
            )
        if "cuenta activa pueden fundar comunidades" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo comerciantes con cuenta activa pueden fundar comunidades comerciales."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar la creación de la comunidad: {err_msg}"
        )

# ==============================================================================
# 3. OBTENER DETALLE Y ROL DEL USUARIO EN LA COMUNIDAD (Soporte CdU16 a CdU24)
# ==============================================================================
@router.get(
    "/{comunidad_id}/detalle",
    response_model=ComunidadDetalleResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener detalles de una comunidad y el rango jerárquico del usuario consultante"
)
def obtener_detalle_comunidad(
    comunidad_id: str,
    user_id: str = Depends(get_current_user_id)
):
    com_res = supabase.table("comunidades").select("*, comerciantes(nombre_razon_social)").eq("id", comunidad_id).execute()
    if not com_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La comunidad solicitada no existe o no se encuentra disponible."
        )

    comunidad = com_res.data[0]

    miembro_res = (
        supabase.table("comunidad_miembros")
        .select("rol, estado")
        .eq("comunidad_id", comunidad_id)
        .eq("comerciante_id", user_id)
        .eq("estado", "activo")
        .execute()
    )

    rol_usuario = miembro_res.data[0]["rol"] if miembro_res.data else None
    es_mod_o_creador = rol_usuario in ["Creador", "Moderador"]

    solicitud_res = (
        supabase.table("comunidad_solicitudes")
        .select("estado")
        .eq("comunidad_id", comunidad_id)
        .eq("comerciante_id", user_id)
        .execute()
    )
    solicitud_estado = solicitud_res.data[0]["estado"] if solicitud_res.data else None

    return {
        "id": comunidad["id"],
        "nombre": comunidad["nombre"],
        "descripcion": comunidad.get("descripcion"),
        "rubro": comunidad["rubro"],
        "creador_id": comunidad["creador_id"],
        "estado": comunidad["estado"],
        "creado_el": comunidad["creado_el"],
        "actualizado_el": comunidad["actualizado_el"],
        "rol_usuario_actual": rol_usuario,
        "estado_solicitud": solicitud_estado,
        "es_moderador_o_creador": es_mod_o_creador
    }

# ==============================================================================
# 4. CdU16 - CONFIGURAR COMUNIDAD
# ==============================================================================
@router.put(
    "/{comunidad_id}/configuracion",
    response_model=ComunidadResponse,
    status_code=status.HTTP_200_OK,
    summary="Modificar configuración con ventana de 15 días y alerta por correo (CdU16)"
)
def configurar_comunidad(
    comunidad_id: str,
    datos: ComunidadUpdateInput,
    user_id: str = Depends(get_current_user_id)
):
    nombre_limpio = datos.nombre.strip()
    descripcion_limpia = datos.descripcion.strip() if datos.descripcion else None

    if not nombre_limpio or len(nombre_limpio) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de la comunidad debe contener al menos 3 caracteres."
        )

    try:
        rpc_res = supabase.rpc(
            "fn_configurar_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_usuario_id": user_id,
                "p_nuevo_nombre": nombre_limpio,
                "p_nueva_descripcion": descripcion_limpia
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo respuesta de la actualización en base de datos.")

        if resultado.get("cambio_nombre"):
            try:
                miembros_res = (
                    supabase.table("comunidad_miembros")
                    .select("comerciantes(email)")
                    .eq("comunidad_id", comunidad_id)
                    .eq("estado", "activo")
                    .execute()
                )
                
                lista_emails = [
                    m["comerciantes"]["email"] 
                    for m in (miembros_res.data or []) 
                    if m.get("comerciantes") and m["comerciantes"].get("email")
                ]

                nombre_ant = resultado.get("nombre_anterior", "Denominación Previa")
                nombre_nuevo = resultado.get("nombre")
                rubro_com = resultado.get("rubro")

                for correo in set(lista_emails):
                    try:
                        enviar_correo_cambio_nombre_comunidad(correo, nombre_ant, nombre_nuevo, rubro_com)
                    except Exception as mail_err:
                        print(f"[SMTP WARN CdU16] Error enviando a {correo}: {mail_err}")
            except Exception as notify_err:
                print(f"[WARN CdU16] Fallo al recuperar lista de miembros: {notify_err}")

        return resultado

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "El nombre de la comunidad solo puede modificarse cada 15 días" in texto_limpio:
            match_dias = re.search(r"El nombre de la comunidad solo puede modificarse cada 15 días\.[^']*", texto_limpio)
            mensaje_final = match_dias.group(0) if match_dias else texto_limpio
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=mensaje_final)
        if "Acceso denegado: Se requieren permisos" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido: Solo el Creador o los Moderadores pueden configurar esta comunidad.")
        if "ya pertenece a otra comunidad activa" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre ingresado ya pertenece a otra comunidad activa en la plataforma.")
        if "La comunidad solicitada no existe" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La comunidad solicitada no existe o fue dada de baja.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al actualizar la configuración: {texto_limpio}")

# ==============================================================================
# 5. CdU17 - SOLICITAR INGRESO A UNA COMUNIDAD
# ==============================================================================
@router.post(
    "/{comunidad_id}/solicitar-ingreso",
    response_model=SolicitudIngresoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar solicitud de ingreso a una comunidad con validación de rubro (CdU17)"
)
def solicitar_ingreso_comunidad(
    comunidad_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_solicitar_ingreso_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_comerciante_id": user_id
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo respuesta al registrar la solicitud en base de datos.")

        try:
            solicitante_res = supabase.table("comerciantes").select("nombre_razon_social, rubro_comercial").eq("id", user_id).execute()
            solicitante_info = solicitante_res.data[0] if solicitante_res.data else {}

            mods_res = (
                supabase.table("comunidad_miembros")
                .select("comerciantes(email)")
                .eq("comunidad_id", comunidad_id)
                .in_("rol", ["Creador", "Moderador"])
                .eq("estado", "activo")
                .execute()
            )

            emails_mods = [
                m["comerciantes"]["email"]
                for m in (mods_res.data or [])
                if m.get("comerciantes") and m["comerciantes"].get("email")
            ]

            nom_com = resultado.get("comunidad_nombre", "Comunidad")
            nom_sol = solicitante_info.get("nombre_razon_social", "Comerciante")
            rub_sol = solicitante_info.get("rubro_comercial", "General")

            for correo_mod in set(emails_mods):
                try:
                    enviar_correo_nueva_solicitud_comunidad(correo_mod, nom_com, nom_sol, rub_sol)
                except Exception as mail_e:
                    print(f"[SMTP WARN CdU17] Error notificando moderador: {mail_e}")
        except Exception as notify_e:
            print(f"[WARN CdU17] Fallo al recuperar moderadores para notificación: {notify_e}")

        return resultado

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "Incompatibilidad sectorial" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incompatibilidad sectorial: No posee el rubro comercial requerido para unirse a esta comunidad.")
        if "Usted ya forma parte" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usted ya es miembro activo de esta comunidad.")
        if "Ya posee una solicitud pendiente" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya posee una solicitud pendiente de evaluación para esta comunidad.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al enviar la solicitud: {texto_limpio}")

# ==============================================================================
# 6. CdU18 - CONSULTAR SOLICITUDES PENDIENTES DE UNA COMUNIDAD
# ==============================================================================
@router.get(
    "/{comunidad_id}/solicitudes",
    response_model=List[SolicitudDetalleItem],
    status_code=status.HTTP_200_OK,
    summary="Listar solicitudes de membresía pendientes para moderación (CdU18)"
)
def listar_solicitudes_pendientes(
    comunidad_id: str,
    user_id: str = Depends(get_current_user_id)
):
    miembro_res = (
        supabase.table("comunidad_miembros")
        .select("rol")
        .eq("comunidad_id", comunidad_id)
        .eq("comerciante_id", user_id)
        .eq("estado", "activo")
        .execute()
    )
    rol = miembro_res.data[0]["rol"] if miembro_res.data else None
    if rol not in ["Creador", "Moderador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: Solo el Creador o los Moderadores pueden revisar solicitudes de ingreso."
        )

    sol_res = (
        supabase.table("comunidad_solicitudes")
        .select("id, comunidad_id, comerciante_id, creado_el, comerciantes(*)")
        .eq("comunidad_id", comunidad_id)
        .eq("estado", "Pendiente")
        .order("creado_el", desc=False)
        .execute()
    )

    resultado: List[dict] = []
    for s in (sol_res.data or []):
        c = s.get("comerciantes") or {}
        resultado.append({
            "id": s["id"],
            "comunidad_id": s["comunidad_id"],
            "comerciante_id": s["comerciante_id"],
            "nombre_razon_social": c.get("nombre_razon_social", "Comerciante"),
            "email": c.get("email", "—"),
            "cuit_cuil": c.get("cuit_cuil", "—"),
            "rubro_comercial": c.get("rubro_comercial", "General"),
            "ciudad_localidad": c.get("ciudad_localidad", "—"),
            "provincia": c.get("provincia", "—"),
            "creado_el": s["creado_el"]
        })

    return resultado

# ==============================================================================
# 7. CdU18 - EVALUAR SOLICITUD DE INGRESO (APROBAR O RECHAZAR)
# ==============================================================================
@router.put(
    "/solicitudes/{solicitud_id}/evaluar",
    response_model=EvaluarSolicitudResponse,
    status_code=status.HTTP_200_OK,
    summary="Aprobar o rechazar solicitud de ingreso con notificación SMTP (CdU18)"
)
def evaluar_solicitud_ingreso(
    solicitud_id: str,
    datos: EvaluarSolicitudInput,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_evaluar_solicitud_comunidad",
            {
                "p_solicitud_id": solicitud_id,
                "p_moderador_id": user_id,
                "p_decision": datos.decision
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo respuesta al procesar la evaluación de la solicitud.")

        try:
            dest_email = resultado.get("comerciante_email")
            dest_nombre = resultado.get("comerciante_nombre", "Comercio")
            nom_comunidad = resultado.get("comunidad_nombre", "Comunidad")
            es_aprobada = (datos.decision == "aprobar")

            if dest_email:
                enviar_correo_resolucion_solicitud_comunidad(
                    destinatario=dest_email,
                    nombre_comercio=dest_nombre,
                    nombre_comunidad=nom_comunidad,
                    aprobada=es_aprobada
                )
        except Exception as mail_err:
            print(f"[SMTP WARN CdU18] Error al despachar correo de resolución: {mail_err}")

        mensaje_exito = (
            f"El comerciante ha sido incorporado como Integrante de '{resultado.get('comunidad_nombre')}'."
            if datos.decision == "aprobar" else
            f"La solicitud de ingreso a '{resultado.get('comunidad_nombre')}' ha sido rechazada."
        )

        return {
            "solicitud_id": resultado["solicitud_id"],
            "decision": resultado["decision"],
            "nuevo_estado": resultado["nuevo_estado"],
            "comunidad_id": resultado["comunidad_id"],
            "comunidad_nombre": resultado["comunidad_nombre"],
            "mensaje": mensaje_exito
        }

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "Solo el Creador o los Moderadores" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Solo el Creador o los Moderadores pueden evaluar solicitudes.")
        if "ya ha sido evaluada previamente" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=texto_limpio)
        if "no existe" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La solicitud especificada no existe.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al evaluar la solicitud: {texto_limpio}")

# ==============================================================================
# 8. CdU19 - ABANDONAR COMUNIDAD (SALIDA VOLUNTARIA Y CONTROL ACÉFALO)
# ==============================================================================
@router.delete(
    "/{comunidad_id}/abandonar",
    response_model=AbandonarComunidadResponse,
    status_code=status.HTTP_200_OK,
    summary="Abandonar voluntariamente una comunidad comercial (CdU19)"
)
def abandonar_comunidad(
    comunidad_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_abandonar_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_comerciante_id": user_id
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo confirmación de la base de datos al abandonar la comunidad.")

        return resultado

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "único moderador" in texto_limpio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="No es posible abandonar la comunidad siendo el único moderador. Asigne o promueva a otro integrante antes de retirarse."
            )
        if "no forma parte activa" in texto_limpio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Usted no forma parte activa de esta comunidad."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Fallo al procesar la salida de la comunidad: {texto_limpio}"
        )

# ==============================================================================
# 9. CdU20 - EXPULSAR INTEGRANTE DE LA COMUNIDAD (MODERACIÓN Y BITÁCORA)
# ==============================================================================
@router.delete(
    "/{comunidad_id}/miembros/{integrante_id}/expulsar",
    response_model=ExpulsarIntegranteResponse,
    status_code=status.HTTP_200_OK,
    summary="Expulsar a un integrante activo con justificación obligatoria y auditoría (CdU20)"
)
def expulsar_integrante_comunidad(
    comunidad_id: str,
    integrante_id: str,
    datos: ExpulsarIntegranteInput,
    user_id: str = Depends(get_current_user_id)
):
    justificacion_limpia = datos.justificacion.strip()
    if len(justificacion_limpia) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La justificación de la expulsión es obligatoria y debe contener al menos 5 caracteres."
        )

    try:
        rpc_res = supabase.rpc(
            "fn_expulsar_integrante_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_moderador_id": user_id,
                "p_integrante_id": integrante_id,
                "p_justificacion": justificacion_limpia
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo confirmación de la expulsión en base de datos.")

        try:
            dest_email = resultado.get("comerciante_email")
            dest_nombre = resultado.get("comerciante_nombre", "Comercio")
            nom_comunidad = resultado.get("comunidad_nombre", "Comunidad")

            if dest_email:
                enviar_correo_expulsion_comunidad(
                    destinatario=dest_email,
                    nombre_comercio=dest_nombre,
                    nombre_comunidad=nom_comunidad,
                    motivo=justificacion_limpia
                )
        except Exception as mail_err:
            print(f"[SMTP WARN CdU20] Error despachando correo de expulsión: {mail_err}")

        return {
            "comunidad_id": resultado["comunidad_id"],
            "comunidad_nombre": resultado["comunidad_nombre"],
            "integrante_id": resultado["integrante_id"],
            "mensaje": resultado.get("mensaje", "El integrante ha sido expulsado exitosamente.")
        }

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "Creador de la comunidad no puede ser expulsado" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El Creador de la comunidad posee inmunidad institucional y no puede ser expulsado.")
        if "Un Moderador no puede expulsar a otro Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Un Moderador no puede expulsar a otro Moderador. Esta facultad corresponde al Creador.")
        if "Se requieren privilegios de Creador o Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Se requieren permisos de gestión para expulsar integrantes.")
        if "No es posible auto-expulsarse" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No es posible auto-expulsarse. Utilice la opción de abandonar comunidad.")
        if "no es un miembro activo" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario indicado no pertenece activamente a esta comunidad.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al procesar la expulsión: {texto_limpio}")

# ==============================================================================
# 10. CdU21 - ASIGNAR ROL DE MODERADOR A UN INTEGRANTE
# ==============================================================================
@router.put(
    "/{comunidad_id}/miembros/{integrante_id}/hacer-moderador",
    response_model=AsignarModeradorResponse,
    status_code=status.HTTP_200_OK,
    summary="Promover a un Integrante activo al rol de Moderador (CdU21)"
)
def asignar_rol_moderador(
    comunidad_id: str,
    integrante_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_asignar_moderador_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_moderador_id": user_id,
                "p_integrante_id": integrante_id
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo confirmación de la base de datos al promover al integrante.")

        try:
            dest_email = resultado.get("comerciante_email")
            dest_nombre = resultado.get("comerciante_nombre", "Comercio")
            nom_comunidad = resultado.get("comunidad_nombre", "Comunidad")

            if dest_email:
                enviar_correo_asignacion_moderador_comunidad(
                    destinatario=dest_email,
                    nombre_comercio=dest_nombre,
                    nombre_comunidad=nom_comunidad
                )
        except Exception as mail_err:
            print(f"[SMTP WARN CdU21] Error enviando correo de ascenso: {mail_err}")

        return {
            "comunidad_id": resultado["comunidad_id"],
            "comunidad_nombre": resultado["comunidad_nombre"],
            "integrante_id": resultado["integrante_id"],
            "nuevo_rol": resultado["nuevo_rol"],
            "mensaje": resultado.get("mensaje", "El integrante ha sido ascendido a Moderador exitosamente.")
        }

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "ya posee el rol de Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario seleccionado ya posee el rol de Moderador.")
        if "Se requieren permisos de Creador o Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Se requieren permisos de moderación para realizar ascensos.")
        if "no es un miembro activo" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario objetivo no es un miembro activo de esta comunidad.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al asignar el rol de Moderador: {texto_limpio}")

# ==============================================================================
# 11. CdU22 - REVOCAR ROL DE MODERADOR A UN INTEGRANTE
# ==============================================================================
@router.put(
    "/{comunidad_id}/miembros/{integrante_id}/revocar-moderador",
    response_model=RevocarModeradorResponse,
    status_code=status.HTTP_200_OK,
    summary="Revocar permisos de Moderador volviendo al usuario a Integrante (CdU22)"
)
def revocar_rol_moderador(
    comunidad_id: str,
    integrante_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_revocar_moderador_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_moderador_id": user_id,
                "p_integrante_id": integrante_id
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo confirmación de la base de datos al revocar la moderación.")

        try:
            dest_email = resultado.get("comerciante_email")
            dest_nombre = resultado.get("comerciante_nombre", "Comercio")
            nom_comunidad = resultado.get("comunidad_nombre", "Comunidad")

            if dest_email:
                enviar_correo_revocacion_moderador_comunidad(
                    destinatario=dest_email,
                    nombre_comercio=dest_nombre,
                    nombre_comunidad=nom_comunidad
                )
        except Exception as mail_err:
            print(f"[SMTP WARN CdU22] Error enviando correo de revocación: {mail_err}")

        return {
            "comunidad_id": resultado["comunidad_id"],
            "comunidad_nombre": resultado["comunidad_nombre"],
            "integrante_id": resultado["integrante_id"],
            "nuevo_rol": resultado["nuevo_rol"],
            "mensaje": resultado.get("mensaje", "Los privilegios de moderación han sido revocados exitosamente.")
        }

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "Creador de la comunidad no puede ser degradado" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Jerarquía institucional: El Creador de la comunidad no puede ser degradado.")
        if "Un Moderador no puede revocar a otro Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Un Moderador no puede revocar a otro Moderador. Esta facultad corresponde al Creador.")
        if "Se requieren permisos de Creador o Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Se requieren permisos de gestión.")
        if "no posee el rol de Moderador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario seleccionado no posee el rol de Moderador.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al revocar la moderación: {texto_limpio}")

# ==============================================================================
# 12. CdU23 - SOLICITAR ELIMINACIÓN DE COMUNIDAD
# ==============================================================================
@router.post(
    "/{comunidad_id}/solicitar-eliminacion",
    response_model=SolicitarEliminacionComunidadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar eliminación de una comunidad comercial por su Creador (CdU23)"
)
def solicitar_eliminacion_comunidad(
    comunidad_id: str,
    datos: SolicitarEliminacionComunidadInput,
    user_id: str = Depends(get_current_user_id)
):
    motivo_limpio = datos.motivo.strip()
    if len(motivo_limpio) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El motivo de la solicitud de eliminación es obligatorio y debe contener al menos 5 caracteres."
        )

    try:
        rpc_res = supabase.rpc(
            "fn_solicitar_eliminacion_comunidad",
            {
                "p_comunidad_id": comunidad_id,
                "p_creador_id": user_id,
                "p_motivo": motivo_limpio
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo confirmación de la base de datos al solicitar la eliminación.")

        try:
            admins_res = supabase.table("administradores").select("email").eq("estado", "activo").execute()
            lista_emails_admin = [a["email"] for a in (admins_res.data or []) if a.get("email")]

            nom_creador = resultado.get("creador_nombre", "Creador")
            nom_comunidad = resultado.get("comunidad_nombre", "Comunidad")

            for correo_adm in set(lista_emails_admin):
                try:
                    enviar_correo_solicitud_eliminacion_comunidad(
                        destinatario=correo_adm,
                        nombre_creador=nom_creador,
                        nombre_comunidad=nom_comunidad,
                        motivo=motivo_limpio
                    )
                except Exception as mail_err:
                    print(f"[SMTP WARN CdU23] Error alertando a admin {correo_adm}: {mail_err}")
        except Exception as notify_err:
            print(f"[WARN CdU23] Fallo al consultar correos de administradores: {notify_err}")

        return {
            "solicitud_id": resultado["solicitud_id"],
            "comunidad_id": resultado["comunidad_id"],
            "comunidad_nombre": resultado["comunidad_nombre"],
            "creador_id": resultado["creador_id"],
            "nuevo_estado": resultado["nuevo_estado"],
            "mensaje": resultado.get("mensaje", "Solicitud de eliminación registrada correctamente.")
        }

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "Únicamente el Creador fundador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Únicamente el Creador fundador puede solicitar la eliminación de la comunidad.")
        if "ya posee una solicitud de eliminación pendiente" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta comunidad ya posee una solicitud de eliminación pendiente de evaluación.")
        if "Solo es posible solicitar la eliminación de comunidades activas" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=texto_limpio)
        if "no existe" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La comunidad especificada no existe.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al solicitar la eliminación: {texto_limpio}")

# ==============================================================================
# 13. CdU24 - CONSULTAR SOLICITUDES DE ELIMINACIÓN PENDIENTES (ADMIN)
# ==============================================================================
@router.get(
    "/admin/solicitudes-eliminacion",
    response_model=List[SolicitudEliminacionAdminItem],
    status_code=status.HTTP_200_OK,
    summary="Listar solicitudes de eliminación de comunidad pendientes para Administrador (CdU24)"
)
def listar_solicitudes_eliminacion_admin(admin: dict = Depends(get_current_admin)):
    """
    CdU24: Recupera todas las comunidades en estado 'Pendiente de eliminación'
    junto con los datos del fundador y el motivo registrado para la evaluación administrativa.
    """
    res = (
        supabase.table("comunidad_solicitudes_eliminacion")
        .select("id, comunidad_id, creador_id, motivo, estado, creado_el, comunidades(nombre, rubro), comerciantes(nombre_razon_social, email)")
        .eq("estado", "Pendiente")
        .order("creado_el", desc=True)
        .execute()
    )

    resultado = []
    for item in (res.data or []):
        c = item.get("comunidades") or {}
        u = item.get("comerciantes") or {}
        resultado.append({
            "id": item["id"],
            "comunidad_id": item["comunidad_id"],
            "comunidad_nombre": c.get("nombre", "Comunidad"),
            "comunidad_rubro": c.get("rubro", "General"),
            "creador_id": item["creador_id"],
            "creador_nombre": u.get("nombre_razon_social", "Comerciante Creador"),
            "creador_email": u.get("email", "—"),
            "motivo": item["motivo"],
            "estado": item["estado"],
            "creado_el": item["creado_el"]
        })

    return resultado

# ==============================================================================
# 14. CdU24 - EVALUAR SOLICITUD DE ELIMINACIÓN DE COMUNIDAD (ADMIN)
# ==============================================================================
@router.put(
    "/admin/solicitudes-eliminacion/{solicitud_id}/evaluar",
    response_model=EvaluarEliminacionComunidadResponse,
    status_code=status.HTTP_200_OK,
    summary="Aprobar baja definitiva o rechazar y descongelar comunidad por Administrador (CdU24)"
)
def evaluar_solicitud_eliminacion_comunidad(
    solicitud_id: str,
    datos: EvaluarEliminacionComunidadInput,
    admin: dict = Depends(get_current_admin)
):
    """
    CdU24: Permite a un Administrador global emitir el fallo sobre una comunidad congelada.
    - Si se aprueba: se marca como 'Eliminada', se disuelven miembros y replicaciones, y se notifica al Creador e integrantes.
    - Si se rechaza: se descongela el espacio volviendo a estado 'Activa' y se notifica al Creador.
    - Registra el evento en logs_auditoria.
    """
    admin_id = admin["id"]

    try:
        rpc_res = supabase.rpc(
            "fn_evaluar_solicitud_eliminacion_comunidad",
            {
                "p_solicitud_id": solicitud_id,
                "p_admin_id": admin_id,
                "p_decision": datos.decision
            }
        ).execute()

        resultado = rpc_res.data
        if not resultado:
            raise Exception("No se obtuvo confirmación de la base de datos al evaluar la solicitud de eliminación.")

        # Despachar notificaciones SMTP
        try:
            creador_email = resultado.get("creador_email")
            creador_nombre = resultado.get("creador_nombre", "Comerciante")
            nom_comunidad = resultado.get("comunidad_nombre", "Comunidad")
            es_aprobada = (datos.decision == "aprobar")

            # 1. Notificar al Creador
            if creador_email:
                enviar_correo_resolucion_eliminacion_comunidad(
                    destinatario=creador_email,
                    nombre_destinatario=creador_nombre,
                    nombre_comunidad=nom_comunidad,
                    aprobada=es_aprobada
                )

            # 2. Si se aprobó la destrucción, notificar a los demás integrantes
            if es_aprobada:
                emails_miembros = resultado.get("emails_miembros") or []
                for m_email in set(emails_miembros):
                    if m_email != creador_email:
                        try:
                            enviar_correo_resolucion_eliminacion_comunidad(
                                destinatario=m_email,
                                nombre_destinatario="Estimado/a integrante",
                                nombre_comunidad=nom_comunidad,
                                aprobada=True
                            )
                        except Exception as m_err:
                            print(f"[SMTP WARN CdU24] Error notificando a miembro {m_email}: {m_err}")

        except Exception as mail_err:
            print(f"[SMTP WARN CdU24] Error despachando notificaciones: {mail_err}")

        return {
            "solicitud_id": resultado["solicitud_id"],
            "comunidad_id": resultado["comunidad_id"],
            "comunidad_nombre": resultado["comunidad_nombre"],
            "decision": resultado["decision"],
            "nuevo_estado_comunidad": resultado["nuevo_estado_comunidad"],
            "mensaje": resultado.get("mensaje", "La solicitud de eliminación ha sido procesada exitosamente.")
        }

    except Exception as e:
        err_msg = str(e)
        match_msg = re.search(r"'(?:message|details)':\s*'([^']+)'", err_msg)
        texto_limpio = match_msg.group(1) if match_msg else err_msg

        if "Se requieren privilegios de Administrador" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado: Se requieren privilegios de Administrador global.")
        if "ya ha sido evaluada previamente" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=texto_limpio)
        if "no existe" in texto_limpio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La solicitud especificada no existe.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fallo al evaluar la solicitud: {texto_limpio}")

# ==============================================================================
# 15. SOPORTE DETALLE COMUNIDAD: FEED DE PUBLICACIONES REPLICADAS (RF04 / CdU25)
# ==============================================================================
@router.get(
    "/{comunidad_id}/publicaciones",
    status_code=status.HTTP_200_OK,
    summary="Obtener las publicaciones de venta replicadas específicamente en esta comunidad (RF04 / CdU25)"
)
def obtener_publicaciones_comunidad(
    comunidad_id: str,
    user_id: str = Depends(get_current_user_id)
):
    rep_res = (
        supabase.table("publicacion_comunidades")
        .select("publicacion_id, publicaciones_venta(*, comerciantes(id, nombre_razon_social, cuit_cuil, provincia, ciudad_localidad))")
        .eq("comunidad_id", comunidad_id)
        .order("creado_el", desc=True)
        .execute()
    )
    
    pubs = []
    for item in (rep_res.data or []):
        p = item.get("publicaciones_venta")
        if p and p.get("estado") == "Activa":
            pubs.append(p)
            
    return pubs

# ==============================================================================
# 16. SOPORTE DETALLE COMUNIDAD: LISTADO DE MIEMBROS ACTIVOS (RF03)
# ==============================================================================
@router.get(
    "/{comunidad_id}/miembros",
    status_code=status.HTTP_200_OK,
    summary="Obtener la lista de comerciantes miembros de la comunidad con sus roles"
)
def obtener_miembros_comunidad(
    comunidad_id: str,
    user_id: str = Depends(get_current_user_id)
):
    miembros_res = (
        supabase.table("comunidad_miembros")
        .select("id, rol, estado, creado_el, comerciante_id, comerciantes(id, nombre_razon_social, email, cuit_cuil, rubro_comercial, ciudad_localidad, provincia)")
        .eq("comunidad_id", comunidad_id)
        .eq("estado", "activo")
        .order("creado_el", desc=False)
        .execute()
    )
    
    miembros_formateados = []
    for m in (miembros_res.data or []):
        c = m.get("comerciantes") or {}
        miembros_formateados.append({
            "miembro_id": m["id"],
            "comerciante_id": m["comerciante_id"],
            "rol": m["rol"],
            "es_usuario_actual": (m["comerciante_id"] == user_id),
            "nombre_razon_social": c.get("nombre_razon_social", "Comerciante"),
            "email": c.get("email", "—"),
            "cuit_cuil": c.get("cuit_cuil", "—"),
            "rubro_comercial": c.get("rubro_comercial", "General"),
            "ubicacion": f"{c.get('ciudad_localidad', '—')}, {c.get('provincia', '—')}",
            "fecha_ingreso": m["creado_el"]
        })

    return miembros_formateados