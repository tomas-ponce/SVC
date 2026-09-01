import io
import re
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from app.schemas.inventario_schema import (
    InventarioItemCreate,
    InventarioItemUpdate,
    InventarioStockAjuste,
    InventarioItemResponse
)
from app.core.security import get_current_user_id
from app.core.email_service import enviar_correo_alerta_bajo_stock
from app.db.supabase_client import supabase

router = APIRouter(prefix="/inventario", tags=["Módulo de Inventario y Catálogo Privado (Sprint 2)"])

def determinar_estado_stock(actual: int, minimo: int) -> str:
    """Calcula el estado del producto en base a existencias reales y umbral (ERS CdU43/CdU44/CdU45)."""
    if actual == 0:
        return "sin_stock"
    elif actual <= minimo:
        return "bajo_stock"
    return "disponible"

def sanitizar_nombre_archivo(texto: str) -> str:
    """Limpia caracteres especiales y espacios para nombres de archivo compatibles."""
    if not texto:
        return "Comercio"
    limpio = re.sub(r'[^\w\-_\.]', '_', texto.strip())
    return re.sub(r'_+', '_', limpio)

class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasos para numerar dinámicamente 'Página X de Y' y agregar pie institucional."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_footer(num_pages)
            super().showPage()
        super().save()

    def draw_page_footer(self, page_count: int):
        self.saveState()
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.75)
        self.line(36, 40, 576, 40)
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(36, 28, "SVC — Sistema de Vinculación para el Comercio | Documento Oficial de Auditoría")
        
        page_str = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(576, 28, page_str)
        self.restoreState()

# ==============================================================================
# 1. CdU43 - REGISTRAR NUEVO ÍTEM EN INVENTARIO
# ==============================================================================
@router.post(
    "/items", 
    response_model=InventarioItemResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo producto en el catálogo privado (CdU43)"
)
def registrar_item(datos: InventarioItemCreate, user_id: str = Depends(get_current_user_id)):
    user_check = supabase.table("comerciantes").select("*").eq("id", user_id).execute()
    if not user_check.data or user_check.data[0].get("estado") != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los comerciantes con cuenta activa pueden gestionar inventario privado."
        )

    comercio = user_check.data[0]
    rubro_oficial = comercio.get("rubro_comercial") or datos.rubro
    subrubro_oficial = comercio.get("subrubro_comercial") or datos.subrubro

    estado_calculado = determinar_estado_stock(datos.stock_actual, datos.stock_minimo_alerta)

    nuevo_item = {
        "comerciante_id": user_id,
        "nombre": datos.nombre.strip(),
        "descripcion": datos.descripcion.strip() if datos.descripcion else None,
        "rubro": rubro_oficial.strip(),
        "subrubro": subrubro_oficial.strip() if subrubro_oficial else None,
        "marca": datos.marca.strip() if datos.marca else None,
        "modelo": datos.modelo.strip() if datos.modelo else None,
        "precio_unitario": datos.precio_unitario,
        "stock_actual": datos.stock_actual,
        "stock_minimo_alerta": datos.stock_minimo_alerta,
        "estado": estado_calculado
    }

    resultado = supabase.table("inventario_items").insert(nuevo_item).execute()
    if not resultado.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al persistir el ítem en la base de datos de inventario."
        )

    item_guardado = resultado.data[0]

    if estado_calculado in ["bajo_stock", "sin_stock"] and datos.stock_minimo_alerta > 0:
        enviar_correo_alerta_bajo_stock(
            destinatario=comercio["email"],
            razon_social=comercio.get("nombre_razon_social", "Comercio"),
            nombre_producto=item_guardado["nombre"],
            stock_actual=item_guardado["stock_actual"],
            stock_minimo=item_guardado["stock_minimo_alerta"]
        )

    return item_guardado

# ==============================================================================
# 2. LISTAR ÍTEMS PRIVADOS DEL COMERCIANTE
# ==============================================================================
@router.get(
    "/items", 
    response_model=List[InventarioItemResponse],
    summary="Listar productos del inventario del comerciante autenticado"
)
def listar_items_inventario(user_id: str = Depends(get_current_user_id)):
    res = (
        supabase.table("inventario_items")
        .select("*")
        .eq("comerciante_id", user_id)
        .order("creado_el", desc=True)
        .execute()
    )
    return res.data or []

# ==============================================================================
# 3. CdU44 - EDITAR ÍTEM EXISTENTE
# ==============================================================================
@router.put(
    "/items/{item_id}", 
    response_model=InventarioItemResponse,
    summary="Modificar la información descriptiva y parámetros de alerta de un producto (CdU44)"
)
def editar_item(item_id: str, datos: InventarioItemUpdate, user_id: str = Depends(get_current_user_id)):
    check_item = (
        supabase.table("inventario_items")
        .select("*")
        .eq("id", item_id)
        .eq("comerciante_id", user_id)
        .execute()
    )
    if not check_item.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El producto solicitado no existe o no pertenece a su catálogo privado."
        )

    item_actual = check_item.data[0]
    estado_anterior = item_actual["estado"]
    nuevo_estado = determinar_estado_stock(item_actual["stock_actual"], datos.stock_minimo_alerta)

    payload_update = {
        "nombre": datos.nombre.strip(),
        "descripcion": datos.descripcion.strip() if datos.descripcion else None,
        "marca": datos.marca.strip() if datos.marca else None,
        "modelo": datos.modelo.strip() if datos.modelo else None,
        "precio_unitario": datos.precio_unitario,
        "stock_minimo_alerta": datos.stock_minimo_alerta,
        "estado": nuevo_estado,
        "actualizado_el": "now()"
    }

    res_update = (
        supabase.table("inventario_items")
        .update(payload_update)
        .eq("id", item_id)
        .eq("comerciante_id", user_id)
        .execute()
    )

    if not res_update.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar los datos del producto en la base de datos."
        )

    item_actualizado = res_update.data[0]

    if nuevo_estado in ["bajo_stock", "sin_stock"] and estado_anterior == "disponible":
        user_info = supabase.table("comerciantes").select("email, nombre_razon_social").eq("id", user_id).execute()
        if user_info.data:
            c = user_info.data[0]
            enviar_correo_alerta_bajo_stock(
                destinatario=c["email"],
                razon_social=c.get("nombre_razon_social", "Comercio"),
                nombre_producto=item_actualizado["nombre"],
                stock_actual=item_actualizado["stock_actual"],
                stock_minimo=item_actualizado["stock_minimo_alerta"]
            )

    return item_actualizado

# ==============================================================================
# 4. CdU45 - AJUSTAR STOCK DE ÍTEM DE INVENTARIO
# ==============================================================================
@router.post(
    "/items/{item_id}/ajustar-stock", 
    response_model=InventarioItemResponse,
    summary="Ajustar manualmente las existencias físicas sumando o restando unidades (CdU45)"
)
def ajustar_stock_item(
    item_id: str, 
    datos: InventarioStockAjuste, 
    user_id: str = Depends(get_current_user_id)
):
    check = (
        supabase.table("inventario_items")
        .select("*")
        .eq("id", item_id)
        .eq("comerciante_id", user_id)
        .execute()
    )
    if not check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El ítem de inventario no existe o no pertenece a su catálogo comercial."
        )

    item = check.data[0]
    stock_anterior = item["stock_actual"]
    estado_anterior = item["estado"]

    if datos.tipo_movimiento == "ingreso":
        nuevo_stock = stock_anterior + datos.cantidad
    else:
        if datos.cantidad > stock_anterior:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ajuste no puede resultar en un stock negativo. Existencias actuales: {stock_anterior} unidades."
            )
        nuevo_stock = stock_anterior - datos.cantidad

    nuevo_estado = determinar_estado_stock(nuevo_stock, item["stock_minimo_alerta"])

    res_update = (
        supabase.table("inventario_items")
        .update({
            "stock_actual": nuevo_stock,
            "estado": nuevo_estado,
            "actualizado_el": "now()"
        })
        .eq("id", item_id)
        .eq("comerciante_id", user_id)
        .execute()
    )

    if not res_update.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el saldo de existencias en el inventario."
        )

    try:
        supabase.table("inventario_ajustes_log").insert({
            "item_id": item_id,
            "comerciante_id": user_id,
            "tipo_movimiento": datos.tipo_movimiento,
            "cantidad": datos.cantidad,
            "stock_anterior": stock_anterior,
            "stock_nuevo": nuevo_stock,
            "motivo": datos.motivo.strip() if datos.motivo else None
        }).execute()
    except Exception:
        pass

    item_ajustado = res_update.data[0]

    if nuevo_estado in ["bajo_stock", "sin_stock"] and estado_anterior == "disponible":
        user_info = supabase.table("comerciantes").select("email, nombre_razon_social").eq("id", user_id).execute()
        if user_info.data:
            c = user_info.data[0]
            enviar_correo_alerta_bajo_stock(
                destinatario=c["email"],
                razon_social=c.get("nombre_razon_social", "Comercio"),
                nombre_producto=item_ajustado["nombre"],
                stock_actual=item_ajustado["stock_actual"],
                stock_minimo=item_ajustado["stock_minimo_alerta"]
            )

    return item_ajustado

# ==============================================================================
# 5. CdU46 - ELIMINAR ÍTEM DEL INVENTARIO
# ==============================================================================
@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Remover un registro de mercadería del catálogo digital (CdU46)"
)
def eliminar_item_inventario(
    item_id: str,
    user_id: str = Depends(get_current_user_id)
):
    check = (
        supabase.table("inventario_items")
        .select("id, nombre")
        .eq("id", item_id)
        .eq("comerciante_id", user_id)
        .execute()
    )
    if not check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El ítem de inventario no existe o no pertenece a su catálogo privado."
        )
    
    item = check.data[0]

    try:
        check_pubs = (
            supabase.table("publicaciones_venta")
            .select("id, titulo")
            .eq("inventario_item_id", item_id)
            .eq("estado", "Activa")
            .execute()
        )
        if check_pubs.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No es posible eliminar '{item['nombre']}' porque se encuentra vinculado a publicaciones de venta activas en la plataforma. Pause o elimine dichas ofertas comerciales antes de destruir el ítem."
            )
    except HTTPException as he:
        raise he
    except Exception:
        pass

    res_delete = (
        supabase.table("inventario_items")
        .delete()
        .eq("id", item_id)
        .eq("comerciante_id", user_id)
        .execute()
    )

    if not res_delete.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el ítem de inventario en la base de datos."
        )

    return {
        "mensaje": f"El producto '{item['nombre']}' ha sido eliminado definitivamente de su inventario.",
        "item_id": item_id
    }

# ==============================================================================
# 6. CdU47 - EXPORTAR REPORTE DE INVENTARIO (PDF)
# ==============================================================================
@router.get(
    "/exportar-pdf",
    summary="Generar y descargar documento consolidado de inventario con marca de tiempo (CdU47)"
)
def exportar_reporte_pdf(user_id: str = Depends(get_current_user_id)):
    user_res = supabase.table("comerciantes").select("*").eq("id", user_id).execute()
    if not user_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró la información del comercio autenticado."
        )
    comercio = user_res.data[0]

    items_res = (
        supabase.table("inventario_items")
        .select("*")
        .eq("comerciante_id", user_id)
        .order("nombre", desc=False)
        .execute()
    )
    items = items_res.data or []

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No posee productos registrados en el inventario para generar un reporte."
        )

    total_articulos = len(items)
    stock_total = sum(int(it.get("stock_actual", 0)) for it in items)
    valor_total = sum(float(it.get("precio_unitario", 0.0)) * int(it.get("stock_actual", 0)) for it in items)
    valor_total_fmt = f"${valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=48
    )

    story = []
    styles = getSampleStyleSheet()

    style_brand_box = ParagraphStyle(
        'BrandBox',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.white
    )

    style_brand_sub = ParagraphStyle(
        'BrandSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#475569'),
        leading=10
    )

    style_meta_right = ParagraphStyle(
        'MetaRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#334155'),
        alignment=2,
        leading=11
    )

    style_kpi_num = ParagraphStyle(
        'KpiNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        leading=15
    )

    style_kpi_lbl = ParagraphStyle(
        'KpiLbl',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        leading=9
    )

    style_th = ParagraphStyle(
        'ThStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=colors.white,
        leading=9
    )

    style_td_main = ParagraphStyle(
        'TdMain',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#0f172a'),
        leading=10
    )

    style_td_desc = ParagraphStyle(
        'TdDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        textColor=colors.HexColor('#64748b'),
        leading=8.5
    )

    style_td = ParagraphStyle(
        'TdNorm',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        textColor=colors.HexColor('#334155'),
        leading=9.5
    )

    style_td_num = ParagraphStyle(
        'TdNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#0f172a'),
        alignment=2,
        leading=10
    )

    # 1. Header B2B
    logo_table = Table([[Paragraph("SVC", style_brand_box)]], colWidths=[42], rowHeights=[22])
    logo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0056b3')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))

    header_left = Table([
        [logo_table, Paragraph("<b>Sistema de Vinculación para el Comercio</b><br/>Reporte Oficial de Inventario y Existencias", style_brand_sub)]
    ], colWidths=[48, 250])
    header_left.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    ahora_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    info_derecha = (
        f"<b>Razón Social:</b> {comercio.get('nombre_razon_social', '—')}<br/>"
        f"<b>CUIT/CUIL:</b> {comercio.get('cuit_cuil', '—')}<br/>"
        f"<b>Rubro:</b> {comercio.get('rubro_comercial', '—')}<br/>"
        f"<b>Fecha de Emisión:</b> {ahora_str} hs"
    )
    header_right = Paragraph(info_derecha, style_meta_right)

    top_header_table = Table([[header_left, header_right]], colWidths=[310, 230])
    top_header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(top_header_table)
    story.append(Spacer(1, 10))

    # 2. KPI Summary Cards
    kpi_col1 = [Paragraph(f"{total_articulos}", style_kpi_num), Paragraph("PRODUCTOS REGISTRADOS", style_kpi_lbl)]
    kpi_col2 = [Paragraph(f"{stock_total}", style_kpi_num), Paragraph("UNIDADES EN STOCK", style_kpi_lbl)]
    kpi_col3 = [Paragraph(f"{valor_total_fmt}", style_kpi_num), Paragraph("VALORIZACIÓN TOTAL", style_kpi_lbl)]

    kpi_table = Table([[kpi_col1, kpi_col2, kpi_col3]], colWidths=[174, 174, 174])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#e2e8f0')),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#e2e8f0')),
        ('BOX', (2, 0), (2, 0), 1, colors.HexColor('#e2e8f0')),
        ('LINEBEFORE', (1, 0), (1, 0), 1, colors.HexColor('#cbd5e1')),
        ('LINEBEFORE', (2, 0), (2, 0), 1, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # 3. Grilla de datos principal
    headers = [
        Paragraph("PRODUCTO / ESPECIFICACIONES", style_th),
        Paragraph("RUBRO / CATEGORÍA", style_th),
        Paragraph("MARCA / MODELO", style_th),
        Paragraph("PRECIO UNITARIO", style_th),
        Paragraph("STOCK", style_th),
        Paragraph("UMBRAL", style_th),
        Paragraph("ESTADO", style_th)
    ]

    tabla_data = [headers]

    for it in items:
        precio_val = float(it.get("precio_unitario", 0.0))
        precio_fmt = f"${precio_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        estado_badge_color = '#d4edda'
        estado_text_color = '#155724'
        estado_txt = "DISPONIBLE"
        
        if it.get("estado") == "bajo_stock":
            estado_badge_color = '#fff3cd'
            estado_text_color = '#856404'
            estado_txt = "BAJO STOCK"
        elif it.get("estado") == "sin_stock":
            estado_badge_color = '#f8d7da'
            estado_text_color = '#721c24'
            estado_txt = "SIN STOCK"

        badge_p = Paragraph(
            f"<font color='{estado_text_color}'><b>{estado_txt}</b></font>",
            ParagraphStyle('BadgeP', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=6.5, alignment=1)
        )
        badge_table = Table([[badge_p]], colWidths=[58], rowHeights=[14])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(estado_badge_color)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
        ]))

        marca_mod = f"{it.get('marca') or '—'} / {it.get('modelo') or '—'}"
        cat_sub = it.get('rubro') or '—'

        fila = [
            [Paragraph(f"{it.get('nombre', '—')}", style_td_main), Paragraph(f"{it.get('descripcion') or 'Sin especificaciones'}", style_td_desc)],
            Paragraph(f"{cat_sub}", style_td),
            Paragraph(f"{marca_mod}", style_td),
            Paragraph(precio_fmt, style_td_num),
            Paragraph(str(it.get("stock_actual", 0)), style_td_num),
            Paragraph(str(it.get("stock_minimo_alerta", 0)), style_td_num),
            badge_table
        ]
        tabla_data.append(fila)

    main_table = Table(tabla_data, colWidths=[150, 75, 80, 68, 42, 42, 65])
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4.5),
    ]))

    story.append(main_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Formato de nombre único: 'razonsocial'_reporte-inventario-SVC_'timestamp'.pdf
    razon_social_raw = comercio.get('nombre_razon_social') or 'Comercio'
    razon_social_clean = sanitizar_nombre_archivo(razon_social_raw)
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{razon_social_clean}_reporte-inventario-SVC_{timestamp_str}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )