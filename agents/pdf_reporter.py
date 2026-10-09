"""
PDF Report Generator for TaxOptimAI
Generates a professional PDF report from agent results.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from datetime import datetime
import io

# Modern Corporate Color Palette
NAVY_BLUE = HexColor("#1B365D")  # Deep Navy Blue for headers
SLATE_GRAY = HexColor("#64748B")  # Slate Gray for text
MUTED_TEAL = HexColor("#A7F3D0")  # Muted pastel Teal for highlights
MUTED_GREEN = HexColor("#86EFAC")  # Muted pastel Green for positive
LIGHT_GRAY = HexColor("#F1F5F9")  # Light gray for backgrounds
DARK_GRAY = HexColor("#334155")  # Dark gray for emphasis


def generate_pdf_report(
    profile: dict,
    strategies: list,
    simulation: dict,
    risks: list,
    report_text: str,
) -> bytes:
    """
    Generate a professional PDF report.
    Returns PDF as bytes (use with st.download_button).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Custom styles ──────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Normal"],
        fontSize=24, fontName="Helvetica-Bold",
        textColor=NAVY_BLUE, spaceAfter=12, alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=12, textColor=SLATE_GRAY,
        spaceAfter=6, alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=NAVY_BLUE, spaceBefore=20, spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=DARK_GRAY,
        spaceAfter=8, leading=16,  # Increased leading for better readability
    )
    small_style = ParagraphStyle(
        "Small", parent=styles["Normal"],
        fontSize=9, textColor=SLATE_GRAY, spaceAfter=4,
    )
    warning_style = ParagraphStyle(
        "Warning", parent=styles["Normal"],
        fontSize=9, textColor=SLATE_GRAY,
        spaceAfter=4, leftIndent=10,
    )

    # ── Cover Page ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("TaxOptimAI", title_style))
    story.append(Paragraph("Rapport d'Optimisation Fiscale — Tunisie 2025", subtitle_style))
    story.append(Spacer(1, 1*cm))

    # User profile summary on cover
    family_labels = {
        "single": "Célibataire",
        "married": "Marié(e) sans enfants",
        "married_with_children": "Marié(e) avec enfants",
    }
    income_labels = {
        "employee": "Salarié(e)",
        "freelancer": "Freelancer / Indépendant(e)",
    }

    cover_profile = [
        ["Type de revenu", income_labels.get(profile.get("income_type",""), "N/A")],
        ["Revenu annuel brut", f"{profile.get('gross_annual', 0):,.0f} DT"],
        ["Situation familiale", family_labels.get(profile.get("family_status",""), "N/A")],
        ["Nombre d'enfants", str(profile.get("children_count", 0))],
    ]

    cover_table = Table(cover_profile, colWidths=[6*cm, 8*cm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_GRAY),
        ("TEXTCOLOR",    (0, 0), (-1, -1), DARK_GRAY),
        ("FONTNAME",     (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 0), (-1, -1), 11),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ("GRID",         (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),  # Light horizontal lines
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        small_style
    ))
    story.append(Paragraph(
        "Loi de Finances n°2024-48 du 9 décembre 2024",
        small_style
    ))
    story.append(PageBreak())

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Rapport d'Analyse Fiscale Détaillée", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_BLUE, spaceAfter=15))

    # ── Profile Summary ───────────────────────────────────────────────────────
    story.append(Paragraph("Profil Financier", heading_style))

    profile_data = [
        ["Paramètre", "Valeur"],
        ["Type de revenu", income_labels.get(profile.get("income_type",""), "N/A")],
        ["Revenu annuel brut", f"{profile.get('gross_annual', 0):,.0f} DT"],
        ["Revenu mensuel brut", f"{profile.get('gross_monthly', 0):,.0f} DT"],
        ["Situation familiale", family_labels.get(profile.get("family_status",""), "N/A")],
        ["Nombre d'enfants", str(profile.get("children_count", 0))],
    ]

    profile_table = Table(profile_data, colWidths=[8*cm, 8*cm])
    profile_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY_BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0), white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 10),
        ("BACKGROUND",   (0, 1), (-1, -1), MUTED_TEAL),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [MUTED_TEAL, white]),
        ("FONTSIZE",     (0, 1), (-1, -1), 10),
        ("GRID",         (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),  # Light horizontal lines only
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
    ]))
    story.append(profile_table)

    # ── Simulation Results ────────────────────────────────────────────────────
    story.append(Paragraph("Résultats de Simulation", heading_style))

    sim = simulation or {}
    current_tax  = sim.get("current_tax", 0)
    optimized    = sim.get("optimized_tax", 0)
    savings      = sim.get("savings", 0)
    cnss         = sim.get("current_cnss_annual", 0)
    savings_pct  = (savings / current_tax * 100) if current_tax > 0 else 0

    sim_data = [
        ["Indicateur", "Montant", "Note"],
        ["IRPP actuel",       f"{current_tax:,.2f} DT",  "Calculé selon barème LF 2025"],
        ["IRPP optimisé",     f"{optimized:,.2f} DT",    "Après application des stratégies"],
        ["Économies annuelles", f"{savings:,.2f} DT",    f"Réduction de {savings_pct:.1f}%"],
        ["CNSS annuelle",     f"{cnss:,.2f} DT",         "Cotisations sociales"],
    ]

    sim_table = Table(sim_data, colWidths=[6*cm, 5*cm, 6*cm])
    sim_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [MUTED_GREEN, white]),
        ("BACKGROUND",    (0, 3), (-1, 3), MUTED_TEAL),
        ("FONTNAME",      (0, 3), (1, 3), "Helvetica-Bold"),
        ("TEXTCOLOR",     (0, 3), (1, 3), NAVY_BLUE),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("GRID",          (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),  # Light horizontal lines
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("ALIGN",         (0, 0), (0, -1), "LEFT"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(sim_table)

    # ── Strategies ────────────────────────────────────────────────────────────
    if strategies:
        story.append(Paragraph("Stratégies Recommandées", heading_style))

        risk_colors = {"low": MUTED_GREEN, "medium": HexColor("#FED7AA"), "high": HexColor("#FECACA")}
        risk_labels = {"low": "Faible", "medium": "Moyen", "high": "Élevé"}

        strat_data = [["#", "Type", "Description", "Économies", "Risque"]]
        for i, s in enumerate(strategies, 1):
            stype = s.get("strategy_type","").replace("_"," ").title()
            desc  = s.get("description","")[:80] + "..." if len(s.get("description","")) > 80 else s.get("description","")
            est   = f"{s.get('expected_savings', 0):,.0f} DT"
            risk  = risk_labels.get(s.get("risk_level",""), "N/A")
            strat_data.append([str(i), stype, desc, est, risk])

        strat_table = Table(strat_data, colWidths=[0.8*cm, 3.5*cm, 7*cm, 2.5*cm, 2.2*cm])
        strat_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY_BLUE),
            ("TEXTCOLOR",     (0, 0), (-1, 0), white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0), 9),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LIGHT_GRAY, white]),
            ("GRID",          (0, 0), (-1, -1), 0.5, HexColor("#E2E8F0")),  # Light horizontal lines
            ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
            ("ALIGN",         (3, 0), (3, -1), "RIGHT"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(strat_table)

    # ── Risk Assessment ───────────────────────────────────────────────────────
    if risks:
        story.append(Paragraph("Évaluation de Conformité", heading_style))
        for r in risks:
            level = r.get("risk_level","medium")
            color = risk_colors.get(level, SLATE_GRAY)
            recs  = r.get("recommendations", [])
            issues = r.get("issues", [])
            for rec in recs:
                story.append(Paragraph(f"→ {rec}", body_style))
            for iss in issues:
                story.append(Paragraph(f"⚠ {iss}", warning_style))

    # ── Detailed Report ───────────────────────────────────────────────────────
    if report_text:
        story.append(Paragraph("Analyse Détaillée", heading_style))
        # Clean markdown formatting
        import re
        clean = re.sub(r'\*\*(.+?)\*\*', r'\1', report_text)
        clean = re.sub(r'\*(.+?)\*', r'\1', clean)
        clean = re.sub(r'#{1,3}\s+', '', clean)
        for para in clean.split('\n'):
            para = para.strip()
            if para:
                story.append(Paragraph(para, body_style))

    # ── Footer disclaimer ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=SLATE_GRAY, spaceAfter=8))
    story.append(Paragraph(
        "Ce rapport est généré automatiquement par TaxOptimAI à titre informatif. "
        "Il ne constitue pas un conseil fiscal professionnel. "
        "Consultez un expert-comptable agréé pour validation.",
        small_style
    ))
    story.append(Paragraph(
        f"Sources : Code IRPP & IS 2025 · Code TVA 2024 · CDPF 2025 · LF n°2024-48 | "
        f"Calculé le {datetime.now().strftime('%d/%m/%Y')}",
        small_style
    ))

    doc.build(story)
    return buffer.getvalue()