"""Email Service for sharing reports"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with reports"""

    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, from_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email

    async def send_research_report(
        self,
        to_emails: List[str],
        company_name: str,
        pdf_buffer: BytesIO,
        subject: Optional[str] = None,
        message: Optional[str] = None
    ) -> bool:
        """
        Send company research report via email

        Args:
            to_emails: List of recipient email addresses
            company_name: Name of the company in the report
            pdf_buffer: PDF file buffer
            subject: Email subject (optional)
            message: Email body message (optional)

        Returns:
            bool: True if email sent successfully
        """
        try:
            logger.info(f"📧 Sending research report for {company_name} to {', '.join(to_emails)}")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject or f"Company Research Report: {company_name}"

            # Email body
            body = message or f"""
Dear Recipient,

Please find attached the comprehensive research report for {company_name}.

This report was generated using Enterprise CIA, powered by You.com APIs.

Key features of this report:
- Comprehensive company overview
- Market analysis and competitive insights
- Data sourced from multiple reliable sources

If you have any questions about this report, please don't hesitate to reach out.

Best regards,
Enterprise CIA Team
            """

            msg.attach(MIMEText(body, 'plain'))

            # Attach PDF
            pdf_buffer.seek(0)
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(pdf_buffer.read())
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{company_name.replace(" ", "_")}_research_report.pdf"'
            )
            msg.attach(pdf_attachment)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False

    async def send_impact_card(
        self,
        to_emails: List[str],
        competitor_name: str,
        pdf_buffer: BytesIO,
        risk_score: int,
        subject: Optional[str] = None,
        message: Optional[str] = None
    ) -> bool:
        """
        Send competitive impact card via email

        Args:
            to_emails: List of recipient email addresses
            competitor_name: Name of the competitor
            pdf_buffer: PDF file buffer
            risk_score: Risk score from impact analysis
            subject: Email subject (optional)
            message: Email body message (optional)

        Returns:
            bool: True if email sent successfully
        """
        try:
            logger.info(f"📧 Sending impact card for {competitor_name} to {', '.join(to_emails)}")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject or f"Competitive Impact Alert: {competitor_name} (Risk: {risk_score}/100)"

            # Email body
            body = message or f"""
Dear Recipient,

A new competitive impact analysis has been generated for {competitor_name}.

Risk Score: {risk_score}/100

Please find the detailed analysis attached as a PDF report.

This analysis includes:
- Latest news and developments
- Competitive impact assessment
- Strategic recommendations

Stay ahead of the competition with Enterprise CIA.

Best regards,
Enterprise CIA Team
            """

            msg.attach(MIMEText(body, 'plain'))

            # Attach PDF
            pdf_buffer.seek(0)
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(pdf_buffer.read())
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{competitor_name.replace(" ", "_")}_impact_card.pdf"'
            )
            msg.attach(pdf_attachment)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return False

    async def send_alert_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        context: dict
    ) -> bool:
        """
        Send automated alert email

        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Alert message content
            context: Alert context data

        Returns:
            bool: True if email sent successfully
        """
        try:
            logger.info(f"🚨 Sending alert email to {to_email}")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Format email body
            body = f"""
{message}

---
Alert Details:
- Triggered: {context.get('triggered_at', 'Now')}
- Competitor: {context.get('competitor', 'Unknown')}
- Alert Type: Automated Competitive Intelligence

This is an automated alert from Enterprise CIA.
To manage your alert preferences, visit the dashboard.

Best regards,
Enterprise CIA Alert System
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Alert email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send alert email: {str(e)}")
            return False

    async def send_digest_email(
        self,
        to_email: str,
        subject: str,
        content: str
    ) -> bool:
        """
        Send daily digest email

        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Digest content (markdown format)

        Returns:
            bool: True if email sent successfully
        """
        try:
            logger.info(f"📧 Sending digest email to {to_email}")

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Convert markdown-like content to plain text
            body = content.replace('# ', '').replace('## ', '').replace('### ', '').replace('*', '')
            
            # Add footer
            body += f"""

---
This digest was automatically generated by Enterprise CIA.
To unsubscribe or modify your digest preferences, visit the dashboard.

Enterprise CIA - Powered by You.com APIs
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Digest email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send digest email: {str(e)}")
            return False


# Factory function to create email service
def get_email_service(config) -> Optional[EmailService]:
    """Create email service instance from config"""
    try:
        if not all([config.smtp_host, config.smtp_port, config.smtp_user, config.smtp_password, config.from_email]):
            logger.warning("⚠️ Email service not configured - some settings are missing")
            return None

        return EmailService(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_user=config.smtp_user,
            smtp_password=config.smtp_password,
            from_email=config.from_email
        )
    except Exception as e:
        logger.error(f"❌ Failed to create email service: {str(e)}")
        return None
