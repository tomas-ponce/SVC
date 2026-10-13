from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==============================================================================
# ESQUEMAS PARA MÓDULO DE NEGOCIACIÓN Y CHAT (CdU34 a CdU42)
# ==============================================================================

# CdU34: Inicio de Sala
class IniciarChatInput(BaseModel):
    publicacion_id: str = Field(..., description="ID de la publicación de venta sobre la cual negociar")
    mensaje_inicial: str = Field(..., min_length=1, max_length=3000, description="Primer mensaje descriptivo o propuesta comercial")

class IniciarChatResponse(BaseModel):
    sala_id: str
    mensaje_id: str
    publicacion_id: str
    publicacion_titulo: str
    publicacion_precio: float
    vendedor_id: str
    comprador_id: str
    contenido: str
    es_sala_reutilizada: bool
    mensaje: str

# CdU35: Enviar Mensaje
class EnviarMensajeInput(BaseModel):
    contenido: str = Field(..., min_length=1, max_length=3000, description="Texto del mensaje a despachar")

class MensajeItemResponse(BaseModel):
    id: str
    sala_id: str
    emisor_id: str
    contenido: str
    leido: bool
    creado_el: datetime
    es_propio: Optional[bool] = False

# CdU36: Bandeja de Chats de Negociación
class BandejaChatItemResponse(BaseModel):
    sala_id: str
    publicacion_id: str
    publicacion_titulo: str
    publicacion_precio: float
    publicacion_estado: str
    contraparte_id: str
    contraparte_nombre: str
    contraparte_rubro: Optional[str] = None
    contraparte_cuit: Optional[str] = None
    archivado: bool = False
    bloqueado: bool = False
    mensajes_no_leidos: int = 0
    ultimo_mensaje_contenido: Optional[str] = None
    ultimo_mensaje_fecha: Optional[datetime] = None
    ultimo_mensaje_emisor_id: Optional[str] = None

# CdU38: Marcar como Leído
class MarcarLeidoResponse(BaseModel):
    sala_id: str
    mensajes_marcados: int
    mensaje: str

# CdU39: Archivar Chat
class ArchivarChatResponse(BaseModel):
    sala_id: str
    archivado: bool
    mensaje: str

# CdU40: Desarchivar Chat
class DesarchivarChatResponse(BaseModel):
    sala_id: str
    archivado: bool
    mensaje: str

# CdU41: Bloquear Usuario
class BloquearUsuarioResponse(BaseModel):
    sala_id: str
    contraparte_id: str
    contraparte_nombre: str
    bloqueado: bool
    mensaje: str

# Soporte de Sala y Listado Detallado (CdU35 / CdU37)
class SalaDetalleResponse(BaseModel):
    sala_id: str
    publicacion_id: str
    publicacion_titulo: str
    publicacion_precio: float
    publicacion_estado: str
    contraparte_id: str
    contraparte_nombre: str
    contraparte_cuit: Optional[str] = None
    contraparte_rubro: Optional[str] = None
    contraparte_telefono: Optional[str] = None
    contraparte_email: Optional[str] = None
    bloqueado_por_mi: bool = False
    archivado_por_mi: bool = False
    mensajes: List[MensajeItemResponse] = []