from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==============================================================================
# ESQUEMAS DE INVENTARIO (CdU43 / CdU44 / CdU45)
# ==============================================================================

class InventarioItemCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=255, description="Denominación comercial del producto")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Especificaciones técnicas o detalles")
    rubro: str = Field(..., min_length=2, max_length=100, description="Rubro comercial heredado del perfil")
    subrubro: Optional[str] = Field(None, max_length=100, description="Subrubro comercial heredado del perfil")
    marca: Optional[str] = Field(None, max_length=100, description="Marca del producto")
    modelo: Optional[str] = Field(None, max_length=100, description="Modelo o versión específica")
    precio_unitario: float = Field(0.0, ge=0.0, description="Precio unitario en ARS")
    stock_actual: int = Field(..., ge=0, description="Existencias iniciales disponibles")
    stock_minimo_alerta: int = Field(0, ge=0, description="Umbral de alerta por escasez")

class InventarioItemUpdate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=255, description="Denominación comercial modificada")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Especificaciones actualizadas")
    marca: Optional[str] = Field(None, max_length=100, description="Marca del producto")
    modelo: Optional[str] = Field(None, max_length=100, description="Modelo o versión específica")
    precio_unitario: float = Field(..., ge=0.0, description="Nuevo precio unitario")
    stock_minimo_alerta: int = Field(..., ge=0, description="Nuevo umbral de alerta")

class InventarioStockAjuste(BaseModel):
    tipo_movimiento: str = Field(..., pattern="^(ingreso|egreso)$", description="'ingreso' para sumar, 'egreso' para restar")
    cantidad: int = Field(..., gt=0, description="Cantidad entera estrictamente positiva a ajustar")
    motivo: Optional[str] = Field(None, max_length=255, description="Justificación del movimiento")

class InventarioItemResponse(BaseModel):
    id: str
    comerciante_id: str
    nombre: str
    descripcion: Optional[str]
    rubro: str
    subrubro: Optional[str]
    marca: Optional[str]
    modelo: Optional[str]
    precio_unitario: float
    stock_actual: int
    stock_minimo_alerta: int
    estado: str
    creado_el: datetime
    actualizado_el: datetime