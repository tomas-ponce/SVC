from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ==============================================================================
# ESQUEMAS PARA BÚSQUEDA Y FILTRADO COMERCIAL (CdU10 / CdU11 / CdU12)
# ==============================================================================

class ComercianteBusquedaItem(BaseModel):
    id: str
    nombre_razon_social: str
    cuit_cuil: str
    rubro_comercial: str
    subrubro_comercial: Optional[str] = None
    direccion: str
    provincia: str
    ciudad_localidad: str
    zona_alcance_logistico: str
    telefono: str
    email: str
    creado_el: datetime

class BusquedaComerciantesResponse(BaseModel):
    termino_busqueda: Optional[str] = None
    rubro_filtro: Optional[str] = None
    subrubro_filtro: Optional[str] = None
    provincia_filtro: Optional[str] = None
    ciudad_filtro: Optional[str] = None
    alcance_filtro: Optional[str] = None
    total_coincidencias: int
    pagina: int
    limite: int
    resultados: List[ComercianteBusquedaItem]