import os
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from app.core.config import settings

logger = logging.getLogger(__name__)

jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)

REPORTS_DIR = "reports"


class ReportService:

    def _ensure_reports_dir(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate_invoice(self, context: dict) -> str:
        """
        Generate invoice PDF dari context data.
        Return path file PDF yang dihasilkan.
        """
        self._ensure_reports_dir()

        template = jinja_env.get_template("invoice.html")
        html_content = template.render(**context)

        filename = f"invoice_{context['booking_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        HTML(string=html_content).write_pdf(filepath)
        logger.info(f"Invoice PDF generated: {filepath}")
        return filepath

    def generate_monthly_report(self, context: dict, period: str) -> str:
        """
        Generate monthly occupancy report PDF.
        Return path file PDF yang dihasilkan.
        """
        self._ensure_reports_dir()

        template = jinja_env.get_template("monthly_report.html")
        html_content = template.render(**context)

        filename = f"report_monthly_{period}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        HTML(string=html_content).write_pdf(filepath)
        logger.info(f"Monthly report PDF generated: {filepath}")
        return filepath


report_service = ReportService()