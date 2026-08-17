import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "file:///C:/Users/ponce/SVC/svc-frontend")

def enviar_correo_recuperacion(destinatario: str, token: str) -> None:
    """
    Despacha el correo de recuperación mediante protocolo SMTP (ERS Secc. 3.9.4).
    Lanza una excepción si la autenticación con el servidor de correo falla.
    """
    reset_url = f"{FRONTEND_BASE_URL}/reset-password.html?token={token}"
    
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = "SVC - Recuperación de Contraseña de Acceso"
    mensaje["From"] = f"Sistema de Vinculación para el Comercio <{SMTP_FROM_EMAIL}>"
    mensaje["To"] = destinatario

    # Plantilla HTML con Global Design System de SVC (border-radius: 0px, #0056b3)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Inter', Arial, sans-serif; background-color: #f8f9fa; color: #212529; margin: 0; padding: 20px; }}
            .email-container {{ max-width: 540px; margin: 0 auto; background: #ffffff; border: 1px solid #ced4da; border-top: 4px solid #0056b3; padding: 30px; border-radius: 0px !important; }}
            .brand-badge {{ background-color: #0056b3; color: #ffffff; font-weight: bold; font-size: 14px; padding: 6px 10px; display: inline-block; border-radius: 0px !important; }}
            .title {{ font-size: 20px; font-weight: bold; color: #0f172a; margin: 20px 0 10px 0; }}
            .text {{ font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 20px; }}
            .btn-action {{ display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; text-decoration: none; font-weight: bold; font-size: 13px; text-transform: uppercase; border-radius: 0px !important; }}
            .warning {{ font-size: 11px; color: #6c757d; margin-top: 25px; border-top: 1px solid #e9ecef; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="brand-badge">SVC</div>
            <div class="title">Restablecimiento de Contraseña</div>
            <p class="text">
                Hemos recibido una solicitud para restablecer la contraseña asociada a la cuenta <strong>{destinatario}</strong> en el <strong>Sistema de Vinculación para el Comercio (SVC)</strong>.
            </p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" class="btn-action">Restablecer mi Contraseña &rarr;</a>
            </p>
            <p class="text" style="font-size: 12px;">
                Si el botón no responde, copie y pegue el siguiente enlace en su navegador:<br>
                <span style="color: #0056b3; word-break: break-all;">{reset_url}</span>
            </p>
            <div class="warning">
                • Este enlace posee una validez estricta de <strong>30 minutos</strong>.<br>
                • Si usted no solicitó este cambio, ignore este mensaje. Su cuenta permanecerá segura.
            </div>
        </div>
    </body>
    </html>
    """

    mensaje.attach(MIMEText(html_content, "html"))

    # Conexión SMTP con STARTTLS
    servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
    servidor.starttls()
    servidor.login(SMTP_USER, SMTP_PASSWORD)
    servidor.sendmail(SMTP_FROM_EMAIL, destinatario, mensaje.as_string())
    servidor.quit()