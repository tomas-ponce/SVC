from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from app.schemas.publicacion_schema import (
    PublicacionVentaCreate, 
    PublicacionVentaUpdate, 
    EliminarPublicacionAdminInput,
    PublicacionVentaResponse,
    PublicacionDetalleCompletoResponse
)
from app.core.security import get_current_user_id, get_current_admin
from app.core.email_service import (
    enviar_correo_alerta_bajo_stock,
    enviar_correo_eliminacion_publicacion_admin
)
from app.db.supabase_client import supabase

router = APIRouter(prefix="/publicaciones", tags=["Gestión de Publicaciones de Venta (Sprint 3)"])

# ==============================================================================
# 1. CdU25 / CdU26 - CREAR PUBLICACIÓN CON DEDUCCIÓN ATÓMICA DE STOCK
# ==============================================================================
@router.post(
    "/nueva",
    response_model=PublicacionVentaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear publicación de venta con deducción atómica de inventario (CdU25 / CdU26)"
)
def crear_publicacion_venta(
    datos: PublicacionVentaCreate,
    user_id: str = Depends(get_current_user_id)
):
    com_res = supabase.table("comerciantes").select("*").eq("id", user_id).execute()
    if not com_res.data or com_res.data[0].get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los comerciantes con cuenta activa pueden publicar ofertas de venta."
        )
    comercio = com_res.data[0]

    item_actual = None
    stock_anterior = None
    nuevo_stock = None
    estado_anterior = None
    nuevo_estado = None

    if datos.inventario_item_id:
        item_res = (
            supabase.table("inventario_items")
            .select("*")
            .eq("id", datos.inventario_item_id)
            .eq("comerciante_id", user_id)
            .execute()
        )
        if not item_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El ítem de inventario seleccionado no existe o no pertenece a su catálogo comercial."
            )

        item_actual = item_res.data[0]
        stock_anterior = int(item_actual.get("stock_actual", 0))
        estado_anterior = item_actual.get("estado", "disponible")

        if datos.unidades_ofertadas > stock_anterior:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Disponible: {stock_anterior} unidades. Solicitadas: {datos.unidades_ofertadas}."
            )

        nuevo_stock = stock_anterior - datos.unidades_ofertadas
        umbral_alerta = int(item_actual.get("stock_minimo_alerta", 0))

        if nuevo_stock == 0:
            nuevo_estado = "sin_stock"
        elif nuevo_stock <= umbral_alerta:
            nuevo_estado = "bajo_stock"
        else:
            nuevo_estado = "disponible"

        upd_item = (
            supabase.table("inventario_items")
            .update({
                "stock_actual": nuevo_stock,
                "estado": nuevo_estado,
                "actualizado_el": "now()"
            })
            .eq("id", datos.inventario_item_id)
            .execute()
        )
        if not upd_item.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al procesar el descuento de existencias en el inventario."
            )

    rubro_final = datos.rubro.strip() if datos.rubro else comercio.get("rubro_comercial")
    subrubro_final = datos.subrubro.strip() if datos.subrubro else comercio.get("subrubro_comercial")

    nueva_publicacion = {
        "comerciante_id": user_id,
        "inventario_item_id": datos.inventario_item_id,
        "titulo": datos.titulo.strip(),
        "descripcion": datos.descripcion.strip() if datos.descripcion else None,
        "precio": datos.precio,
        "origen": datos.origen.strip(),
        "rubro": rubro_final,
        "subrubro": subrubro_final,
        "unidades_ofertadas": datos.unidades_ofertadas,
        "estado": "Activa"
    }

    try:
        pub_res = supabase.table("publicaciones_venta").insert(nueva_publicacion).execute()
        if not pub_res.data:
            raise Exception("No se obtuvieron registros tras la inserción.")
    except Exception as e:
        if datos.inventario_item_id and stock_anterior is not None:
            supabase.table("inventario_items").update({
                "stock_actual": stock_anterior,
                "estado": estado_anterior,
                "actualizado_el": "now()"
            }).eq("id", datos.inventario_item_id).execute()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al registrar la publicación de venta: {str(e)}"
        )

    if datos.inventario_item_id:
        try:
            supabase.table("inventario_ajustes_log").insert({
                "item_id": datos.inventario_item_id,
                "comerciante_id": user_id,
                "tipo_movimiento": "egreso",
                "cantidad": datos.unidades_ofertadas,
                "stock_anterior": stock_anterior,
                "stock_nuevo": nuevo_stock,
                "motivo": f"Deducción por publicación de oferta: '{datos.titulo}'"
            }).execute()
        except Exception:
            pass

        if nuevo_estado in ["bajo_stock", "sin_stock"] and estado_anterior == "disponible":
            try:
                enviar_correo_alerta_bajo_stock(
                    destinatario=comercio["email"],
                    razon_social=comercio.get("nombre_razon_social", "Comercio"),
                    nombre_producto=item_actual["nombre"],
                    stock_actual=nuevo_stock,
                    stock_minimo=item_actual.get("stock_minimo_alerta", 0)
                )
            except Exception as mail_err:
                print(f"[SMTP WARN] No se pudo despachar el correo de alerta: {mail_err}")

    return pub_res.data[0]

# ==============================================================================
# 2. LISTAR PUBLICACIONES DEL COMERCIANTE AUTENTICADO
# ==============================================================================
@router.get(
    "/mis-publicaciones",
    response_model=List[PublicacionVentaResponse],
    summary="Listar las publicaciones de venta creadas por el comerciante autenticado"
)
def listar_mis_publicaciones(user_id: str = Depends(get_current_user_id)):
    res = (
        supabase.table("publicaciones_venta")
        .select("*")
        .eq("comerciante_id", user_id)
        .neq("estado", "Eliminada")
        .order("creado_el", desc=True)
        .execute()
    )
    return res.data or []

# ==============================================================================
# 3. LISTAR PUBLICACIONES PARA MODERACIÓN ADMINISTRATIVA (CdU32)
# ==============================================================================
@router.get(
    "/admin/todas",
    summary="Listar todas las ofertas de la plataforma para moderación (CdU32)"
)
def listar_publicaciones_admin(
    estado: Optional[str] = "Activa",
    admin: dict = Depends(get_current_admin)
):
    query = (
        supabase.table("publicaciones_venta")
        .select("id, comerciante_id, titulo, descripcion, precio, rubro, unidades_ofertadas, estado, creado_el, comerciantes(nombre_razon_social, email, cuit_cuil)")
        .neq("estado", "Eliminada")
        .order("creado_el", desc=True)
    )
    if estado and estado != "todos":
        query = query.eq("estado", estado)

    res = query.execute()
    return res.data or []

# ==============================================================================
# 4. CdU33 - VISUALIZAR DETALLES COMPLETOS DE UNA PUBLICACIÓN
# ==============================================================================
@router.get(
    "/{publicacion_id}/detalle",
    response_model=PublicacionDetalleCompletoResponse,
    status_code=status.HTTP_200_OK,
    summary="Visualizar detalles completos de una oferta y datos de contacto comercial (CdU33)"
)
def obtener_detalle_publicacion(
    publicacion_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    CdU33: Visualizar detalles completos de una publicación.
    Devuelve la ficha comercial de la oferta y los datos del vendedor.
    Determina si el usuario autenticado es el autor para la regla de negociación.
    """
    pub_res = (
        supabase.table("publicaciones_venta")
        .select("*, comerciantes(*)")
        .eq("id", publicacion_id)
        .execute()
    )
    if not pub_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La publicación solicitada no existe o no se encuentra disponible."
        )

    pub = pub_res.data[0]

    # No permitir ver ofertas eliminadas
    if pub.get("estado") == "Eliminada":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esta publicación de venta ha sido retirada de la plataforma."
        )

    vendedor_data = pub.get("comerciantes") or {}

    return {
        "id": pub["id"],
        "comerciante_id": pub["comerciante_id"],
        "inventario_item_id": pub.get("inventario_item_id"),
        "titulo": pub["titulo"],
        "descripcion": pub.get("descripcion"),
        "precio": pub["precio"],
        "origen": pub["origen"],
        "rubro": pub["rubro"],
        "subrubro": pub.get("subrubro"),
        "unidades_ofertadas": pub["unidades_ofertadas"],
        "estado": pub["estado"],
        "creado_el": pub["creado_el"],
        "actualizado_el": pub["actualizado_el"],
        "es_autor": (pub["comerciante_id"] == user_id),
        "vendedor": {
            "id": vendedor_data.get("id", pub["comerciante_id"]),
            "nombre_razon_social": vendedor_data.get("nombre_razon_social", "Comercio Registrado"),
            "cuit_cuil": vendedor_data.get("cuit_cuil", "—"),
            "telefono": vendedor_data.get("telefono", "—"),
            "email": vendedor_data.get("email", "—"),
            "direccion": vendedor_data.get("direccion", "—"),
            "ciudad_localidad": vendedor_data.get("ciudad_localidad", "—"),
            "provincia": vendedor_data.get("provincia", "—"),
            "zona_alcance_logistico": vendedor_data.get("zona_alcance_logistico", "Regional")
        }
    }

# ==============================================================================
# 5. CdU27 - EDITAR INFORMACIÓN DE PUBLICACIÓN Y CONCILIAR STOCK
# ==============================================================================
@router.put(
    "/{publicacion_id}",
    status_code=status.HTTP_200_OK,
    summary="Modificar atributos y conciliar stock de publicación existente (CdU27)"
)
def editar_publicacion_venta(
    publicacion_id: str,
    datos: PublicacionVentaUpdate,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_editar_publicacion_con_stock",
            {
                "p_publicacion_id": publicacion_id,
                "p_comerciante_id": user_id,
                "p_titulo": datos.titulo.strip(),
                "p_descripcion": datos.descripcion.strip() if datos.descripcion else None,
                "p_precio": datos.precio,
                "p_origen": datos.origen.strip(),
                "p_rubro": datos.rubro.strip(),
                "p_subrubro": datos.subrubro.strip() if datos.subrubro else None,
                "p_unidades_nuevas": datos.unidades_ofertadas
            }
        ).execute()

        return rpc_res.data

    except Exception as e:
        err_msg = str(e)
        if "Stock insuficiente en inventario" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )
        if "No es posible editar una publicación que ha sido eliminada" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No es posible editar una oferta eliminada."
            )
        if "La publicación no existe o no pertenece" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada o no posee permisos para modificarla."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al actualizar la publicación de venta: {err_msg}"
        )

# ==============================================================================
# 6. CdU28 / CdU30 - PAUSAR PUBLICACIÓN Y RESTITUIR STOCK AL INVENTARIO
# ==============================================================================
@router.put(
    "/{publicacion_id}/pausar",
    status_code=status.HTTP_200_OK,
    summary="Pausar publicación de venta y devolver unidades a inventario (CdU28 / CdU30)"
)
def pausar_publicacion_venta(
    publicacion_id: str,
    user_id: str = Depends(get_current_user_id)
):
    pub_res = (
        supabase.table("publicaciones_venta")
        .select("id, inventario_item_id, unidades_ofertadas, estado, titulo")
        .eq("id", publicacion_id)
        .eq("comerciante_id", user_id)
        .execute()
    )
    if not pub_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada o no posee permisos para pausarla."
        )

    publicacion = pub_res.data[0]

    if publicacion["estado"] == "Pausada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La publicación ya se encuentra pausada."
        )

    if publicacion["estado"] == "Eliminada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No es posible pausar una publicación eliminada."
        )

    unidades_restituidas = 0

    if publicacion.get("inventario_item_id"):
        try:
            rpc_res = supabase.rpc(
                "fn_devolver_stock_inventario",
                {
                    "p_item_id": publicacion["inventario_item_id"],
                    "p_comerciante_id": user_id,
                    "p_cantidad": publicacion["unidades_ofertadas"],
                    "p_motivo": f"Devolución por pausa de oferta: {publicacion['titulo']}"
                }
            ).execute()

            if rpc_res.data and rpc_res.data.get("exito"):
                unidades_restituidas = rpc_res.data.get("unidades_restituidas", 0)
        except Exception as e:
            print(f"[WARN CdU30] Error restituyendo inventario: {str(e)}")

    upd_res = (
        supabase.table("publicaciones_venta")
        .update({
            "estado": "Pausada",
            "actualizado_el": "now()"
        })
        .eq("id", publicacion_id)
        .eq("comerciante_id", user_id)
        .execute()
    )

    if not upd_res.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el estado de la publicación en la base de datos."
        )

    return {
        "mensaje": f"Publicación '{publicacion['titulo']}' pausada exitosamente.",
        "estado": "Pausada",
        "unidades_restituidas": unidades_restituidas,
        "publicacion_id": publicacion_id
    }

# ==============================================================================
# 7. CdU29 / CdU26 - REACTIVAR PUBLICACIÓN DE VENTA CON RESERVA DE STOCK
# ==============================================================================
@router.put(
    "/{publicacion_id}/reactivar",
    status_code=status.HTTP_200_OK,
    summary="Reactivar publicación de venta validando y reservando stock (CdU29 / CdU26)"
)
def reactivar_publicacion_venta(
    publicacion_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_reactivar_publicacion_con_stock",
            {
                "p_publicacion_id": publicacion_id,
                "p_comerciante_id": user_id
            }
        ).execute()

        resultado = rpc_res.data
        return {
            "mensaje": f"Publicación '{resultado.get('titulo')}' reactivada exitosamente en la red B2B.",
            "estado": "Activa",
            "unidades_reservadas": resultado.get("unidades_reservadas", 0),
            "publicacion_id": publicacion_id
        }
    except Exception as e:
        err_msg = str(e)
        if "Stock insuficiente en inventario para reactivar" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=err_msg
            )
        if "ya se encuentra activa" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La publicación ya se encuentra activa."
            )
        if "ya no existe en su catálogo" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ítem de inventario vinculado a esta oferta fue eliminado previamente."
            )
        if "no existe o no pertenece" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada o no posee permisos para modificarla."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reactivar la publicación: {err_msg}"
        )

# ==============================================================================
# 8. CdU31 / CdU30 - ELIMINAR PUBLICACIÓN DE VENTA POR AUTOR
# ==============================================================================
@router.delete(
    "/{publicacion_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar publicación de venta por autor con restitución de stock (CdU31 / CdU30)"
)
def eliminar_publicacion_por_autor(
    publicacion_id: str,
    user_id: str = Depends(get_current_user_id)
):
    try:
        rpc_res = supabase.rpc(
            "fn_eliminar_publicacion_autor",
            {
                "p_publicacion_id": publicacion_id,
                "p_comerciante_id": user_id
            }
        ).execute()

        resultado = rpc_res.data
        return {
            "mensaje": f"Publicación '{resultado.get('titulo')}' eliminada permanentemente.",
            "estado": "Eliminada",
            "unidades_restituidas": resultado.get("unidades_restituidas", 0),
            "publicacion_id": publicacion_id
        }
    except Exception as e:
        err_msg = str(e)
        if "ya ha sido eliminada previamente" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La publicación ya se encuentra eliminada."
            )
        if "no existe o no pertenece" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicación no encontrada o no posee permisos para eliminarla."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la eliminación de la oferta: {err_msg}"
        )

# ==============================================================================
# 9. CdU32 / CdU30 - ELIMINAR PUBLICACIÓN DE VENTA POR ADMINISTRADOR (MODERACIÓN)
# ==============================================================================
@router.delete(
    "/{publicacion_id}/admin",
    status_code=status.HTTP_200_OK,
    summary="Baja forzosa de oferta por Administrador con justificación y auditoría (CdU32 / CdU30)"
)
def eliminar_publicacion_por_administrador(
    publicacion_id: str,
    datos: EliminarPublicacionAdminInput,
    admin: dict = Depends(get_current_admin)
):
    admin_id = admin["id"]

    try:
        rpc_res = supabase.rpc(
            "fn_eliminar_publicacion_admin",
            {
                "p_publicacion_id": publicacion_id,
                "p_admin_id": admin_id,
                "p_justificacion": datos.motivo_infraccion.strip()
            }
        ).execute()

        res_data = rpc_res.data

        if res_data and res_data.get("comerciante_email"):
            try:
                enviar_correo_eliminacion_publicacion_admin(
                    destinatario=res_data["comerciante_email"],
                    razon_social=res_data.get("comerciante_nombre") or "Comercio Registrado",
                    titulo_publicacion=res_data.get("titulo"),
                    motivo=datos.motivo_infraccion.strip()
                )
            except Exception as mail_err:
                print(f"[SMTP WARN CdU32] Error despachando correo de moderación: {mail_err}")

        return {
            "mensaje": f"Publicación '{res_data.get('titulo')}' dada de baja por moderación administrativa.",
            "estado": "Eliminada",
            "unidades_restituidas": res_data.get("unidades_restituidas", 0),
            "publicacion_id": publicacion_id
        }

    except Exception as e:
        err_msg = str(e)
        if "justificación institucional es obligatoria" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe ingresar una justificación formal para la baja (mínimo 5 caracteres)."
            )
        if "privilegios de Administrador" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado: Se requieren privilegios de Administrador Global."
            )
        if "no existe o ya fue destruida" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La publicación solicitada no existe."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar la baja administrativa: {err_msg}"
        )