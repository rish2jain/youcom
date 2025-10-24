"""PDF Generation Service for Company Research Reports"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate professional PDF reports for company research"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        ))

        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))

        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

    def generate_research_report(self, research_data: Dict[str, Any]) -> BytesIO:
        """
        Generate PDF report for company research

        Args:
            research_data: Dictionary containing:
                - company_name: str
                - search_results: Dict (company profile, context)
                - research_report: Dict (comprehensive analysis)
                - total_sources: int
                - api_usage: Dict
                - created_at: datetime

        Returns:
            BytesIO: PDF file buffer
        """
        try:
            logger.info(f"📄 Generating PDF report for {research_data.get('company_name')}")

            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Container for the 'Flowable' objects
            elements = []

            # Add title
            company_name = research_data.get('company_name', 'Unknown Company')
            title = Paragraph(
                f"Company Research Report: {company_name}",
                self.styles['CustomTitle']
            )
            elements.append(title)
            elements.append(Spacer(1, 0.2 * inch))

            # Add metadata
            created_at = research_data.get('created_at', datetime.utcnow())
            if isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M UTC")

            metadata = f"<b>Generated:</b> {created_at_str}<br/>"
            metadata += f"<b>Total Sources:</b> {research_data.get('total_sources', 0)}<br/>"

            elements.append(Paragraph(metadata, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.3 * inch))

            # Add search results section
            search_results = research_data.get('search_results', {})
            if search_results:
                elements.append(Paragraph("Company Overview", self.styles['CustomHeading']))

                company_profile = search_results.get('company_profile', {})
                if company_profile:
                    profile_text = self._format_company_profile(company_profile)
                    elements.append(Paragraph(profile_text, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.2 * inch))

                # Add context snippets
                context = search_results.get('context', [])
                if context:
                    elements.append(Paragraph("Key Information", self.styles['CustomHeading']))
                    for idx, snippet in enumerate(context[:5], 1):
                        snippet_text = f"<b>{idx}.</b> {snippet.get('snippet', '')}"
                        elements.append(Paragraph(snippet_text, self.styles['CustomBody']))

                        # Add source
                        source_url = snippet.get('url', '')
                        if source_url:
                            source_text = f"<i>Source: {source_url}</i>"
                            elements.append(Paragraph(source_text, self.styles['Footer']))

                        elements.append(Spacer(1, 0.1 * inch))

            # Add research report section
            research_report = research_data.get('research_report', {})
            if research_report:
                elements.append(PageBreak())
                elements.append(Paragraph("Comprehensive Research Analysis", self.styles['CustomHeading']))

                # Add executive summary
                exec_summary = research_report.get('executive_summary', '')
                if exec_summary:
                    elements.append(Paragraph("<b>Executive Summary</b>", self.styles['CustomBody']))
                    elements.append(Paragraph(exec_summary, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.2 * inch))

                # Add detailed analysis
                detailed_analysis = research_report.get('detailed_analysis', '')
                if detailed_analysis:
                    elements.append(Paragraph("<b>Detailed Analysis</b>", self.styles['CustomBody']))
                    elements.append(Paragraph(detailed_analysis, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.2 * inch))

                # Add key findings
                key_findings = research_report.get('key_findings', [])
                if key_findings:
                    elements.append(Paragraph("<b>Key Findings</b>", self.styles['CustomBody']))
                    for finding in key_findings:
                        finding_text = f"• {finding}"
                        elements.append(Paragraph(finding_text, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.2 * inch))

            # Add API usage section
            api_usage = research_data.get('api_usage', {})
            if api_usage:
                elements.append(PageBreak())
                elements.append(Paragraph("Research Methodology", self.styles['CustomHeading']))

                usage_data = [
                    ['API', 'Calls Made', 'Sources'],
                    ['Search API', str(api_usage.get('search_calls', 0)), str(api_usage.get('search_sources', 0))],
                    ['ARI API', str(api_usage.get('ari_calls', 0)), str(api_usage.get('ari_sources', 0))],
                ]

                usage_table = Table(usage_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                usage_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                elements.append(usage_table)

            # Add footer
            elements.append(Spacer(1, 0.5 * inch))
            footer_text = "Generated by Enterprise CIA - Powered by You.com APIs"
            elements.append(Paragraph(footer_text, self.styles['Footer']))

            # Build PDF
            doc.build(elements)

            # Get PDF data
            buffer.seek(0)
            logger.info(f"✅ PDF report generated successfully for {company_name}")
            return buffer

        except Exception as e:
            logger.error(f"❌ Failed to generate PDF report: {str(e)}")
            raise

    def _format_company_profile(self, profile: Dict[str, Any]) -> str:
        """Format company profile data for PDF"""
        parts = []

        if profile.get('name'):
            parts.append(f"<b>Company:</b> {profile['name']}")

        if profile.get('description'):
            parts.append(f"<b>Description:</b> {profile['description']}")

        if profile.get('industry'):
            parts.append(f"<b>Industry:</b> {profile['industry']}")

        if profile.get('website'):
            parts.append(f"<b>Website:</b> {profile['website']}")

        if profile.get('headquarters'):
            parts.append(f"<b>Headquarters:</b> {profile['headquarters']}")

        return '<br/>'.join(parts) if parts else 'No company profile available'

    def generate_impact_card_report(self, impact_card_data: Dict[str, Any]) -> BytesIO:
        """
        Generate PDF report for impact card

        Args:
            impact_card_data: Dictionary containing impact card information

        Returns:
            BytesIO: PDF file buffer
        """
        try:
            logger.info(f"📄 Generating PDF for impact card")

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            elements = []

            # Add title
            title = Paragraph(
                f"Competitive Impact Analysis: {impact_card_data.get('competitor_name', 'Unknown')}",
                self.styles['CustomTitle']
            )
            elements.append(title)
            elements.append(Spacer(1, 0.2 * inch))

            # Add metadata
            created_at = impact_card_data.get('created_at', datetime.utcnow())
            if isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M UTC")

            metadata = f"<b>Generated:</b> {created_at_str}<br/>"
            metadata += f"<b>Risk Score:</b> {impact_card_data.get('risk_score', 0)}/100<br/>"
            metadata += f"<b>Total Sources:</b> {impact_card_data.get('total_sources', 0)}<br/>"

            elements.append(Paragraph(metadata, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.3 * inch))

            # Add impact summary
            impact_summary = impact_card_data.get('impact_summary', {})
            if impact_summary:
                elements.append(Paragraph("Impact Summary", self.styles['CustomHeading']))
                summary_text = impact_summary.get('summary', '')
                elements.append(Paragraph(summary_text, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.2 * inch))

            # Build PDF
            doc.build(elements)
            buffer.seek(0)

            logger.info("✅ Impact card PDF generated successfully")
            return buffer

        except Exception as e:
            logger.error(f"❌ Failed to generate impact card PDF: {str(e)}")
            raise


# Singleton instance
pdf_generator = PDFReportGenerator()
