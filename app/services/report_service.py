import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

logger = logging.getLogger(__name__)

REPORTS_DIR = "reports"
BRAND_COLOR = colors.HexColor("#1a3c5e")
LIGHT_COLOR = colors.HexColor("#f0f4f8")


class ReportService:

    def _ensure_reports_dir(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def generate_invoice(self, context: dict) -> str:
        self._ensure_reports_dir()

        filename = f"invoice_{context['booking_code']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", fontSize=20, textColor=BRAND_COLOR, spaceAfter=4)
        subtitle_style = ParagraphStyle("subtitle", fontSize=10, textColor=colors.grey)
        heading_style = ParagraphStyle("heading", fontSize=11, textColor=BRAND_COLOR, spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
        normal_style = ParagraphStyle("normal", fontSize=10)

        elements = []

        # Header
        elements.append(Paragraph("🏨 Hotel Management System", title_style))
        elements.append(Paragraph("Jl. Contoh No. 123, Jakarta | Tel: (021) 123-4567", subtitle_style))
        elements.append(Spacer(1, 0.5*cm))

        # Invoice title
        elements.append(Paragraph("INVOICE", ParagraphStyle("inv", fontSize=24, textColor=BRAND_COLOR, alignment=TA_RIGHT)))
        elements.append(Paragraph(f"No: {context['booking_code']}", ParagraphStyle("code", fontSize=10, alignment=TA_RIGHT)))
        elements.append(Paragraph(f"Tanggal: {context['invoice_date']}", ParagraphStyle("date", fontSize=10, alignment=TA_RIGHT)))
        elements.append(Spacer(1, 0.5*cm))

        # Guest info
        elements.append(Paragraph("Tagihan Kepada:", heading_style))
        elements.append(Paragraph(f"<b>{context['guest_name']}</b>", normal_style))
        elements.append(Paragraph(context['guest_email'], normal_style))
        if context.get('guest_phone'):
            elements.append(Paragraph(context['guest_phone'], normal_style))
        elements.append(Spacer(1, 0.5*cm))

        # Booking detail table
        elements.append(Paragraph("Detail Menginap:", heading_style))
        booking_data = [
            ["Deskripsi", "Check-in", "Check-out", "Malam", "Harga/Malam", "Total"],
            [
                f"Kamar {context['room_number']}\n({context['room_type'].title()})",
                context['check_in_date'],
                context['check_out_date'],
                str(context['total_nights']),
                f"Rp {context['price_per_night']:,.0f}",
                f"Rp {context['total_amount']:,.0f}",
            ],
        ]
        booking_table = Table(booking_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 3*cm])
        booking_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 1), (-1, -1), LIGHT_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_COLOR]),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(booking_table)
        elements.append(Spacer(1, 0.3*cm))

        # Total
        total_data = [
            ["", "Subtotal", f"Rp {context['total_amount']:,.0f}"],
            ["", "Pajak (0%)", "Rp 0"],
            ["", "TOTAL", f"Rp {context['total_amount']:,.0f}"],
        ]
        total_table = Table(total_data, colWidths=[9.5*cm, 3*cm, 4*cm])
        total_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTNAME", (1, 2), (-1, 2), "Helvetica-Bold"),
            ("TEXTCOLOR", (1, 2), (-1, 2), BRAND_COLOR),
            ("LINEABOVE", (1, 2), (-1, 2), 1, BRAND_COLOR),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 0.5*cm))

        # Payment info
        elements.append(Paragraph("Informasi Pembayaran:", heading_style))
        payment_data = [
            ["Metode Pembayaran", "Tanggal Bayar", "Status"],
            [context['payment_method'].title(), context['payment_date'], "LUNAS"],
        ]
        payment_table = Table(payment_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
        payment_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 1), (-1, -1), LIGHT_COLOR),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 1*cm))

        # Footer
        elements.append(Paragraph(
            "Terima kasih telah menginap di Hotel Management System.",
            ParagraphStyle("footer", fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(elements)
        logger.info(f"Invoice PDF generated: {filepath}")
        return filepath

    def generate_monthly_report(self, context: dict, period: str) -> str:
        self._ensure_reports_dir()

        filename = f"report_monthly_{period}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle("heading", fontSize=11, textColor=BRAND_COLOR, spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold")
        normal_style = ParagraphStyle("normal", fontSize=10)

        elements = []

        # Header
        elements.append(Paragraph("🏨 Laporan Okupansi Bulanan", ParagraphStyle("title", fontSize=18, textColor=colors.white)))
        elements.append(Paragraph(f"Periode: {context['period']} | Digenerate: {context['generated_at']}", ParagraphStyle("sub", fontSize=10, textColor=BRAND_COLOR)))
        elements.append(Spacer(1, 0.5*cm))

        # Summary stats
        elements.append(Paragraph("Ringkasan:", heading_style))
        stats_data = [
            ["Total Booking", "Total Revenue", "Check-out", "Cancellations"],
            [
                str(context['total_bookings']),
                f"Rp {context['total_revenue']:,.0f}",
                str(context['total_checkouts']),
                str(context['total_cancellations']),
            ],
        ]
        stats_table = Table(stats_data, colWidths=[4*cm, 5*cm, 4*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("BACKGROUND", (0, 1), (-1, -1), LIGHT_COLOR),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 0.5*cm))

        # Room type stats
        elements.append(Paragraph("Booking per Tipe Kamar:", heading_style))
        rt_data = [["Tipe Kamar", "Jumlah Booking", "Total Revenue", "Rata-rata"]]
        for item in context['room_type_stats']:
            rt_data.append([
                item['room_type'].title(),
                str(item['booking_count']),
                f"Rp {item['revenue']:,.0f}",
                f"Rp {item['avg_per_booking']:,.0f}",
            ])
        rt_table = Table(rt_data, colWidths=[4*cm, 3.5*cm, 5*cm, 4*cm])
        rt_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_COLOR]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(rt_table)
        elements.append(Spacer(1, 0.5*cm))

        # Booking detail
        elements.append(Paragraph("Detail Booking:", heading_style))
        detail_data = [["Kode", "Guest", "Kamar", "Check-in", "Check-out", "Total", "Status"]]
        for b in context['bookings']:
            detail_data.append([
                b['booking_code'],
                b['guest_name'],
                b['room_number'],
                b['check_in_date'],
                b['check_out_date'],
                f"Rp {b['total_amount']:,.0f}",
                b['status'].title(),
            ])
        detail_table = Table(detail_data, colWidths=[2.5*cm, 3*cm, 1.5*cm, 2.2*cm, 2.2*cm, 3*cm, 2*cm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_COLOR]),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(detail_table)

        doc.build(elements)
        logger.info(f"Monthly report PDF generated: {filepath}")
        return filepath


report_service = ReportService()