import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header
from dotenv import load_dotenv

class EmailNotifier:
    def __init__(self):
        load_dotenv()
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        spm_email_raw = os.getenv("SPM_EMAIL")
        self.spm_email = spm_email_raw.strip() if spm_email_raw else ""
        
        self.spm_password = os.getenv("SPM_PASSWORD")
        
        personal_email_raw = os.getenv("PERSONAL_EMAIL")
        self.personal_email = personal_email_raw.strip() if personal_email_raw else ""

    def enviar_oferta(self, titulo: str, empresa: str, score: int, url: str, pdf_path: str):
        if not self.spm_email or not self.personal_email:
            raise ValueError("Las direcciones de correo (SPM_EMAIL o PERSONAL_EMAIL) están vacías o no se encontraron en el archivo .env")
            
        if not self.spm_password:
            print("Faltan credenciales de correo (contraseña) en el archivo .env")
            return

        msg = MIMEMultipart()
        msg['From'] = self.spm_email
        msg['To'] = self.personal_email
        msg['Subject'] = Header(f"¡Match de Empleo Encontrado! {titulo} en {empresa} (Score: {score})", 'utf-8')

        body = f"""
        Hola,

        He encontrado una oferta de trabajo que hace un excelente match con tu perfil.

        Detalles de la oferta:
        - Título: {titulo}
        - Empresa: {empresa}
        - Score de Match: {score}/100
        - Enlace: {url}

        Adjunto encontrarás tu Hoja de Vida adaptada específicamente para esta oferta.

        ¡Mucho éxito en tu aplicación!
        """
        msg.attach(MIMEText(body, 'plain'))

        # Adjuntar PDF
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(pdf_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(pdf_path)}"'
            msg.attach(part)
        else:
            print(f"Advertencia: No se encontró el archivo PDF en {pdf_path}")

        try:
            # Conectar al servidor SMTP
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            server.login(self.spm_email, self.spm_password)
            server.send_message(msg)
            server.quit()
            print(f"Correo enviado exitosamente para la oferta: {titulo} en {empresa}")
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
