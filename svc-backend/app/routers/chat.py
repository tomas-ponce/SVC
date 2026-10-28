from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from app.core.security import get_current_user_id
from app.db.supabase_client import supabase

router = APIRouter(prefix="/chat", tags=["Central de Negociación y Notificaciones (Sprint 5)"])

class IniciarChatInput(BaseModel):
    publicacion_id: str
    mensaje_inicial: str = Field(..., min_length=1, max_length=3000)

class EnviarMensajeInput(BaseModel):
    contenido: str = Field(..., min_length=1, max_length=3000)

class PreferenciasNotificacionesInput(BaseModel):
    email_notificaciones_activas: bool = True
    horas_silencio: int = 0
    notificar_mensajes_chat: bool = True
    notificar_alertas_stock: bool = True
    notificar_comunidades: bool = True
    notificar_sanciones: bool = True

# ==============================================================================
# NOTIFICACIONES (RF07 / CdU62, CdU50, CdU51)
# ==============================================================================
@router.get("/notificaciones", status_code=status.HTTP_200_OK)
def obtener_notificaciones_usuario(
    filtro: Optional[str] = Query("todas", pattern="^(todas|stock|mensajes|comunidades)$"),
    user_id: str = Depends(get_current_user_id)
):
    """
    CdU62: Recupera el listado centralizado de notificaciones del comerciante
    con soporte de filtrado por categoría y cálculo de pendientes.
    """
    try:
        query = supabase.table("notificaciones")\
            .select("*")\
            .eq("comerciante_id", user_id)\
            .order("creado_el", desc=True)

        if filtro == "stock":
            query = query.eq("tipo", "alerta_stock")
        elif filtro == "mensajes":
            query = query.eq("tipo", "mensaje_chat")
        elif filtro == "comunidades":
            query = query.eq("tipo", "comunidad_publicacion")

        res = query.execute()
        items = res.data or []

        # Contadores de métricas
        total_no_leidas = sum(1 for n in items if not n.get("leida", False))
        no_leidas_stock = sum(1 for n in items if not n.get("leida", False) and n.get("tipo") == "alerta_stock")
        no_leidas_mensajes = sum(1 for n in items if not n.get("leida", False) and n.get("tipo") == "mensaje_chat")
        no_leidas_comunidades = sum(1 for n in items if not n.get("leida", False) and n.get("tipo") == "comunidad_publicacion")

        return {
            "total_notificaciones": len(items),
            "total_no_leidas": total_no_leidas,
            "metricas": {
                "stock": no_leidas_stock,
                "mensajes": no_leidas_mensajes,
                "comunidades": no_leidas_comunidades
            },
            "notificaciones": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notificaciones/{notificacion_id}/leer", status_code=status.HTTP_200_OK)
def descartar_notificacion_individual(
    notificacion_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """CdU50: Descartar o marcar como leída una notificación individual."""
    try:
        res = supabase.table("notificaciones")\
            .update({"leida": True})\
            .eq("id", notificacion_id)\
            .eq("comerciante_id", user_id)\
            .execute()
        return {"mensaje": "Notificación marcada como leída.", "id": notificacion_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notificaciones/marcar-todas-leidas", status_code=status.HTTP_200_OK)
def marcar_todas_notificaciones_leidas(
    user_id: str = Depends(get_current_user_id)
):
    """CdU51: Actualizar en lote todas las notificaciones pendientes a leídas."""
    try:
        res = supabase.table("notificaciones")\
            .update({"leida": True})\
            .eq("comerciante_id", user_id)\
            .eq("leida", False)\
            .execute()
        return {"mensaje": "Todas las notificaciones han sido marcadas como leídas."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notificaciones/preferencias", status_code=status.HTTP_200_OK, summary="Obtener preferencias de notificaciones (CdU48)")
def obtener_preferencias_notificaciones(user_id: str = Depends(get_current_user_id)):
    """CdU48: Recupera la configuración actual de alertas y estado de silencio del usuario."""
    try:
        res = supabase.table("notificaciones_preferencias").select("*").eq("comerciante_id", user_id).execute()
        if res.data:
            return res.data[0]
        # Valores por defecto de la plataforma
        return {
            "comerciante_id": user_id,
            "email_notificaciones_activas": True,
            "silenciado_hasta": None,
            "notificar_mensajes_chat": True,
            "notificar_alertas_stock": True,
            "notificar_comunidades": True,
            "notificar_sanciones": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener preferencias: {str(e)}")

@router.put("/notificaciones/preferencias", status_code=status.HTTP_200_OK, summary="Actualizar preferencias de notificaciones (CdU48)")
def actualizar_preferencias_notificaciones(datos: PreferenciasNotificacionesInput, user_id: str = Depends(get_current_user_id)):
    """CdU48: Actualiza canales habilitados y ventana temporal de silencio de alertas."""
    try:
        silenciado_hasta = None
        if datos.horas_silencio > 0:
            silenciado_hasta = (datetime.now(timezone.utc) + timedelta(hours=datos.horas_silencio)).isoformat()

        payload = {
            "comerciante_id": user_id,
            "email_notificaciones_activas": datos.email_notificaciones_activas,
            "silenciado_hasta": silenciado_hasta,
            "notificar_mensajes_chat": datos.notificar_mensajes_chat,
            "notificar_alertas_stock": datos.notificar_alertas_stock,
            "notificar_comunidades": datos.notificar_comunidades,
            "notificar_sanciones": datos.notificar_sanciones,
            "actualizado_el": "now()"
        }

        # Comprobar si ya existe fila para update o insert
        existente = supabase.table("notificaciones_preferencias").select("comerciante_id").eq("comerciante_id", user_id).execute()
        if existente.data:
            supabase.table("notificaciones_preferencias").update(payload).eq("comerciante_id", user_id).execute()
        else:
            supabase.table("notificaciones_preferencias").insert(payload).execute()

        return {"mensaje": "Preferencias de notificaciones actualizadas correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar preferencias: {str(e)}")

# ==============================================================================
# NEGOCIACIONES & CHATS (CdU34 a CdU42)
# ==============================================================================
@router.get("/bandeja-agrupada", status_code=status.HTTP_200_OK)
def obtener_bandeja_agrupada(
    filtro: Optional[str] = Query("activos", pattern="^(activos|archivados|bloqueados)$"),
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_obtener_bandeja_agrupada",
            {"p_usuario_id": user_id, "p_filtro": filtro}
        ).execute()
        return rpc_res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/iniciar", status_code=status.HTTP_201_CREATED)
def iniciar_chat(datos: IniciarChatInput, user_id: str = Depends(get_current_user_id)):
    texto = datos.mensaje_inicial.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
    try:
        rpc_res = supabase.rpc(
            "fn_iniciar_chat_negociacion",
            {"p_publicacion_id": datos.publicacion_id, "p_comprador_id": user_id, "p_mensaje_inicial": texto}
        ).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{sala_id}/mensajes", status_code=status.HTTP_201_CREATED)
def enviar_mensaje(sala_id: str, datos: EnviarMensajeInput, user_id: str = Depends(get_current_user_id)):
    texto = datos.contenido.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
    try:
        rpc_res = supabase.rpc(
            "fn_enviar_mensaje_chat",
            {"p_sala_id": sala_id, "p_emisor_id": user_id, "p_contenido": texto}
        ).execute()
        return rpc_res.data
    except Exception as e:
        err = str(e)
        if "bloqueada" in err:
            raise HTTPException(status_code=403, detail="La interacción con este comerciante está bloqueada.")
        raise HTTPException(status_code=500, detail=err)

@router.get("/{sala_id}/detalle", status_code=status.HTTP_200_OK)
def obtener_detalle(sala_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc(
            "fn_acceder_sala_chat_especifica",
            {"p_sala_id": sala_id, "p_usuario_id": user_id}
        ).execute()
        data = rpc_res.data
        if not data:
            raise HTTPException(status_code=404, detail="Sala no encontrada.")
        
        bloq_res = supabase.table("comerciantes_bloqueados")\
            .select("id")\
            .eq("bloqueador_id", user_id)\
            .eq("bloqueado_id", data["contraparte_id"])\
            .execute()
        data["bloqueado_por_mi"] = bool(bloq_res.data)
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sala_id}/marcar-leido", status_code=status.HTTP_200_OK)
def marcar_leido(sala_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc("fn_marcar_chat_leido", {"p_sala_id": sala_id, "p_usuario_id": user_id}).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sala_id}/archivar", status_code=status.HTTP_200_OK)
def archivar(sala_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc("fn_archivar_chat", {"p_sala_id": sala_id, "p_usuario_id": user_id}).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{sala_id}/desarchivar", status_code=status.HTTP_200_OK)
def desarchivar(sala_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc("fn_desarchivar_chat", {"p_sala_id": sala_id, "p_usuario_id": user_id}).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comerciantes/{comerciante_id}/archivar-todos", status_code=status.HTTP_200_OK)
def archivar_todos_chats_comerciante(comerciante_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc(
            "fn_archivar_todos_chats_comerciante",
            {"p_usuario_id": user_id, "p_contraparte_id": comerciante_id}
        ).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comerciantes/{comerciante_id}/desarchivar-todos", status_code=status.HTTP_200_OK)
def desarchivar_todos_chats_comerciante(comerciante_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc(
            "fn_desarchivar_todos_chats_comerciante",
            {"p_usuario_id": user_id, "p_contraparte_id": comerciante_id}
        ).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comerciantes/{comerciante_id}/bloquear", status_code=status.HTTP_200_OK)
def bloquear_comerciante_global(comerciante_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc(
            "fn_bloquear_comerciante",
            {"p_bloqueador_id": user_id, "p_bloqueado_id": comerciante_id}
        ).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/comerciantes/{comerciante_id}/desbloquear", status_code=status.HTTP_200_OK)
def desbloquear_comerciante_global(comerciante_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        rpc_res = supabase.rpc(
            "fn_desbloquear_comerciante",
            {"p_bloqueador_id": user_id, "p_bloqueado_id": comerciante_id}
        ).execute()
        return rpc_res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))