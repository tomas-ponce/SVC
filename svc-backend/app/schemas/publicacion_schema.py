from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==============================================================================
# ESQUEMAS PARA PUBLICACIONES DE VENTA (CdU25 a CdU33)
# ==============================================================================

class PublicacionVentaCreate(BaseModel):
    titulo: str = Field(..., min_length=4, max_length=255, description="Título descriptivo de la oferta")
    descripcion: Optional[str] = Field(None, max_length=2000, description="Especificaciones y detalles comerciales")
    precio: float = Field(..., ge=0.0, description="Precio unitario en ARS")
    origen: str = Field("Nacional", min_length=2, max_length=100, description="Origen comercial declarado")
    rubro: str = Field(..., min_length=2, max_length=100, description="Rubro comercial de la oferta")
    subrubro: Optional[str] = Field(None, max_length=100, description="Subrubro comercial")
    unidades_ofertadas: int = Field(1, gt=0, description="Cantidad de unidades ofertadas")
    inventario_item_id: Optional[str] = Field(None, description="ID del ítem de inventario si aplica deducción")

class PublicacionVentaUpdate(BaseModel):
    titulo: str = Field(..., min_length=4, max_length=255, description="Nuevo título de la oferta")
    descripcion: Optional[str] = Field(None, max_length=2000, description="Especificaciones técnicas actualizadas")
    precio: float = Field(..., ge=0.0, description="Precio unitario referencial actualizado en ARS")
    origen: str = Field("Nacional", min_length=2, max_length=100, description="Origen comercial de la mercadería")
    rubro: str = Field(..., min_length=2, max_length=100, description="Rubro comercial")
    subrubro: Optional[str] = Field(None, max_length=100, description="Subrubro comercial")
    unidades_ofertadas: int = Field(..., gt=0, description="Cantidad de unidades ofertadas actualizada")

class EliminarPublicacionAdminInput(BaseModel):
    motivo_infraccion: str = Field(..., min_length=5, max_length=1000, description="Justificación obligatoria de la medida de moderación")

class PublicacionVentaResponse(BaseModel):
    id: str
    comerciante_id: str
    inventario_item_id: Optional[str] = None
    titulo: str
    descripcion: Optional[str] = None
    precio: float
    origen: str
    rubro: str
    subrubro: Optional[str] = None
    unidades_ofertadas: int
    estado: str
    creado_el: datetime
    actualizado_el: datetime

class ComerciantePublicacionItem(BaseModel):
    id: str
    nombre_razon_social: str
    cuit_cuil: str
    telefono: str
    email: str
    direccion: str
    ciudad_localidad: str
    provincia: str
    zona_alcance_logistico: str

class PublicacionDetalleCompletoResponse(BaseModel):
    id: str
    comerciante_id: str
    inventario_item_id: Optional[str] = None
    titulo: str
    descripcion: Optional[str] = None
    precio: float
    origen: str
    rubro: str
    subrubro: Optional[str] = None
    unidades_ofertadas: int
    estado: str
    creado_el: datetime
    actualizado_el: datetime
    es_autor: bool
    vendedor: ComerciantePublicacionItem