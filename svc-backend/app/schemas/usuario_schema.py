from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# Esquemas de Registro (CdU01)
class ComercianteRegistroCreate(BaseModel):
    nombre_razon_social: str = Field(..., min_length=3)
    cuit_cuil: str = Field(..., min_length=10, max_length=13)
    rubro_comercial: str
    subrubro_comercial: str
    direccion: str
    pais: str = "Argentina"
    provincia: str
    ciudad_localidad: str
    zona_alcance_logistico: str
    telefono: str
    email: EmailStr
    password: str = Field(..., min_length=8)

class ComercianteRegistroResponse(BaseModel):
    id: str
    email: EmailStr
    nombre_razon_social: str
    cuit_cuil: str
    telefono: str
    direccion: str
    rubro_comercial: str
    subrubro_comercial: str
    pais: str
    provincia: str
    ciudad_localidad: str
    zona_alcance_logistico: str
    rol: str
    estado: str
    creado_el: datetime

# Esquemas de Autenticación (CdU02 / CdU06)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: ComercianteRegistroResponse

# Esquema de Actualización de Perfil (CdU04)
class ComerciantePerfilUpdate(BaseModel):
    nombre_razon_social: str = Field(..., min_length=3)
    telefono: str
    rubro_comercial: str
    subrubro_comercial: str
    direccion: str
    provincia: str
    ciudad_localidad: str
    zona_alcance_logistico: str

# Esquemas de Recuperación de Contraseña (CdU03)
class RecuperarPasswordRequest(BaseModel):
    email: EmailStr

class RestablecerPasswordRequest(BaseModel):
    token: str
    nueva_password: str = Field(..., min_length=8)