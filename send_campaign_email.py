"""
Script para enviar email de campaña de servicios devLink
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Configuración SMTP
SMTP_SERVER = "c2641734.ferozo.com"
SMTP_PORT = 465
SMTP_USER = "info@devlink.com.ar"
SMTP_PASSWORD = "@Inf124578"  # Contraseña del correo

# Destinatarios
TO_EMAILS = ["eudyespinoza@gmail.com"]

# Leer el HTML del email
html_path = Path(__file__).parent / "templates" / "email-campana-servicios-inline.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Versión texto plano (alternativa)
text_content = """
devLink - Soluciones Digitales a Tu Medida

¿Tu negocio necesita dar el salto digital?

En devLink transformamos tus ideas en soluciones tecnológicas:

✓ Desarrollo de Aplicaciones a Medida
✓ Chatbots con Inteligencia Artificial (WhatsApp Business)
✓ Páginas Web Profesionales

¿Listo para transformar tu negocio?
Agendá una consulta gratuita: https://devlink.com.ar/#contacto

Contacto:
📧 info@devlink.com.ar
📱 +54 343 452 4773
📱 +54 376 414 2176
🌐 www.devlink.com.ar

© 2025 devLink. Todos los derechos reservados.
"""

# Enviar email a múltiples destinatarios
print(f"Conectando a {SMTP_SERVER}:{SMTP_PORT}...")
try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.set_debuglevel(1)  # Activar debug
        print("Autenticando...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        for email in TO_EMAILS:
            # Crear mensaje para cada destinatario
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Soluciones tecnológicas para optimizar tu operación | devLink"
            msg["From"] = f"devLink <{SMTP_USER}>"
            msg["To"] = email
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            print(f"Enviando email a {email}...")
            result = server.sendmail(SMTP_USER, email, msg.as_string())
            print(f"✅ Email enviado a {email}")
        
        print("✅ Todos los emails enviados exitosamente!")
except Exception as e:
    print(f"❌ Error al enviar: {e}")
    import traceback
    traceback.print_exc()
