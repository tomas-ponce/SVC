from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.core.security import get_current_user_id
from app.db.supabase_client import supabase

router = APIRouter(prefix="/calificaciones", tags=["Reputación y Reseñas B2B (Sprint 6)"])

# ==============================================================================
# Modelos de Entrada (Pydantic DTOs)
# ==============================================================================
class CalificarPublicacionInput(BaseModel):
    transaccion_id: str = Field(..., description="UUID de la transacción comercial formalizada")
    puntaje: int = Field(..., ge=1, le=5, description="Puntaje de 1 a 5 estrellas")
    comentario: Optional[str] = Field("", max_length=1000, description="Comentario o reseña de calidad")

class CalificarComercianteInput(BaseModel):
    transaccion_id: str = Field(..., description="UUID de la transacción comercial formalizada")
    puntaje: int = Field(..., ge=1, le=5, description="Puntaje de 1 a 5 estrellas")
    comentario: Optional[str] = Field("", max_length=1000, description="Comentario sobre la experiencia comercial")

# ==============================================================================
# CdU58: Calificar publicación de venta adquirida
# ==============================================================================
@router.post("/publicacion", status_code=status.HTTP_201_CREATED, summary="Calificar publicación adquirida (CdU58)")
def calificar_publicacion(
    datos: CalificarPublicacionInput,
    user_id: str = Depends(get_current_user_id)
):
    """
    Permite al comprador evaluar la publicación/producto adquirido en una orden formalizada abonada.
    """
    try:
        # 1. Verificar transacción comercial
        res_t = supabase.table("transacciones_comerciales").select("*").eq("id", datos.transaccion_id).execute()
        if not res_t.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción comercial no encontrada.")
        
        t = res_t.data[0]

        # 2. Validar que el usuario sea el comprador de la orden (RBAC / Integridad)
        if t["comprador_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el comprador de la orden comercial tiene autorización para calificar el producto adquirido."
            )

        # 3. Validar estado comercial de la transacción
        if t["estado"] not in ["Abonada", "Completada", "Entregada", "Finalizada"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La transacción debe encontrarse 'Abonada' para emitir una calificación (Estado actual: {t['estado']})."
            )

        # 4. Validar unicidad (no calificar más de una vez la misma orden)
        res_existente = supabase.table("calificaciones_publicaciones").select("id").eq("transaccion_id", datos.transaccion_id).execute()
        if res_existente.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya ha registrado una valoración para esta publicación en la transacción especificada."
            )

        # 5. Insertar calificación
        payload = {
            "transaccion_id": datos.transaccion_id,
            "publicacion_id": t["publicacion_id"],
            "comprador_id": user_id,
            "puntaje": datos.puntaje,
            "comentario": (datos.comentario or "").strip()
        }

        res_ins = supabase.table("calificaciones_publicaciones").insert(payload).execute()
        calificacion_creada = res_ins.data[0] if res_ins.data else payload

        # 6. Notificación asíncrona no bloqueante al vendedor
        try:
            supabase.table("notificaciones").insert({
                "comerciante_id": t["vendedor_id"],
                "tipo": "mensaje_chat",
                "titulo": "Nueva Calificación de Producto",
                "mensaje": f"El comprador calificó con {datos.puntaje} estrellas tu publicación '{t.get('titulo_congelado', 'producto')}'.",
                "origen_tipo": "transaccion",
                "origen_id": datos.transaccion_id,
                "uri_destino": "historial-transacciones.html",
                "leida": False
            }).execute()
        except Exception as notif_err:
            print(f"[WARN CdU58] Notificación calificación: {notif_err}")

        return {
            "mensaje": "Calificación de publicación registrada exitosamente.",
            "calificacion": calificacion_creada
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al calificar publicación: {str(e)}")

# ==============================================================================
# CdU59: Calificar contraparte comercial
# ==============================================================================
@router.post("/comerciante", status_code=status.HTTP_201_CREATED, summary="Calificar contraparte comercial (CdU59)")
def calificar_contraparte(
    datos: CalificarComercianteInput,
    user_id: str = Depends(get_current_user_id)
):
    """
    Permite al comprador calificar al vendedor o al vendedor calificar al comprador
    tras una transacción formalizada abonada.
    """
    try:
        # 1. Recuperar la transacción
        res_t = supabase.table("transacciones_comerciales").select("*").eq("id", datos.transaccion_id).execute()
        if not res_t.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción comercial no encontrada.")
        
        t = res_t.data[0]

        # 2. Validar que el usuario sea parte del acuerdo comercial
        es_comprador = (t["comprador_id"] == user_id)
        es_vendedor = (t["vendedor_id"] == user_id)

        if not (es_comprador or es_vendedor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo las partes involucradas en la transacción pueden evaluar a su contraparte."
            )

        # 3. Validar estado comercial
        if t["estado"] not in ["Abonada", "Completada", "Entregada", "Finalizada"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La transacción debe encontrarse 'Abonada' para calificar a la contraparte (Estado actual: {t['estado']})."
            )

        rol_calificador = "comprador" if es_comprador else "vendedor"
        calificado_id = t["vendedor_id"] if es_comprador else t["comprador_id"]

        # 4. Validar unicidad (una sola calificación por contraparte por orden)
        res_existente = supabase.table("calificaciones_comerciantes")\
            .select("id")\
            .eq("transaccion_id", datos.transaccion_id)\
            .eq("calificador_id", user_id)\
            .execute()

        if res_existente.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya ha registrado una calificación para la contraparte en esta transacción comercial."
            )

        # 5. Insertar calificación
        payload = {
            "transaccion_id": datos.transaccion_id,
            "calificador_id": user_id,
            "calificado_id": calificado_id,
            "rol_calificador": rol_calificador,
            "puntaje": datos.puntaje,
            "comentario": (datos.comentario or "").strip()
        }

        res_ins = supabase.table("calificaciones_comerciantes").insert(payload).execute()
        calificacion_creada = res_ins.data[0] if res_ins.data else payload

        # 6. Notificación asíncrona a la contraparte
        try:
            supabase.table("notificaciones").insert({
                "comerciante_id": calificado_id,
                "tipo": "mensaje_chat",
                "titulo": "Nueva Reseña de Reputación Comercial",
                "mensaje": f"Has recibido una valoración de {datos.puntaje} estrellas por la orden #{datos.transaccion_id[:8]}.",
                "origen_tipo": "transaccion",
                "origen_id": datos.transaccion_id,
                "uri_destino": "ver-perfil.html",
                "leida": False
            }).execute()
        except Exception as notif_err:
            print(f"[WARN CdU59] Notificación contraparte: {notif_err}")

        return {
            "mensaje": "Calificación a la contraparte registrada con éxito.",
            "calificacion": calificacion_creada
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al calificar contraparte: {str(e)}")

# ==============================================================================
# CdU60: Consultar reputación y reseñas de un comerciante
# ==============================================================================
@router.get("/comerciante/{comerciante_id}", status_code=status.HTTP_200_OK, summary="Consultar reputación de un comerciante (CdU60)")
def consultar_reputacion_comerciante(comerciante_id: str):
    """
    Retorna métricas agregadas de reputación (promedio, distribución de estrellas)
    y el listado de reseñas recibidas por el comerciante.
    """
    try:
        # 1. Consultar reseñas recibidas
        res = supabase.table("calificaciones_comerciantes")\
            .select("*")\
            .eq("calificado_id", comerciante_id)\
            .order("creado_el", desc=True)\
            .execute()

        resenas = res.data or []
        total = len(resenas)

        # 2. Calcular agregaciones
        desglose = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        suma_puntos = 0

        for r in resenas:
            p = r.get("puntaje", 0)
            if 1 <= p <= 5:
                desglose[p] += 1
                suma_puntos += p

        promedio = round(suma_puntos / total, 1) if total > 0 else 0.0

        # 3. Enriquecer con nombres de emisores (calificadores)
        calificadores_ids = list(set(r["calificador_id"] for r in resenas if "calificador_id" in r))
        calificadores_map = {}
        if calificadores_ids:
            res_users = supabase.table("comerciantes")\
                .select("id, nombre_razon_social, ciudad_localidad, provincia")\
                .in_("id", calificadores_ids)\
                .execute()
            calificadores_map = {u["id"]: u for u in (res_users.data or [])}

        lista_enriquecida = []
        for r in resenas:
            r_copy = dict(r)
            r_copy["emisor"] = calificadores_map.get(r["calificador_id"], {
                "nombre_razon_social": "Comerciante Anónimo"
            })
            lista_enriquecida.append(r_copy)

        return {
            "comerciante_id": comerciante_id,
            "total_resenas": total,
            "promedio": promedio,
            "desglose": desglose,
            "resenas": lista_enriquecida
        }
    except Exception as e:
        print(f"[WARN CdU60] Error al obtener reputación de comerciante {comerciante_id}: {e}")
        return {
            "comerciante_id": comerciante_id,
            "total_resenas": 0,
            "promedio": 0.0,
            "desglose": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "resenas": []
        }

# ==============================================================================
# CdU61: Consultar valoraciones de una publicación
# ==============================================================================
@router.get("/publicacion/{publicacion_id}", status_code=status.HTTP_200_OK, summary="Consultar valoraciones de una publicación (CdU61)")
def consultar_valoraciones_publicacion(publicacion_id: str):
    """
    Retorna métricas y opiniones de compradores sobre una publicación de venta.
    """
    try:
        res = supabase.table("calificaciones_publicaciones")\
            .select("*")\
            .eq("publicacion_id", publicacion_id)\
            .order("creado_el", desc=True)\
            .execute()

        resenas = res.data or []
        total = len(resenas)

        desglose = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        suma_puntos = 0

        for r in resenas:
            p = r.get("puntaje", 0)
            if 1 <= p <= 5:
                desglose[p] += 1
                suma_puntos += p

        promedio = round(suma_puntos / total, 1) if total > 0 else 0.0

        compradores_ids = list(set(r["comprador_id"] for r in resenas if "comprador_id" in r))
        compradores_map = {}
        if compradores_ids:
            res_users = supabase.table("comerciantes")\
                .select("id, nombre_razon_social")\
                .in_("id", compradores_ids)\
                .execute()
            compradores_map = {u["id"]: u for u in (res_users.data or [])}

        lista_enriquecida = []
        for r in resenas:
            r_copy = dict(r)
            r_copy["comprador"] = compradores_map.get(r["comprador_id"], {
                "nombre_razon_social": "Comprador Verificado"
            })
            lista_enriquecida.append(r_copy)

        return {
            "publicacion_id": publicacion_id,
            "total_resenas": total,
            "promedio": promedio,
            "desglose": desglose,
            "resenas": lista_enriquecida
        }
    except Exception as e:
        print(f"[WARN CdU61] Error al obtener valoraciones de publicación {publicacion_id}: {e}")
        return {
            "publicacion_id": publicacion_id,
            "total_resenas": 0,
            "promedio": 0.0,
            "desglose": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "resenas": []
        }

# ==============================================================================
# Helper: Consultar estado de calificación de una orden específica
# ==============================================================================
@router.get("/transaccion/{transaccion_id}/estado", status_code=status.HTTP_200_OK, summary="Estado de calificación de una transacción")
def consultar_estado_calificaciones_transaccion(
    transaccion_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Informa si el usuario actual ya emitió la calificación de producto y/o contraparte para habilitar botones en el frontend.
    """
    try:
        res_t = supabase.table("transacciones_comerciales").select("*").eq("id", transaccion_id).execute()
        if not res_t.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada.")

        t = res_t.data[0]
        es_comprador = (t["comprador_id"] == user_id)
        es_vendedor = (t["vendedor_id"] == user_id)

        califico_publicacion = False
        if es_comprador:
            chk_pub = supabase.table("calificaciones_publicaciones").select("id").eq("transaccion_id", transaccion_id).execute()
            califico_publicacion = bool(chk_pub.data)

        chk_com = supabase.table("calificaciones_comerciantes")\
            .select("id")\
            .eq("transaccion_id", transaccion_id)\
            .eq("calificador_id", user_id)\
            .execute()
        califico_contraparte = bool(chk_com.data)

        return {
            "transaccion_id": transaccion_id,
            "es_comprador": es_comprador,
            "es_vendedor": es_vendedor,
            "estado_orden": t["estado"],
            "califico_publicacion": califico_publicacion,
            "califico_contraparte": califico_contraparte,
            "puede_calificar": (t["estado"] in ["Abonada", "Completada", "Entregada", "Finalizada"])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al verificar estado: {str(e)}")
