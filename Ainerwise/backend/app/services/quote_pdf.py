import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_quote_pdf(quote: dict, lead: dict | None = None) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "QuoteTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=4 * mm,
        textColor=colors.HexColor("#1a365d"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#4a5568"),
        spaceAfter=2 * mm,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        textColor=colors.HexColor("#2d3748"),
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#718096"),
    )

    # Header
    story.append(Paragraph("AinerWise", title_style))
    story.append(Paragraph("Smart Building &amp; Energy Integration", subtitle_style))
    story.append(Spacer(1, 4 * mm))

    # Quote meta
    quote_id_short = str(quote.get("id", ""))[:8]
    meta_data = [
        ["Quote Reference:", f"Q-{quote_id_short.upper()}"],
        ["Status:", str(quote.get("status", "draft")).replace("_", " ").title()],
        ["Currency:", quote.get("currency", "EUR")],
        ["Date:", str(date.today())],
        ["Valid Until:", str(quote.get("valid_until", "-"))],
    ]
    meta_table = Table(meta_data, colWidths=[35 * mm, 80 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4a5568")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)

    # Lead / Client info
    if lead:
        story.append(Spacer(1, 4 * mm))
        client_data = []
        if lead.get("contact_name"):
            client_data.append(["Client:", lead["contact_name"]])
        if lead.get("contact_email"):
            client_data.append(["Email:", lead["contact_email"]])
        if lead.get("country") or lead.get("city"):
            location = f"{lead.get('city', '')} {lead.get('country', '')}".strip()
            client_data.append(["Location:", location])
        if lead.get("project_type"):
            client_data.append(["Project Type:", lead["project_type"]])
        if client_data:
            client_table = Table(client_data, colWidths=[35 * mm, 80 * mm])
            client_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4a5568")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(client_table)

    # Line items
    items = quote.get("quote_items_json") or []
    if items:
        story.append(Paragraph("Line Items", section_style))

        header = ["#", "Description", "Category", "Qty", "Unit Price", "Subtotal"]
        table_data = [header]
        for i, item in enumerate(items, 1):
            table_data.append([
                str(i),
                str(item.get("description", "")),
                str(item.get("category", "")),
                str(item.get("quantity", 1)),
                f"{item.get('unit_price', 0):,.2f}",
                f"{item.get('subtotal', 0):,.2f}",
            ])

        col_widths = [8 * mm, 65 * mm, 25 * mm, 15 * mm, 25 * mm, 25 * mm]
        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(items_table)

    currency = quote.get("currency", "EUR")

    # Customer-facing solution packages (FI.4.4 / FI.4.7) — no supplier cost/model.
    packages = quote.get("customer_line_items_json") or []
    if packages:
        story.append(Paragraph("Solution Packages", section_style))
        pkg_data = [["Package", "Amount"]]
        for pkg in packages:
            pkg_data.append([str(pkg.get("label", "")), str(pkg.get("display", ""))])
        pkg_table = Table(pkg_data, colWidths=[95 * mm, 40 * mm])
        pkg_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(pkg_table)

        # Lifecycle / recurring totals
        fy = quote.get("first_year_total", 0) or 0
        ar = quote.get("annual_recurring_total", 0) or 0
        if fy or ar:
            story.append(Spacer(1, 3 * mm))
            life_rows = [
                ["Estimated First-Year Total:", f"{fy:,.2f} {currency}"],
                ["Estimated Annual Recurring:", f"{ar:,.2f} {currency}"],
            ]
            life_table = Table(life_rows, colWidths=[55 * mm, 40 * mm])
            life_table.setStyle(TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(life_table)

    # Cost summary
    story.append(Paragraph("Cost Summary", section_style))
    summary_rows = [
        ["Device Total:", f"{quote.get('device_total', 0):,.2f} {currency}"],
        ["Service Total:", f"{quote.get('service_total', 0):,.2f} {currency}"],
        ["Platform Fee:", f"{quote.get('platform_fee', 0):,.2f} {currency}"],
        ["Support Package:", f"{quote.get('support_package_fee', 0):,.2f} {currency}"],
        ["Spare Parts:", f"{quote.get('spare_parts_fee', 0):,.2f} {currency}"],
        ["Logistics:", f"{quote.get('logistics_fee', 0):,.2f} {currency}"],
        ["Tax:", f"{quote.get('tax_fee', 0):,.2f} {currency}"],
        ["Discount:", f"-{quote.get('discount', 0):,.2f} {currency}"],
    ]
    # Filter out zero rows except total
    summary_rows = [r for r in summary_rows if not r[1].startswith("0.00") and not r[1].startswith("-0.00")]
    summary_rows.append(["TOTAL:", f"{quote.get('total', 0):,.2f} {currency}"])

    summary_table = Table(summary_rows, colWidths=[45 * mm, 40 * mm])
    summary_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#2d3748")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(summary_table)

    # Notes
    if quote.get("notes"):
        story.append(Paragraph("Notes", section_style))
        for line in quote["notes"].split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), body_style))

    # Footer disclaimer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "This quote is a preliminary estimate. Final pricing may vary based on site survey, "
        "engineering review, and supplier confirmation. All prices exclude customs duties unless "
        "otherwise stated. Payment terms: as per contract agreement.",
        small_style,
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "AinerWise d.o.o. | Smart Building &amp; Energy Integration | www.ainerwise.com",
        small_style,
    ))

    doc.build(story)
    return buf.getvalue()
