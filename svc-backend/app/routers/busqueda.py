from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional
from app.schemas.busqueda_schema import BusquedaComerciantesResponse
from app.core.security import get_current_user_id
from app.db.supabase_client import supabase

router = APIRouter(prefix="/busqueda", tags=["Motor de Búsqueda y Filtrado Comercial (Sprint 3 / CdU10, CdU11, CdU12)"])

@router.get(
    "/comerciantes",
    response_model=BusquedaComerciantesResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar y filtrar comerciantes por texto, rubro, locación y alcance logístico (CdU10, CdU11, CdU12)"
)
def buscar_y_filtrar_comerciantes(
    q: Optional[str] = Query(None, description="Término o palabra clave textual (CdU10)"),
    rubro: Optional[str] = Query(None, description="Rubro comercial principal (CdU11)"),
    subrubro: Optional[str] = Query(None, description="Subrubro comercial específico (CdU11)"),
    provincia: Optional[str] = Query(None, description="Provincia geográfica del comercio (CdU12)"),
    ciudad: Optional[str] = Query(None, description="Ciudad o localidad del comercio (CdU12)"),
    alcance: Optional[str] = Query(None, description="Zona de alcance logístico declarada: Regional, Nacional, Internacional (CdU12)"),
    pagina: int = Query(1, ge=1, description="Número de página para paginación"),
    limite: int = Query(12, ge=1, le=50, description="Cantidad de registros por página"),
    user_id: str = Depends(get_current_user_id)
):
    """
    CdU10: Búsqueda de Comerciantes.
    CdU11: Filtrar comerciantes por rubro.
    CdU12: Filtrar comerciantes por locación y zonas de alcance.
    Permite combinar búsqueda libre con filtros taxonómicos y geográficos sobre perfiles comerciales activos.
    Excluye estrictamente cuentas en estado 'inhabilitado' o 'baja'.
    """
    # 1. Validar que el usuario que consulta esté autenticado y en estado 'activo'
    verificar_usuario = (
        supabase.table("comerciantes")
        .select("id, estado")
        .eq("id", user_id)
        .execute()
    )
    if not verificar_usuario.data or verificar_usuario.data[0].get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Su cuenta comercial no se encuentra autorizada o activa para operar en la red."
        )

    # 2. Sanitización y limpieza de parámetros de consulta
    termino_limpio = q.strip() if q else None
    rubro_limpio = rubro.strip() if rubro and rubro != "todos" else None
    subrubro_limpio = subrubro.strip() if subrubro and subrubro != "todos" else None
    provincia_limpia = provincia.strip() if provincia and provincia != "todos" else None
    ciudad_limpia = ciudad.strip() if ciudad else None
    alcance_limpio = alcance.strip() if alcance and alcance != "todos" else None

    # Flujo alterno CdU12: Validar formato de alcance logístico si fue provisto
    if alcance_limpio and alcance_limpio not in ["Regional", "Nacional", "Internacional"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zona de alcance logístico inválida. Opciones válidas: Regional, Nacional, Internacional."
        )

    # Validar que al menos un parámetro de filtro o búsqueda esté presente
    if not any([termino_limpio, rubro_limpio, provincia_limpia, ciudad_limpia, alcance_limpio]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe ingresar un término de búsqueda o seleccionar al menos un criterio de filtrado."
        )

    # 3. Paginación
    offset = (pagina - 1) * limite

    try:
        # 4. Construcción dinámica de la consulta sobre perfiles activos
        query = (
            supabase.table("comerciantes")
            .select(
                "id, nombre_razon_social, cuit_cuil, rubro_comercial, subrubro_comercial, "
                "direccion, provincia, ciudad_localidad, zona_alcance_logistico, telefono, email, creado_el",
                count="exact"
            )
            .eq("estado", "activo")
        )

        # CdU11: Taxonomía comercial
        if rubro_limpio:
            query = query.eq("rubro_comercial", rubro_limpio)
        if subrubro_limpio:
            query = query.eq("subrubro_comercial", subrubro_limpio)

        # CdU12: Locación y alcance logístico
        if provincia_limpia:
            query = query.ilike("provincia", f"%{provincia_limpia}%")
        if ciudad_limpia:
            query = query.ilike("ciudad_localidad", f"%{ciudad_limpia}%")
        if alcance_limpio:
            query = query.eq("zona_alcance_logistico", alcance_limpio)

        # CdU10: Coincidencia textual libre concurrente
        if termino_limpio:
            filtro_or = (
                f"nombre_razon_social.ilike.%{termino_limpio}%,"
                f"cuit_cuil.ilike.%{termino_limpio}%,"
                f"direccion.ilike.%{termino_limpio}%"
            )
            query = query.or_(filtro_or)

        # Ordenamiento alfabético por razón social y paginación
        query_res = (
            query.order("nombre_razon_social", desc=False)
            .range(offset, offset + limite - 1)
            .execute()
        )

        total = query_res.count if query_res.count is not None else len(query_res.data or [])
        datos_coincidentes = query_res.data or []

        return {
            "termino_busqueda": termino_limpio,
            "rubro_filtro": rubro_limpio,
            "subrubro_filtro": subrubro_limpio,
            "provincia_filtro": provincia_limpia,
            "ciudad_filtro": ciudad_limpia,
            "alcance_filtro": alcance_limpio,
            "total_coincidencias": total,
            "pagina": pagina,
            "limite": limite,
            "resultados": datos_coincidentes
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar la búsqueda y filtrado de comerciantes: {str(e)}"
        )