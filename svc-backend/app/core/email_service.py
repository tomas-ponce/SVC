import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "svc.team.oficial@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "file:///C:/Users/ponce/SVC/svc-frontend")

def _enviar_email_smtp(destinatario: str, asunto: str, html_body: str) -> None:
    """Función base para transporte SMTP seguro mediante STARTTLS."""
    try:
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = asunto
        mensaje["From"] = f"Sistema de Vinculación para el Comercio <{SMTP_FROM_EMAIL}>"
        mensaje["To"] = destinatario
        mensaje.attach(MIMEText(html_body, "html"))

        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        servidor.starttls()
        servidor.login(SMTP_USER, SMTP_PASSWORD)
        servidor.sendmail(SMTP_FROM_EMAIL, destinatario, mensaje.as_string())
        servidor.quit()
        print(f"[SMTP OK] Correo enviado a: {destinatario} | Asunto: {asunto}")
    except Exception as e:
        print(f"[SMTP FALLBACK LOG] Error enviando correo a {destinatario}: {str(e)}")

# ── CdU03: Recuperación de Contraseña ──────────────────────────────────
def enviar_correo_recuperacion(destinatario: str, token: str) -> None:
    reset_url = f"{FRONTEND_BASE_URL}/reset-password.html?token={token}"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0056b3; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 20px; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC</div>
            <div class="title">Restablecimiento de Contraseña</div>
            <p class="text">Hemos recibido una solicitud para restablecer la contraseña asociada a la cuenta <strong>{destinatario}</strong> en el <strong>Sistema de Vinculación para el Comercio (SVC)</strong>.</p>
            <p style="text-align: center; margin: 30px 0;"><a href="{reset_url}" target="_blank" rel="noopener noreferrer" class="btn">Restablecer mi Contraseña &rarr;</a></p>
            <p class="text" style="font-size: 12px;">Enlace alternativo:<br><span style="color: #0056b3; word-break: break-all;">{reset_url}</span></p>
            <div class="warn">• Válido por <strong>30 minutos</strong>.<br>• Si no lo solicitó, ignore este mensaje.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Recuperación de Contraseña de Acceso", html)

# ── CdU09: Confirmación de Baja de Cuenta (2FA) ───────────────────────
def enviar_correo_confirmacion_baja(destinatario: str, razon_social: str, token: str) -> None:
    confirm_url = f"{FRONTEND_BASE_URL}/confirmar-baja.html?token={token}"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #dc3545; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #dc3545; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #991b1b; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 20px; }}
        .code-box {{ background-color: #fff5f5; border: 1px dashed #dc3545; padding: 15px; margin: 20px 0; text-align: center; border-radius: 0px !important; }}
        .code-label {{ font-size: 11px; font-weight: 700; color: #991b1b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
        .code-val {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: 700; color: #0f172a; word-break: break-all; letter-spacing: 1px; }}
        .btn {{ display: inline-block; background-color: #dc3545; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — SEGURIDAD</div>
            <div class="title">Confirmación de Baja de Cuenta</div>
            <p class="text">Estimado/a representante de <strong>{razon_social}</strong>:<br><br>Se ha iniciado el proceso de baja voluntaria de su cuenta comercial en <strong>SVC</strong>.</p>
            
            <div class="code-box">
                <div class="code-label">Su código / token de confirmación:</div>
                <div class="code-val">{token}</div>
            </div>

            <p class="text" style="font-size: 12px;">Puede copiar el código anterior y pegarlo en la ventana de su perfil, o bien hacer clic directamente en el siguiente botón:</p>

            <p style="text-align: center; margin: 25px 0;">
                <a href="{confirm_url}" target="_blank" rel="noopener noreferrer" class="btn">Confirmar Eliminación Definitiva &rarr;</a>
            </p>
            
            <div class="warn">• Válido por <strong>15 minutos</strong>.<br>• Si no lo solicitó, desestime este mensaje y cambie su contraseña de acceso inmediatamente.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Confirmación de Baja de Cuenta Comercial", html)

# ── CdU05: Alta de Administrador ──────────────────────────────────────
def enviar_correo_bienvenida_admin(destinatario: str, nombre_completo: str, password_provisoria: str) -> None:
    login_url = f"{FRONTEND_BASE_URL}/login.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0056b3; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .cred {{ background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 15px; margin: 20px 0; font-family: monospace; font-size: 13px; color: #0f172a; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — GESTIÓN GLOBAL</div>
            <div class="title">Bienvenido/a al Equipo de Administración</div>
            <p class="text">Estimado/a <strong>{nombre_completo}</strong>:<br><br>Se le ha otorgado acceso con rol de <strong>Administrador</strong> en el Sistema de Vinculación para el Comercio (SVC).</p>
            <div class="cred"><strong>Usuario:</strong> {destinatario}<br><strong>Contraseña Provisoria:</strong> {password_provisoria}</div>
            <p style="text-align: center; margin: 25px 0;"><a href="{login_url}" target="_blank" rel="noopener noreferrer" class="btn">Acceder al Panel de Control &rarr;</a></p>
            <div class="warn">• Recomendamos cambiar su contraseña al iniciar sesión.<br>• Este correo contiene credenciales confidenciales.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Alta de Cuenta Administrativa", html)

# ── CdU07: Inhabilitación de Comerciante ───────────────────────────────
def enviar_correo_inhabilitacion_comerciante(destinatario: str, razon_social: str, motivo: str) -> None:
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #dc3545; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #dc3545; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #991b1b; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .motivo {{ background-color: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; font-size: 13px; color: #7f1d1d; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — MODERACIÓN COMERCIAL</div>
            <div class="title">Cuenta Comercial Inhabilitada</div>
            <p class="text">Estimado/a representante de <strong>{razon_social}</strong>:<br><br>Le informamos que la administración global de SVC ha dispuesto la <strong>inhabilitación preventiva</strong> de su cuenta comercial.</p>
            <div class="motivo"><strong>Justificación de la Sanción:</strong><br>{motivo}</div>
            <p class="text" style="font-size: 12px;">Sus publicaciones de venta e inventario han sido pausados de la vista pública y su acceso a la plataforma se encuentra restringido.</p>
            <div class="warn">• Puede comunicarse con soporte respondiendo a este correo.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Notificación Oficial de Suspensión de Cuenta Comercial", html)

# ── CdU07: Inhabilitación de Administrador ─────────────────────────────
def enviar_correo_inhabilitacion_admin(destinatario: str, nombre_completo: str, motivo: str) -> None:
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #dc3545; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0f172a; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #991b1b; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .motivo {{ background-color: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; font-size: 13px; color: #7f1d1d; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — AUDITORÍA INSTITUCIONAL</div>
            <div class="title">Cuenta Administrativa Inhabilitada</div>
            <p class="text">Estimado/a <strong>{nombre_completo}</strong>:<br><br>Le notificamos que la Administración Principal de SVC ha revocado temporalmente sus credenciales y permisos operativos con rol de <strong>Administrador</strong>.</p>
            <div class="motivo"><strong>Motivo Institucional Registrado:</strong><br>{motivo}</div>
            <p class="text" style="font-size: 12px;">A partir de este momento, su acceso al panel de control centralizado y a las herramientas de moderación ha sido bloqueado.</p>
            <div class="warn">• Esta sanción se encuentra registrada con marca de tiempo en la bitácora de auditoría del sistema.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Notificación Oficial de Suspensión de Credenciales Administrativas", html)

# ── CdU07: Reactivación de Comerciante ─────────────────────────────────
def enviar_correo_reactivacion_comerciante(destinatario: str, razon_social: str) -> None:
    login_url = f"{FRONTEND_BASE_URL}/login.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #28a745; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #28a745; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #166534; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .success {{ background-color: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; font-size: 13px; color: #14532d; }}
        .btn {{ display: inline-block; background-color: #28a745; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — GESTIÓN GLOBAL</div>
            <div class="title">Cuenta Comercial Reactivada</div>
            <p class="text">Estimado/a representante de <strong>{razon_social}</strong>:<br><br>Nos complace informarle que la administración global de SVC ha dispuesto la <strong>reactivación plena</strong> de su cuenta comercial.</p>
            <div class="success">Su perfil se encuentra nuevamente habilitado para operar, publicar ofertas y participar de las negociaciones en la red B2B.</div>
            <p style="text-align: center; margin: 25px 0;"><a href="{login_url}" target="_blank" rel="noopener noreferrer" class="btn">Iniciar Sesión en SVC &rarr;</a></p>
            <div class="warn">• Gracias por formar parte de la red de comercio transparente de SVC.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Notificación Oficial de Reactivación de Cuenta Comercial", html)

# ── CdU07: Reactivación de Administrador ───────────────────────────────
def enviar_correo_reactivacion_admin(destinatario: str, nombre_completo: str) -> None:
    login_url = f"{FRONTEND_BASE_URL}/login.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0f172a; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .success {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0056b3; padding: 15px; margin: 20px 0; font-size: 13px; color: #0f172a; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — GESTIÓN INSTITUCIONAL</div>
            <div class="title">Credenciales Administrativas Rehabilitadas</div>
            <p class="text">Estimado/a <strong>{nombre_completo}</strong>:<br><br>Le informamos que la Administración Principal ha dispuesto la <strong>rehabilitación formal</strong> de su cuenta con privilegios de <strong>Administrador</strong>.</p>
            <div class="success">Su acceso al panel de control centralizado y a las herramientas de moderación del sistema se encuentra completamente operativo.</div>
            <p style="text-align: center; margin: 25px 0;"><a href="{login_url}" target="_blank" rel="noopener noreferrer" class="btn">Acceder al Panel de Control &rarr;</a></p>
            <div class="warn">• El levantamiento de la sanción ha sido registrado en la bitácora de auditoría.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Rehabilitación de Credenciales Administrativas", html)

# ── CdU09: Notificación de Baja de Cuenta Comercial ────────────────────
def enviar_correo_notificacion_baja(destinatario: str, razon_social: str = "Comercio") -> None:
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #6c757d; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #6c757d; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #334155; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — CUENTA DADA DE BAJA</div>
            <div class="title">Baja de Cuenta Procesada</div>
            <p class="text">Estimado/a representante de <strong>{razon_social}</strong>:<br><br>Le informamos que su cuenta comercial ha sido dada de baja voluntariamente del Sistema de Vinculación para el Comercio (SVC).</p>
            <p class="text" style="font-size: 12px;">Sus publicaciones y catálogo han sido pausados de la vista pública.</p>
            <div class="warn">• Sus datos han sido resguardados de acuerdo a las normativas de auditoría.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, "SVC - Notificación de Baja de Cuenta", html)

# ── CdU43/CdU44: Alerta Automática de Bajo Stock (RF06 / RF07) ─────────
def enviar_correo_alerta_bajo_stock(destinatario: str, razon_social: str, nombre_producto: str, stock_actual: int, stock_minimo: int) -> None:
    inv_url = f"{FRONTEND_BASE_URL}/inventario.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #ffc107; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #ffc107; color: #000000; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #b45309; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .stock-box {{ background-color: #fffbeb; border: 1px solid #fde68a; padding: 15px; margin: 20px 0; font-size: 13px; color: #92400e; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — ALERTA DE INVENTARIO</div>
            <div class="title">Advertencia de Stock Bajo</div>
            <p class="text">Estimado/a representante de <strong>{razon_social}</strong>:<br><br>Le notificamos que el producto <strong>"{nombre_producto}"</strong> ha alcanzado o cruzado su umbral mínimo de existencias en el catálogo de inventario.</p>
            <div class="stock-box">
                <strong>Existencias Actuales:</strong> {stock_actual} unidades<br>
                <strong>Umbral de Alerta Configurado:</strong> {stock_minimo} unidades
            </div>
            <p class="text">Le sugerimos realizar un ajuste de reposición de mercadería para evitar la interrupción de sus publicaciones comerciales.</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{inv_url}" target="_blank" rel="noopener noreferrer" class="btn">Gestionar mi Inventario &rarr;</a></p>
            <div class="warn">• Esta es una notificación automática generada por el módulo de inventario de SVC.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Alerta de Stock Bajo: {nombre_producto}", html)

# ── CdU32: Notificación Oficial de Baja de Publicación por Moderación (RF04) ──
def enviar_correo_eliminacion_publicacion_admin(destinatario: str, razon_social: str, titulo_publicacion: str, motivo: str) -> None:
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #dc3545; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #dc3545; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #991b1b; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .motivo {{ background-color: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; font-size: 13px; color: #7f1d1d; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — MODERACIÓN COMERCIAL</div>
            <div class="title">Publicación de Venta Retirada</div>
            <p class="text">Estimado/a representante de <strong>{razon_social}</strong>:<br><br>Le informamos que la Administración Global de SVC ha procedido a dar de baja de forma forzosa su oferta comercial titulada <strong>"{titulo_publicacion}"</strong> por infracción a las normativas de la plataforma.</p>
            <div class="motivo"><strong>Justificación de la Medida Disciplinaria:</strong><br>{motivo}</div>
            <p class="text" style="font-size: 12px;">Si la oferta se encontraba activa y vinculada a su catálogo privado, las unidades retenidas han sido devueltas automáticamente a su inventario (CdU30). La publicación ya no es visible en búsquedas ni comunidades.</p>
            <div class="warn">• Esta sanción se encuentra registrada con marca de tiempo en la bitácora de auditoría del sistema.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Notificación de Moderación: Baja de Oferta Comercial", html)

# ── CdU16: Notificación de Cambio de Nombre de Comunidad ──────────────
def enviar_correo_cambio_nombre_comunidad(
    destinatario: str, 
    nombre_anterior: str, 
    nombre_nuevo: str, 
    rubro: str
) -> None:
    comunidades_url = f"{FRONTEND_BASE_URL}/comunidades.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0056b3; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .info-box {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0056b3; padding: 15px; margin: 20px 0; font-size: 13px; color: #0f172a; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — COMUNIDADES B2B</div>
            <div class="title">Actualización en su Comunidad</div>
            <p class="text">Le informamos que un moderador del espacio comercial del cual forma parte ha actualizado la denominación de la comunidad.</p>
            <div class="info-box">
                <strong>Nombre Anterior:</strong> {nombre_anterior}<br>
                <strong>Nuevo Nombre Oficial:</strong> {nombre_nuevo}<br>
                <strong>Sector / Rubro:</strong> {rubro}
            </div>
            <p class="text" style="font-size: 12px;">Por normativas de la plataforma, el nombre de un espacio no podrá volver a modificarse durante los próximos 15 días.</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{comunidades_url}" target="_blank" rel="noopener noreferrer" class="btn">Acceder a Comunidades &rarr;</a></p>
            <div class="warn">• Esta es una notificación automática del Sistema de Vinculación para el Comercio (SVC).</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Cambio de nombre en comunidad: {nombre_nuevo}", html)

    # ── CdU17: Alerta de Nueva Solicitud de Ingreso a Comunidad ──────────
def enviar_correo_nueva_solicitud_comunidad(
    destinatario: str,
    nombre_comunidad: str,
    nombre_solicitante: str,
    rubro_solicitante: str
) -> None:
    comunidades_url = f"{FRONTEND_BASE_URL}/comunidades.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0056b3; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .info-box {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0056b3; padding: 15px; margin: 20px 0; font-size: 13px; color: #0f172a; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — GESTIÓN DE COMUNIDADES</div>
            <div class="title">Nueva Solicitud de Membresía</div>
            <p class="text">El comerciante <strong>{nombre_solicitante}</strong> ha solicitado incorporarse a la comunidad <strong>"{nombre_comunidad}"</strong>.</p>
            <div class="info-box">
                <strong>Empresa Postulante:</strong> {nombre_solicitante}<br>
                <strong>Rubro Fiscal Declarado:</strong> {rubro_solicitante}<br>
                <strong>Comunidad Destino:</strong> {nombre_comunidad}
            </div>
            <p class="text" style="font-size: 12px;">Como administrador o moderador del espacio, puede ingresar al panel para evaluar y aprobar o rechazar esta incorporación (CdU18).</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{comunidades_url}" target="_blank" rel="noopener noreferrer" class="btn">Gestionar Solicitudes &rarr;</a></p>
            <div class="warn">• Esta es una notificación oficial del Sistema de Vinculación para el Comercio (SVC).</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Nueva Solicitud de Ingreso: {nombre_comunidad}", html)

    # ── CdU18: Notificación de Resolución de Solicitud de Ingreso ─────────
def enviar_correo_resolucion_solicitud_comunidad(
    destinatario: str,
    nombre_comercio: str,
    nombre_comunidad: str,
    aprobada: bool
) -> None:
    comunidades_url = f"{FRONTEND_BASE_URL}/comunidades.html"
    color_borde = "#28a745" if aprobada else "#dc3545"
    titulo_estado = "Solicitud de Ingreso Aprobada" if aprobada else "Solicitud de Ingreso Denegada"
    mensaje_cuerpo = (
        f"Nos complace informarle que los moderadores de la comunidad <strong>\"{nombre_comunidad}\"</strong> han "
        f"<strong>aprobado</strong> su incorporación al espacio. Ya puede participar activamente y difundir sus publicaciones."
        if aprobada else
        f"Le informamos que el equipo de moderación de <strong>\"{nombre_comunidad}\"</strong> ha decidido "
        f"<strong>no aprobar</strong> su solicitud de ingreso en este momento."
    )
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid {color_borde}; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: {color_borde}; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 20px; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — COMUNIDADES B2B</div>
            <div class="title">{titulo_estado}</div>
            <p class="text">Estimado/a representante de <strong>{nombre_comercio}</strong>:<br><br>{mensaje_cuerpo}</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{comunidades_url}" target="_blank" rel="noopener noreferrer" class="btn">Explorar Comunidades &rarr;</a></p>
            <div class="warn">• Notificación generada automáticamente por la plataforma comercial SVC.</div>
        </div>
    </body>
    </html>
    """
    asunto = f"SVC — Solicitud Aprobada: {nombre_comunidad}" if aprobada else f"SVC — Solicitud Denegada: {nombre_comunidad}"
    _enviar_email_smtp(destinatario, asunto, html)

    # ── CdU20: Notificación Oficial de Expulsión de Comunidad ─────────────
def enviar_correo_expulsion_comunidad(
    destinatario: str,
    nombre_comercio: str,
    nombre_comunidad: str,
    motivo: str
) -> None:
    comunidades_url = f"{FRONTEND_BASE_URL}/comunidades.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #dc3545; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #dc3545; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #991b1b; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .motivo-box {{ background-color: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; font-size: 13px; color: #7f1d1d; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — MODERACIÓN DE COMUNIDADES</div>
            <div class="title">Expulsión de Comunidad</div>
            <p class="text">Estimado/a representante de <strong>{nombre_comercio}</strong>:<br><br>Le informamos que el equipo de moderación ha dispuesto su <strong>expulsión</strong> de la comunidad <strong>"{nombre_comunidad}"</strong>.</p>
            <div class="motivo-box">
                <strong>Justificación de la Sanción:</strong><br>{motivo}
            </div>
            <p class="text" style="font-size: 12px;">A partir de este momento, ha perdido el acceso directo al espacio y sus publicaciones han dejado de replicarse en dicho muro.</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{comunidades_url}" target="_blank" rel="noopener noreferrer" class="btn">Explorar Otras Comunidades &rarr;</a></p>
            <div class="warn">• Esta sanción ha sido registrada de forma inmutable en la bitácora de auditoría del sistema.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Notificación de Expulsión: {nombre_comunidad}", html)

    # ── CdU21: Notificación Oficial de Asignación de Rol de Moderador ─────
def enviar_correo_asignacion_moderador_comunidad(
    destinatario: str,
    nombre_comercio: str,
    nombre_comunidad: str
) -> None:
    comunidades_url = f"{FRONTEND_BASE_URL}/comunidades.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #0056b3; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .info-box {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0056b3; padding: 15px; margin: 20px 0; font-size: 13px; color: #0f172a; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — COMUNIDADES B2B</div>
            <div class="title">Designación de Moderador</div>
            <p class="text">Estimado/a representante de <strong>{nombre_comercio}</strong>:<br><br>Nos complace informarle que ha sido promovido al rol de <strong>Moderador</strong> en la comunidad <strong>"{nombre_comunidad}"</strong>.</p>
            <div class="info-box">
                <strong>Comunidad:</strong> {nombre_comunidad}<br>
                <strong>Nuevo Rango:</strong> Moderador<br>
                <strong>Nuevos Privilegios:</strong> Ahora puede evaluar solicitudes de ingreso (CdU18), expulsar miembros infractores (CdU20) y colaborar en la configuración general del espacio (CdU16).
            </div>
            <p style="text-align: center; margin: 25px 0;"><a href="{comunidades_url}" target="_blank" rel="noopener noreferrer" class="btn">Ingresar al Panel de Moderación &rarr;</a></p>
            <div class="warn">• Esta es una notificación oficial del Sistema de Vinculación para el Comercio (SVC).</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Has sido nombrado Moderador en: {nombre_comunidad}", html)

    # ── CdU22: Notificación de Revocación de Moderador ───────────────────
def enviar_correo_revocacion_moderador_comunidad(destinatario: str, nombre_comercio: str, nombre_comunidad: str) -> None:
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #64748b; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #64748b; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .info-box {{ background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #64748b; padding: 15px; margin: 20px 0; font-size: 13px; color: #0f172a; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — COMUNIDADES B2B</div>
            <div class="title">Actualización de Rango en Comunidad</div>
            <p class="text">Estimado/a representante de <strong>{nombre_comercio}</strong>:<br><br>Le informamos que sus privilegios de gestión en la comunidad <strong>"{nombre_comunidad}"</strong> han cesado, retornando su cuenta al rango de <strong>Integrante</strong> estándar.</p>
            <div class="info-box">
                <strong>Comunidad:</strong> {nombre_comunidad}<br>
                <strong>Rango Actual:</strong> Integrante<br>
                <strong>Estado:</strong> Conserva su acceso regular al espacio comercial y a la difusión de publicaciones.
            </div>
            <p style="text-align: center; margin: 25px 0;"><a href="{FRONTEND_BASE_URL}/comunidades.html" target="_blank" rel="noopener noreferrer" class="btn">Acceder a Comunidades &rarr;</a></p>
            <div class="warn">• Notificación oficial de SVC.</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Actualización de rol en comunidad: {nombre_comunidad}", html)

    # ── CdU23: Notificación a Administradores de Solicitud de Eliminación ─
def enviar_correo_solicitud_eliminacion_comunidad(
    destinatario: str,
    nombre_creador: str,
    nombre_comunidad: str,
    motivo: str
) -> None:
    admin_panel_url = f"{FRONTEND_BASE_URL}/admin-dashboard.html"
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #dc3545; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: #dc3545; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #991b1b; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 15px; }}
        .info-box {{ background-color: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; font-size: 13px; color: #7f1d1d; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — MODERACIÓN GLOBAL</div>
            <div class="title">Solicitud de Eliminación de Comunidad</div>
            <p class="text">El Creador fundador <strong>{nombre_creador}</strong> ha solicitado la baja definitiva de la comunidad <strong>"{nombre_comunidad}"</strong>.</p>
            <div class="info-box">
                <strong>Comunidad:</strong> {nombre_comunidad}<br>
                <strong>Estado:</strong> Congelada (Pendiente de eliminación)<br>
                <strong>Motivo ingresado por el Creador:</strong><br>{motivo}
            </div>
            <p class="text" style="font-size: 12px;">Como Administrador, debe evaluar esta solicitud desde el panel de control global para aprobar la baja definitiva o rechazarla y restaurar el espacio (CdU24).</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{admin_panel_url}" target="_blank" rel="noopener noreferrer" class="btn">Evaluar en Panel Admin &rarr;</a></p>
            <div class="warn">• Notificación oficial del Sistema de Vinculación para el Comercio (SVC).</div>
        </div>
    </body>
    </html>
    """
    _enviar_email_smtp(destinatario, f"SVC — Solicitud de Eliminación: {nombre_comunidad}", html)

    # ── CdU24: Notificación de Resolución de Eliminación de Comunidad ────
def enviar_correo_resolucion_eliminacion_comunidad(
    destinatario: str,
    nombre_destinatario: str,
    nombre_comunidad: str,
    aprobada: bool
) -> None:
    comunidades_url = f"{FRONTEND_BASE_URL}/comunidades.html"
    color_borde = "#dc3545" if aprobada else "#28a745"
    titulo = "Comunidad Eliminada Definitivamente" if aprobada else "Solicitud de Eliminación Rechazada"
    mensaje = (
        f"Le informamos que la Administración Global ha <strong>aprobado</strong> la solicitud de baja "
        f"para la comunidad <strong>\"{nombre_comunidad}\"</strong>. El espacio y sus enlaces comerciales han sido removidos."
        if aprobada else
        f"Le informamos que la Administración Global ha <strong>rechazado</strong> la solicitud de eliminación "
        f"para la comunidad <strong>\"{nombre_comunidad}\"</strong>. La comunidad ha sido <strong>descongelada y reactivada</strong> para operar normalmente."
    )
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"><style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
        .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid {color_borde}; padding: 30px; border-radius: 0px !important; }}
        .badge {{ background-color: {color_borde}; color: #ffffff; font-weight: bold; font-size: 13px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
        .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
        .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 20px; }}
        .btn {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
        .warn {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
    </style></head>
    <body>
        <div class="box">
            <div class="badge">SVC — ADMINISTRACIÓN GLOBAL</div>
            <div class="title">{titulo}</div>
            <p class="text">Estimado/a <strong>{nombre_destinatario}</strong>:<br><br>{mensaje}</p>
            <p style="text-align: center; margin: 25px 0;"><a href="{comunidades_url}" target="_blank" rel="noopener noreferrer" class="btn">Ir a Comunidades &rarr;</a></p>
            <div class="warn">• Notificación oficial de resolución de gobernanza emitida por SVC.</div>
        </div>
    </body>
    </html>
    """
    asunto = f"SVC — Resolución de Eliminación: {nombre_comunidad}"
    _enviar_email_smtp(destinatario, asunto, html)