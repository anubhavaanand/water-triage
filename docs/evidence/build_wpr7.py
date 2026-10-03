import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 20, page_text)
        self.drawString(36, 20, "WaterTriage — Minor Project (ETMN100) | WPR-7: Discussion & Comparative Analysis")
        self.setStrokeColor(colors.HexColor("#cccccc"))
        self.setLineWidth(0.5)
        self.line(36, 30, A4[0] - 36, 30)
        self.restoreState()

def build_pdf():
    pdf_path = "/home/anubhavanand/Documents/NTCC minor project/reports/WPR_7_Anubhav_Anand.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=1, # Center
        textColor=colors.HexColor('#111827')
    )
    
    sub_style = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#374151')
    )
    
    meta_label = ParagraphStyle('MetaLabel', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#1f2937'))
    meta_val = ParagraphStyle('MetaVal', fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#374151'))
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#0f766e'), # Teal
        spaceBefore=8,
        spaceAfter=4
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=5,
        spaceAfter=3
    )

    body = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=4
    )
    
    bullet = ParagraphStyle(
        'Bullet_Custom',
        parent=body,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    tbl_head = ParagraphStyle('TblHead', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.white, alignment=1)
    tbl_cell = ParagraphStyle('TblCell', fontName='Helvetica', fontSize=7, leading=8.5, textColor=colors.HexColor('#111827'))
    tbl_cell_bold = ParagraphStyle('TblCellBold', fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=colors.HexColor('#111827'))

    story = []

    # Header
    story.append(Paragraph("AMITY SCHOOL OF ENGINEERING & TECHNOLOGY", title_style))
    story.append(Paragraph("Amity University Uttar Pradesh, Greater Noida", sub_style))
    story.append(Paragraph("Minor Project (ETMN100) — WEEKLY PROGRESS REPORT (WPR) – 7", ParagraphStyle('WPRTitle', parent=title_style, fontSize=11, textColor=colors.HexColor('#0f766e'), spaceBefore=2)))
    story.append(Spacer(1, 6))

    # Meta Table
    meta_data = [
        [Paragraph("<b>Week:</b> 31/08/2026 – 06/09/2026", meta_val), Paragraph("<b>Enrollment No:</b> A41105223039", meta_val)],
        [Paragraph("<b>Student Name:</b> Anubhav Anand", meta_val), Paragraph("<b>Program:</b> B.Tech CSE (Batch 2027)", meta_val)],
        [Paragraph("<b>Faculty Guide:</b> Dr. Girish Paliwal", meta_val), Paragraph("<b>Topic:</b> Discussion & Comparative Analysis", meta_val)],
        [Paragraph("<b>Project:</b> WaterTriage: Data-Driven Water Quality Risk Scoring for UP & Bihar", meta_val), Paragraph("<b>Status:</b> On Schedule", meta_val)]
    ]
    t_meta = Table(meta_data, colWidths=[280, 243])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6))

    # Targets Set
    story.append(Paragraph("TARGETS SET FOR THE WEEK", h1_style))
    story.append(Paragraph("• Perform comparative hydrochemical synthesis between Uttar Pradesh and Bihar across 1,359 lab samples and 5,718 parameter readings.", bullet))
    story.append(Paragraph("• Mathematically evaluate and validate the Acute Hazard Escalation Rule against conventional arithmetic WQI dilution.", bullet))
    story.append(Paragraph("• Analyze temporal recurrence metrics across 100,690 historical contamination events (2009–2012) to identify persistent aquifer failure epicenters.", bullet))
    story.append(Paragraph("• Synthesize actionable engineering and policy intervention matrix for Jal Jeevan Mission (JJM), detailing CapEx, OpEx, and feasibility.", bullet))
    story.append(Spacer(1, 4))

    # Achievements
    story.append(Paragraph("ACHIEVEMENTS FOR THE WEEK", h1_style))
    story.append(Paragraph("1. Comparative Hydrochemical Analysis: The Indo-Gangetic Divide", h2_style))
    story.append(Paragraph("Analysis of 1,359 validated samples (747 UP, 612 Bihar) containing 5,718 discrete readings confirms distinct hydrochemical regimes across the Gangetic basin. UP exhibits severe geogenic Fluoride ($F^- > 1.5$ mg/L in Unnao/Firozabad) and non-point agricultural Nitrate ($\text{NO}_3^- > 45$ mg/L). In contrast, Bihar's reducing alluvial aquifers exhibit pervasive dissolved Iron ($\text{Fe} > 2.5$ mg/L in Purnia/Katihar) and localized floodplain Arsenic ($\text{As} > 0.05$ mg/L along Buxar-Bhagalpur belt).", body))

    # Table 1
    t1_data = [
        [Paragraph("Metric / Parameter", tbl_head), Paragraph("Uttar Pradesh (UP)", tbl_head), Paragraph("Bihar", tbl_head), Paragraph("Regional Hydrochemical Determinants", tbl_head)],
        [Paragraph("Total Scored Samples", tbl_cell_bold), Paragraph("747", tbl_cell), Paragraph("612", tbl_cell), Paragraph("Live WQMIS ingestion across priority districts", tbl_cell)],
        [Paragraph("Mean Composite Risk (CRS)", tbl_cell_bold), Paragraph("14.30", tbl_cell), Paragraph("8.83", tbl_cell), Paragraph("UP has broader co-occurrence of multiple contaminants", tbl_cell)],
        [Paragraph("Critical Band (CRS ≥ 75)", tbl_cell_bold), Paragraph("14 (1.9%)", tbl_cell), Paragraph("8 (1.3%)", tbl_cell), Paragraph("Acute pathogens (E. coli) & toxic Arsenic triggers", tbl_cell)],
        [Paragraph("High Severity (50 ≤ CRS < 75)", tbl_cell_bold), Paragraph("337 (45.1%)", tbl_cell), Paragraph("156 (25.5%)", tbl_cell), Paragraph("Geogenic Fluoride, Iron, & agricultural Nitrates", tbl_cell)],
        [Paragraph("Low / Compliant (CRS < 25)", tbl_cell_bold), Paragraph("385 (51.5%)", tbl_cell), Paragraph("448 (73.2%)", tbl_cell), Paragraph("Baseline compliant drinking water sources", tbl_cell)],
        [Paragraph("Dominant Contaminant", tbl_cell_bold), Paragraph("Fluoride (F⁻) & Nitrate (NO₃⁻)", tbl_cell), Paragraph("Iron (Fe) & Arsenic (As)", tbl_cell), Paragraph("Basement granites vs Holocene reducing floodplains", tbl_cell)]
    ]
    t1 = Table(t1_data, colWidths=[110, 85, 75, 253])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f766e')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t1)
    story.append(Spacer(1, 6))

    # Escalation Rule Validation
    story.append(Paragraph("2. Validation of the Acute Hazard Escalation Invariant", h2_style))
    story.append(Paragraph("Conventional arithmetic Water Quality Indices suffer from the <i>dilution (eclipsing) flaw</i>: a single lethal toxin (e.g., Arsenic at 0.08 mg/L, 8× BIS limit) is mathematically masked if other parameters (pH, TDS, Turbidity) are normal, yielding a misleading 'Good' score (~32/100). WaterTriage enforces an <b>Acute Hazard Escalation Invariant</b>: any Category-1 carcinogen (Arsenic ≥ 0.05 mg/L) or acute pathogen (E. coli > 0) immediately forces the composite score to Critical (CRS ≥ 75.0). This invariant rescued <b>22 habitations</b> across UP and Bihar from dangerous false-negative classification.", body))

    # Recurrence & Case Study
    story.append(Paragraph("3. Recurrence Dynamics & Chronic Hotspots: Khokha Case Study", h2_style))
    story.append(Paragraph("Evaluating 100,690 historical contamination records (2009–2012) across 14,044 villages demonstrates that snapshot sampling fails to capture structural aquifer failure. In <b>Khokha village (Purnia, Bihar)</b>, 166 recurring Iron exceedances were recorded over multi-year cycles. While Iron is normally low-weighted (aesthetic nuisance), 166 repeated breaches confirm irreversible shallow aquifer lateritization. Local officials repeatedly drilled shallow handpumps that failed; the system output mandates deep confined aquifer tapping (>180m) or piped surface water.", body))
    
    story.append(PageBreak()) # Clean 2-page division

    # Intervention Matrix
    story.append(Paragraph("4. Jal Jeevan Mission (JJM) Policy & Engineering Intervention Matrix", h2_style))
    story.append(Paragraph("WaterTriage bridges data science and civil engineering by translating risk scores directly into actionable infrastructure recommendations categorized by CapEx, OpEx, and institutional dispatch protocols:", body))

    t2_data = [
        [Paragraph("Contaminant Profile", tbl_head), Paragraph("Target Region", tbl_head), Paragraph("Engineering Remedy", tbl_head), Paragraph("CapEx vs OpEx", tbl_head), Paragraph("Institutional Action", tbl_head)],
        [Paragraph("Acute Pathogen<br/>(E. coli > 0)", tbl_cell_bold), Paragraph("Shallow handpumps (Lucknow, Hardoi)", tbl_cell), Paragraph("Inline electro-chlorination & sanitary wellhead grouting", tbl_cell), Paragraph("Low CapEx (₹15k/pump)<br/>Low OpEx", tbl_cell), Paragraph("Immediate PHED disinfection squad; village boiling advisory", tbl_cell)],
        [Paragraph("Geogenic Fluoride<br/>(F⁻ > 1.5 mg/L)", tbl_cell_bold), Paragraph("Central UP (Unnao, Firozabad)", tbl_cell), Paragraph("Activated Alumina Units / CSIR-NEERI Nalgonda plants", tbl_cell), Paragraph("Med CapEx (₹2.5–5L)<br/>Med OpEx (alum refill)", tbl_cell), Paragraph("Deploy community defluoridation; VWSC water testing kits", tbl_cell)],
        [Paragraph("Dissolved Iron<br/>(Fe > 1.0 mg/L)", tbl_cell_bold), Paragraph("North Bihar (Purnia, Katihar)", tbl_cell), Paragraph("Aeration-Sedimentation-Filtration (IRP) gravity sand units", tbl_cell), Paragraph("Low-Med CapEx (₹1–2L)<br/>Very Low OpEx", tbl_cell), Paragraph("Attach top-head sand filters to existing handpumps", tbl_cell)],
        [Paragraph("Geogenic Arsenic<br/>(As ≥ 0.05 mg/L)", tbl_cell_bold), Paragraph("Ganga floodplains (Buxar, Bhagalpur)", tbl_cell), Paragraph("Adsorptive Media Filters (CSIR-AMPRI) & Deep Aquifer Bores", tbl_cell), Paragraph("High CapEx (₹8–15L)<br/>High OpEx (toxic media)", tbl_cell), Paragraph("Immediate shallow well seal; shift to Multi-Village Piped Scheme", tbl_cell)],
        [Paragraph("Nitrate Excess<br/>(NO₃⁻ > 45 mg/L)", tbl_cell_bold), Paragraph("Agrarian Western & Central UP", tbl_cell), Paragraph("Watershed agricultural buffer zones & RO drinking kiosks", tbl_cell), Paragraph("High CapEx (₹5–8L)<br/>High OpEx (reject brine)", tbl_cell), Paragraph("Fertilizer capping policy; centralized community RO kiosk", tbl_cell)]
    ]
    t2 = Table(t2_data, colWidths=[90, 85, 125, 95, 128])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f766e')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6))

    # Alignment
    story.append(Paragraph("5. Literature Alignment & Limitations (Reflecting on WPR-4)", h2_style))
    story.append(Paragraph("• <b>BIS IS 10500:2012 Compliance:</b> Scoring functions strictly mirror Indian statutory limits distinguishing acceptable vs permissible bounds.<br/>"
                           "• <b>Hydrogeological Grounding:</b> Co-occurrence of Arsenic and Iron in Holocene sediments aligns with Chakraborti et al. (2018) and CGWB Gangetic Basin surveys.<br/>"
                           "• <b>Acknowledged Scope Limitations:</b> The 1,359 samples represent prioritized geographic clusters rather than uniform coverage. Furthermore, while the live dashboard (port 3000) visualizes 121 districts, automated scraping remains rate-limited to avoid burdening government servers.", body))
    story.append(Spacer(1, 4))

    # Future Work
    story.append(Paragraph("FUTURE WORK PLANS", h1_style))
    story.append(Paragraph("• <b>WPR-8 Deliverable (Conclusion & Limitations):</b> Finalize system limitations, technical trade-offs, and multi-year maintenance framework for the final project report.", bullet))
    story.append(Paragraph("• <b>Automated Work-Order Generator:</b> Build one-click PDF work-order rosters for Gram Panchayat and block junior engineers directly from priority queue queries.", bullet))
    story.append(Paragraph("• <b>Predictive Spatial Kriging:</b> Prototype spatial interpolation to estimate contamination probabilities for unmonitored habitations between surveyed clusters.", bullet))
    story.append(Spacer(1, 14))

    # Signature Block
    sig_data = [
        [Paragraph("<b>Anubhav Anand</b><br/>Student Signature", meta_val), Paragraph("<b>Dr. Girish Paliwal</b><br/>Faculty Guide Signature", ParagraphStyle('RightSig', parent=meta_val, alignment=2))]
    ]
    t_sig = Table(sig_data, colWidths=[260, 263])
    t_sig.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (0,0), 0.5, colors.HexColor('#94a3b8')),
        ('LINEABOVE', (1,0), (1,0), 0.5, colors.HexColor('#94a3b8')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(KeepTogether([t_sig]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF build complete:", pdf_path)

if __name__ == '__main__':
    build_pdf()
