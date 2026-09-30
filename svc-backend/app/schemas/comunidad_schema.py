from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ==============================================================================
# ESQUEMAS PARA GESTIÓN DE COMUNIDADES (CdU13 a CdU24)
# ==============================================================================

class ComunidadCreateInput(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150, description="Nombre único de la comunidad comercial")
    descripcion: Optional[str] = Field(None, max_length=1500, description="Descripción, reglas o especificaciones del espacio")
    rubro: str = Field(..., min_length=2, max_length=100, description="Etiqueta inmutable de rubro comercial asignado")

class ComunidadUpdateInput(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150, description="Nuevo nombre de la comunidad comercial")
    descripcion: Optional[str] = Field(None, max_length=1500, description="Descripción, acuerdos y normativas actualizadas")

class ComunidadResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    rubro: str
    creador_id: str
    rol_usuario: Optional[str] = None
    estado: str
    creado_el: Optional[datetime] = None

class ComunidadDetalleResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    rubro: str
    creador_id: str
    estado: str
    creado_el: datetime
    actualizado_el: datetime
    rol_usuario_actual: Optional[str] = None
    estado_solicitud: Optional[str] = None
    es_moderador_o_creador: bool = False

class ComunidadListItemResponse(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    rubro: str
    creador_id: str
    estado: str
    total_miembros: int = 1
    rol_usuario_actual: Optional[str] = None
    estado_solicitud: Optional[str] = None
    es_moderador_o_creador: bool = False
    creado_el: datetime

class BusquedaComunidadesResponse(BaseModel):
    termino_busqueda: Optional[str] = None
    rubro_filtro: Optional[str] = None
    total_coincidencias: int
    comunidades: List[ComunidadListItemResponse]

class SolicitudIngresoResponse(BaseModel):
    id: str
    comunidad_id: str
    comunidad_nombre: str
    comerciante_id: str
    estado: str
    mensaje: str

class SolicitudDetalleItem(BaseModel):
    id: str
    comunidad_id: str
    comerciante_id: str
    nombre_razon_social: str
    email: str
    cuit_cuil: str
    rubro_comercial: str
    ciudad_localidad: str
    provincia: str
    creado_el: datetime

class EvaluarSolicitudInput(BaseModel):
    decision: str = Field(..., pattern="^(aprobar|rechazar)$", description="'aprobar' para admitir, 'rechazar' para denegar")

class EvaluarSolicitudResponse(BaseModel):
    solicitud_id: str
    decision: str
    nuevo_estado: str
    comunidad_id: str
    comunidad_nombre: str
    mensaje: str

class AbandonarComunidadResponse(BaseModel):
    comunidad_id: str
    comunidad_nombre: str
    comerciante_id: str
    mensaje: str

class ExpulsarIntegranteInput(BaseModel):
    justificacion: str = Field(..., min_length=5, max_length=1000, description="Motivo obligatorio de la expulsión")

class ExpulsarIntegranteResponse(BaseModel):
    comunidad_id: str
    comunidad_nombre: str
    integrante_id: str
    mensaje: str

class AsignarModeradorResponse(BaseModel):
    comunidad_id: str
    comunidad_nombre: str
    integrante_id: str
    nuevo_rol: str
    mensaje: str

class RevocarModeradorResponse(BaseModel):
    comunidad_id: str
    comunidad_nombre: str
    integrante_id: str
    nuevo_rol: str
    mensaje: str

class SolicitarEliminacionComunidadInput(BaseModel):
    motivo: str = Field(..., min_length=5, max_length=1000, description="Motivo obligatorio de la baja")

class SolicitarEliminacionComunidadResponse(BaseModel):
    solicitud_id: str
    comunidad_id: str
    comunidad_nombre: str
    creador_id: str
    nuevo_estado: str
    mensaje: str

class SolicitudEliminacionAdminItem(BaseModel):
    id: str
    comunidad_id: str
    comunidad_nombre: str
    comunidad_rubro: str
    creador_id: str
    creador_nombre: str
    creador_email: str
    motivo: str
    estado: str
    creado_el: datetime

class EvaluarEliminacionComunidadInput(BaseModel):
    decision: str = Field(..., pattern="^(aprobar|rechazar)$", description="'aprobar' para dar de baja definitiva, 'rechazar' para restaurar la comunidad")

class EvaluarEliminacionComunidadResponse(BaseModel):
    solicitud_id: str
    comunidad_id: str
    comunidad_nombre: str
    decision: str
    nuevo_estado_comunidad: str
    mensaje: str