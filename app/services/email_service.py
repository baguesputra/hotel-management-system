import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.config import settings

logger = logging.getLogger(__name__)

# setup Jinja2 untuk load template dari folder templates/
jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)


class EmailService:

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render HTML template dengan context data."""
        template = jinja_env.get_template(template_name)
        return template.render(**context)

    def send(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        template_name: str,
        context: dict,
    ) -> bool:
        """
        Kirim email via SMTP.
        Return True jika sukses, False jika gagal.
        Ini synchronous karena dipanggil dari dalam Celery worker.
        """
        try:
            html_content = self._render_template(template_name, context)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.mail_from_name} <{settings.mail_from}>"
            msg["To"] = f"{to_name} <{to_email}>"

            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
                server.starttls()
                server.login(settings.mail_username, settings.mail_password)
                server.sendmail(settings.mail_from, to_email, msg.as_string())

            logger.info(f"Email terkirim ke {to_email} - subject: {subject}")
            return True

        except Exception as e:
            logger.error(f"Gagal kirim email ke {to_email}: {str(e)}")
            raise


email_service = EmailService()