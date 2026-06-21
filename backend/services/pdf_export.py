import io
import logging
from datetime import datetime

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_INSTALLED = True
except (ImportError, OSError):
    WEASYPRINT_INSTALLED = False

# Import ReportLab flowables and styles for the pure-python PDF fallback
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger('ats_resume_scorer')


def draw_header_footer(canvas, doc):
    """Draws a professional header and footer line with page numbering on every page."""
    canvas.saveState()
    
    # Header line
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
    canvas.setLineWidth(0.5)
    canvas.line(36, 756, 576, 756)
    
    # Header text
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(colors.HexColor('#0F172A'))
    canvas.drawString(36, 762, "RESUME EVALUATION REPORT — DETAILED PERFORMANCE ANALYSIS")
    
    # Footer line
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
    canvas.setLineWidth(0.5)
    canvas.line(36, 45, 576, 45)
    
    # Footer text
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#64748B'))
    canvas.drawString(36, 32, "Confidential — Resume Performance Analysis Report")
    canvas.drawRightString(576, 32, f"Page {doc.page}")
    
    canvas.restoreState()


def _generate_reportlab_pdf(raw_data: dict) -> bytes:
    """Generates a highly detailed multi-page PDF report using ReportLab with all parsed metrics."""
    buffer = io.BytesIO()
    
    # Margins: 0.5 inch (36pt) left/right, 0.75 inch (54pt) top/bottom to prevent header/footer collision
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=54,
        bottomMargin=54
    )
    story = []
    
    # Extract key metrics
    ats_score = raw_data.get('ats_score', raw_data.get('ATS_score', 0))
    interpretation = raw_data.get('interpretation', '')
    
    # Base stylesheet
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    body_bold_style = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    # Color-code based on ATS Score ranges
    if ats_score >= 80:
        score_color = colors.HexColor('#16A34A')  # Green
        score_bg = colors.HexColor('#F0FDF4')
    elif ats_score >= 60:
        score_color = colors.HexColor('#D97706')  # Orange
        score_bg = colors.HexColor('#FFFBEB')
    else:
        score_color = colors.HexColor('#DC2626')  # Red
        score_bg = colors.HexColor('#FEF2F2')
        
    # --- PAGE 1: EXECUTIVE SUMMARY & SCORING METRICS ---
    story.append(Paragraph("Resume Analysis & Evaluation Report", title_style))
    formatted_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    story.append(Paragraph(f"Report Generated on {formatted_date}", subtitle_style))
    
    # Executive Summary Card
    score_p = Paragraph(f"<font size=28 color='{score_color.hexval()}'><b>{ats_score:.0f}/100</b></font><br/><b>ATS Compatibility Score</b>", body_style)
    interp_p = Paragraph(f"<b>Overall Evaluation:</b><br/>{interpretation}", body_style)
    
    summary_table = Table([[score_p, interp_p]], colWidths=[140, 400])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), score_bg),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))
    
    # Category score breakdown
    story.append(Paragraph("Score Breakdown by Category", h1_style))
    cs = raw_data.get('component_scores', {})
    if hasattr(cs, 'model_dump'):
        cs = cs.model_dump()
    elif not isinstance(cs, dict):
        cs = cs.__dict__ if hasattr(cs, '__dict__') else {}
        
    comp_headers = [
        Paragraph("<b>Evaluation Category</b>", body_style),
        Paragraph("<b>Your Score</b>", body_style),
        Paragraph("<b>Max Score</b>", body_style),
        Paragraph("<b>Percentage</b>", body_style)
    ]
    
    def get_row(name, val, max_val):
        pct = (val / max_val * 100) if max_val > 0 else 0
        return [
            Paragraph(name, body_style),
            Paragraph(f"{val:.1f}", body_style),
            Paragraph(str(max_val), body_style),
            Paragraph(f"{pct:.0f}%", body_style)
        ]
        
    comp_data = [
        comp_headers,
        get_row("Formatting & Layout Structure", cs.get('formatting', 0), 20),
        get_row("Keyword Matching & Relevance", cs.get('keywords', 0), 25),
        get_row("Content Quality & Impact", cs.get('content', 0), 25),
        get_row("Skill Validation Evidence", cs.get('skill_validation', 0), 15),
        get_row("ATS Technical Compatibility", cs.get('ats_compatibility', 0), 15),
    ]
    
    comp_table = Table(comp_data, colWidths=[240, 100, 100, 100])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor('#94A3B8')),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#94A3B8')),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 10))
    
    # Key Strengths
    story.append(Paragraph("Key Strengths", h1_style))
    strengths = raw_data.get('strengths', [])
    if strengths:
        for strg in strengths:
            story.append(Paragraph(f"• {strg}", bullet_style))
    else:
        story.append(Paragraph("No major strengths identified yet.", body_style))
        
    story.append(PageBreak())
    
    # --- PAGE 2: IMPROVEMENTS, SKILLS & JD COMPARISON ---
    story.append(Paragraph("Detailed Feedback & Optimization Recommendations", title_style))
    story.append(Spacer(1, 5))
    
    # Extract detailed feedback
    raw_feedback = raw_data.get('detailed_feedback', [])
    def to_dict(item):
        if isinstance(item, dict):
            return item
        return item.model_dump() if hasattr(item, 'model_dump') else item.__dict__
        
    detailed_feedback = [to_dict(fb) for fb in raw_feedback]
    
    high_priority = [fb for fb in detailed_feedback if fb.get('severity_level', '').lower() in ('high',)]
    mod_priority = [fb for fb in detailed_feedback if fb.get('severity_level', '').lower() in ('moderate', 'medium')]
    
    def append_issue_card(fb, border_color):
        issue = fb.get('issue_title', fb.get('issue_description', ''))
        explanation = fb.get('explanation', '')
        fix = fb.get('how_to_fix', fb.get('suggestions', ''))
        example = fb.get('example_improvement', '')
        action_items = fb.get('action_items', [])
        
        issue_story = []
        issue_story.append(Paragraph(f"<b>{issue}</b>", ParagraphStyle('IssueTitle', parent=body_bold_style, fontSize=10, textColor=colors.HexColor('#0F172A'))))
        
        if explanation:
            issue_story.append(Paragraph(f"<b>Explanation:</b> {explanation}", body_style))
        if fix:
            issue_story.append(Paragraph(f"<b>Recommendation:</b> {fix}", body_style))
        if example:
            example_clean = example.replace('\n', '<br/>')
            issue_story.append(Paragraph(f"<b>Improvement Example:</b><br/><font color='#475569'><i>{example_clean}</i></font>", body_style))
        if action_items:
            for item in action_items:
                issue_story.append(Paragraph(f"• {item}", bullet_style))
                
        issue_table = Table([[issue_story]], colWidths=[540])
        issue_table.setStyle(TableStyle([
            ('LINELEFT', (0,0), (0,0), 3, border_color),
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#F8FAFC')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(issue_table)
        story.append(Spacer(1, 10))

    if high_priority:
        story.append(Paragraph("High Priority Action Items", h1_style))
        story.append(Spacer(1, 4))
        for fb in high_priority[:5]:
            append_issue_card(fb, colors.HexColor('#DC2626'))
            
    if mod_priority:
        story.append(Paragraph("Moderate Action Items", h1_style))
        story.append(Spacer(1, 4))
        for fb in mod_priority[:5]:
            append_issue_card(fb, colors.HexColor('#D97706'))
            
    if not high_priority and not mod_priority:
        story.append(Paragraph("No critical or moderate issues were detected. The document structure is fully compliant.", body_style))
        
    # General Suggestions/Improvements
    suggestions = raw_data.get('suggestions', [])
    if suggestions:
        story.append(Paragraph("Strategic Optimization Strategies", h1_style))
        for sugg in suggestions:
            story.append(Paragraph(f"• {sugg}", bullet_style))
        story.append(Spacer(1, 10))
        
    # Skill Validation Results
    story.append(Paragraph("Skill Context & Evidence Verification", h1_style))
    svd = raw_data.get('skill_validation_details', {})
    if hasattr(svd, 'model_dump'):
        svd = svd.model_dump()
    elif not isinstance(svd, dict):
        svd = svd.__dict__ if hasattr(svd, '__dict__') else {}
        
    val_pct = svd.get('validation_pct', 0.0)
    story.append(Paragraph(f"<b>Skill Context Verification Rate: {val_pct:.1f}%</b> (Proportions of listed skills verified within project descriptions or employment context)", body_style))
    validated = svd.get('validated', [])
    unvalidated = svd.get('unvalidated', [])
    
    if validated:
        val_names = ", ".join(item.get('skill', '') for item in validated[:15])
        story.append(Paragraph(f"<b>Verified Skills:</b> {val_names}", body_style))
    if unvalidated:
        unval_names = ", ".join(unvalidated[:15])
        story.append(Paragraph(f"<b>Skills Lacking Context:</b> <font color='#B91C1C'>{unval_names}</font>", body_style))
        
    # Job Description Match
    jd_analysis = raw_data.get('jd_match_analysis', raw_data.get('jd_comparison'))
    if hasattr(jd_analysis, 'model_dump'):
        jd_analysis = jd_analysis.model_dump()
    elif not isinstance(jd_analysis, dict) and jd_analysis is not None:
        jd_analysis = jd_analysis.__dict__
        
    if jd_analysis:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Job Description Matching Metrics", h1_style))
        match_pct = jd_analysis.get('match_percentage', 0.0)
        similarity = jd_analysis.get('semantic_similarity', 0.0)
        story.append(Paragraph(f"<b>Role Match Percentage:</b> {match_pct:.1f}% (Semantic Vector Similarity: {similarity:.2f})", body_style))
        
        matched = jd_analysis.get('matched_keywords', [])
        missing = jd_analysis.get('missing_keywords', [])
        skills_gap = jd_analysis.get('skills_gap', [])
        
        if matched:
            story.append(Paragraph(f"<b>Matched Professional Keywords:</b> {', '.join(matched[:15])}", body_style))
        if missing:
            story.append(Paragraph(f"<b>Missing Target Keywords (Recommended to add):</b> {', '.join(missing[:15])}", body_style))
        if skills_gap:
            story.append(Paragraph(f"<b>Skills Gap Identification:</b> {', '.join(skills_gap[:10])}", body_style))
            
    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    return buffer.getvalue()


def generate_combined_pdf(html_docs: dict[str, str], raw_data: dict = None) -> bytes:
    """Generates combined PDF bytes using WeasyPrint (HTML to PDF) or ReportLab as a pure-Python fallback."""
    import sys
    if sys.platform != 'win32' and WEASYPRINT_INSTALLED:
        try:
            documents = []
            for name, html_str in html_docs.items():
                doc = HTML(string=html_str).render()
                documents.append(doc)
            
            first_doc = documents[0]
            for other_doc in documents[1:]:
                for page in other_doc.pages:
                    first_doc.pages.append(page)
                    
            return first_doc.write_pdf()
        except Exception as e:
            logger.warning(f"WeasyPrint PDF rendering failed, trying ReportLab fallback: {e}")
            
    # Fallback path if WeasyPrint is missing/failed
    if raw_data:
        try:
            return _generate_reportlab_pdf(raw_data)
        except Exception as e:
            logger.error(f"ReportLab PDF generation failed: {e}")
            raise RuntimeError(f"All PDF generation attempts failed. ReportLab error: {e}")
            
    raise ImportError(
        "WeasyPrint is not installed or missing system libraries, and no raw data was provided for fallback PDF generation."
    )
