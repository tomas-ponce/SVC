from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import httpx
from app.core.security import get_current_user_id, cifrar_credencial
from app.db.supabase_client import supabase

router = APIRouter(prefix="/integraciones", tags=["Integración Financiera y Logística (Sprint 6)"])

class IntegracionMPInput(BaseModel):
    public_key: str = Field(..., min_length=10)
    access_token: str = Field(..., min_length=10)

class IntegracionLogisticaInput(BaseModel):
    proveedor: str = Field(..., pattern="^(Correo Argentino|Andreani)$")
    api_key: str = Field(..., min_length=5)

@router.get("/estado", status_code=status.HTTP_200_OK, summary="Consultar estado de integraciones externas (CdU52 / CdU56)")
def consultar_estado_integraciones(user_id: str = Depends(get_current_user_id)):
    """
    Retorna el estado de vinculación de pasarelas del comerciante sin exponer
    credenciales privadas desencriptadas por normativas de seguridad (RF08 / RF09).
    """
    try:
        res = supabase.table("comerciante_integraciones").select("*").eq("comerciante_id", user_id).execute()
        if not res.data:
            return {
                "mercadopago_vinculado": False,
                "mp_public_key": None,
                "logistica_vinculada": False,
                "logistica_proveedor": None
            }
        
        datos = res.data[0]
        tiene_mp = bool(datos.get("mp_access_token"))
        tiene_log = bool(datos.get("logistica_api_key"))

        return {
            "mercadopago_vinculado": tiene_mp,
            "mp_public_key": datos.get("mp_public_key") if tiene_mp else None,
            "logistica_vinculada": tiene_log,
            "logistica_proveedor": datos.get("logistica_proveedor") if tiene_log else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo al recuperar estado de integraciones: {str(e)}")

@router.post("/mercadopago", status_code=status.HTTP_200_OK, summary="Vincular MercadoPago (CdU52)")
async def configurar_mercadopago(datos: IntegracionMPInput, user_id: str = Depends(get_current_user_id)):
    # 1. Handshake de Validación Externa (RF08 - Paso 4 y 5 de CdU52)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res_mp = await client.get(
                "https://api.mercadopago.com/users/me",
                headers={"Authorization": f"Bearer {datos.access_token.strip()}"}
            )
        
        if res_mp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Error de validación. Verifique sus credenciales con MercadoPago."
            )
    except httpx.RequestError:
        # Flujo alterno 4.1 y 4.2 del CdU52 (Caída de servicio o timeout)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de validación de MercadoPago no se encuentra disponible momentáneamente. Intente nuevamente más tarde."
        )

    # 2. Cifrado simétrico robusto de la credencial privada antes de persistir (CdU52 - Paso 6)
    token_cifrado = cifrar_credencial(datos.access_token.strip())
    
    try:
        # Verificamos existencia previa para no sobreescribir los datos logísticos
        existente = supabase.table("comerciante_integraciones").select("comerciante_id").eq("comerciante_id", user_id).execute()
        
        if existente.data:
            supabase.table("comerciante_integraciones").update({
                "mp_public_key": datos.public_key.strip(),
                "mp_access_token": token_cifrado,
                "actualizado_el": "now()"
            }).eq("comerciante_id", user_id).execute()
        else:
            supabase.table("comerciante_integraciones").insert({
                "comerciante_id": user_id,
                "mp_public_key": datos.public_key.strip(),
                "mp_access_token": token_cifrado
            }).execute()

        return {"mensaje": "Vinculación Exitosa. El cobro digital ha sido activado para sus ventas."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en la persistencia de credenciales: {str(e)}")

@router.post("/logistica", status_code=status.HTTP_200_OK, summary="Vincular Logística Externa (CdU56)")
async def configurar_logistica(datos: IntegracionLogisticaInput, user_id: str = Depends(get_current_user_id)):
    # 1. Validación de formato y consistencia de credencial logística (CdU56 - Paso 4 y 5)
    clave_limpia = datos.api_key.strip()
    if len(clave_limpia) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación. Verifique sus credenciales con {datos.proveedor}."
        )

    # 2. Cifrado simétrico robusto de la API Key (CdU56 - Paso 6)
    api_key_cifrada = cifrar_credencial(clave_limpia)
    
    try:
        # Verificamos existencia previa para no sobreescribir los datos de MercadoPago
        existente = supabase.table("comerciante_integraciones").select("comerciante_id").eq("comerciante_id", user_id).execute()
        
        if existente.data:
            supabase.table("comerciante_integraciones").update({
                "logistica_proveedor": datos.proveedor,
                "logistica_api_key": api_key_cifrada,
                "actualizado_el": "now()"
            }).eq("comerciante_id", user_id).execute()
        else:
            supabase.table("comerciante_integraciones").insert({
                "comerciante_id": user_id,
                "logistica_proveedor": datos.proveedor,
                "logistica_api_key": api_key_cifrada
            }).execute()

        return {"mensaje": f"Vinculación Logística Exitosa. Trazabilidad activada con {datos.proveedor}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo al registrar integración logística: {str(e)}")
