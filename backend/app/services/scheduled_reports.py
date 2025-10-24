"""Scheduled reports service using Celery or APScheduler"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from croniter import croniter

from app.models.dashboard import ScheduledReport
from app.models.workspace import Workspace
from app.services.pdf_service import pdf_generator
from app.services.email_service import get_email_service
from app.services.slack_service import get_slack_service
from app.config import settings

logger = logging.getLogger(__name__)


class ScheduledReportsService:
    """Service for managing scheduled reports"""

    @staticmethod
    async def get_due_reports(db: AsyncSession) -> List[ScheduledReport]:
        """Get all reports that are due to run"""
        now = datetime.utcnow()

        result = await db.execute(
            select(ScheduledReport).where(
                ScheduledReport.is_active == True,
                ScheduledReport.next_run_at <= now
            )
        )

        return result.scalars().all()

    @staticmethod
    def calculate_next_run(cron_expression: str, timezone: str = "UTC") -> datetime:
        """Calculate next run time from cron expression"""
        try:
            iter = croniter(cron_expression, datetime.utcnow())
            return iter.get_next(datetime)
        except Exception as e:
            logger.error(f"❌ Failed to calculate next run: {str(e)}")
            # Default to 1 day from now
            from datetime import timedelta
            return datetime.utcnow() + timedelta(days=1)

    @staticmethod
    async def execute_report(
        report: ScheduledReport,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Execute a scheduled report"""
        try:
            logger.info(f"📊 Executing scheduled report: {report.name}")

            # Get workspace
            workspace_result = await db.execute(
                select(Workspace).where(Workspace.id == report.workspace_id)
            )
            workspace = workspace_result.scalar_one_or_none()

            if not workspace:
                raise ValueError("Workspace not found")

            # Generate report based on type
            report_data = await ScheduledReportsService._generate_report_data(
                report, workspace, db
            )

            # Generate PDF if needed
            pdf_buffer = None
            if report.format == "pdf":
                pdf_buffer = await ScheduledReportsService._generate_pdf(
                    report, report_data
                )

            # Send via email
            if report.recipient_emails:
                await ScheduledReportsService._send_email_report(
                    report, report_data, pdf_buffer
                )

            # Send via Slack
            if report.recipient_slack_channels:
                await ScheduledReportsService._send_slack_report(
                    report, report_data
                )

            # Update report execution stats
            report.last_run_at = datetime.utcnow()
            report.next_run_at = ScheduledReportsService.calculate_next_run(
                report.schedule_cron, report.timezone
            )
            report.total_runs += 1
            report.successful_runs += 1

            await db.commit()

            logger.info(f"✅ Scheduled report executed: {report.name}")

            return {
                "success": True,
                "report_id": report.id,
                "report_name": report.name,
                "next_run_at": report.next_run_at
            }

        except Exception as e:
            logger.error(f"❌ Failed to execute report {report.name}: {str(e)}")

            # Update failure stats
            report.total_runs += 1
            report.failed_runs += 1
            report.last_run_at = datetime.utcnow()
            await db.commit()

            return {
                "success": False,
                "report_id": report.id,
                "error": str(e)
            }

    @staticmethod
    async def _generate_report_data(
        report: ScheduledReport,
        workspace: Workspace,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate report data based on report type"""

        if report.report_type == "daily_summary":
            # Get all impact cards from last 24 hours
            from app.models.impact_card import ImpactCard
            from datetime import timedelta

            yesterday = datetime.utcnow() - timedelta(days=1)
            result = await db.execute(
                select(ImpactCard).where(
                    ImpactCard.created_at >= yesterday
                ).order_by(ImpactCard.risk_score.desc())
            )
            impact_cards = result.scalars().all()

            return {
                "type": "daily_summary",
                "workspace": workspace.name,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "impact_cards_count": len(impact_cards),
                "high_risk_count": sum(1 for card in impact_cards if card.risk_score >= 70),
                "impact_cards": [
                    {
                        "competitor": card.competitor_name,
                        "risk_score": card.risk_score,
                        "risk_level": card.risk_level
                    }
                    for card in impact_cards[:10]  # Top 10
                ]
            }

        elif report.report_type == "weekly_digest":
            # Get summary for the week
            from datetime import timedelta

            week_ago = datetime.utcnow() - timedelta(days=7)
            # Implement weekly aggregation logic here

            return {
                "type": "weekly_digest",
                "workspace": workspace.name,
                "week_start": week_ago.strftime("%Y-%m-%d"),
                "week_end": datetime.utcnow().strftime("%Y-%m-%d"),
                "summary": "Weekly competitive intelligence summary"
            }

        else:
            return {
                "type": report.report_type,
                "workspace": workspace.name,
                "generated_at": datetime.utcnow().isoformat()
            }

    @staticmethod
    async def _generate_pdf(
        report: ScheduledReport,
        report_data: Dict[str, Any]
    ):
        """Generate PDF from report data"""
        # Use existing PDF service to generate report
        # This is a simplified version - expand based on report type
        return None  # Placeholder

    @staticmethod
    async def _send_email_report(
        report: ScheduledReport,
        report_data: Dict[str, Any],
        pdf_buffer = None
    ):
        """Send report via email"""
        email_service = get_email_service(settings)

        if not email_service:
            logger.warning("⚠️ Email service not configured")
            return

        subject = f"Scheduled Report: {report.name}"
        message = f"""
Scheduled Report: {report.name}

Type: {report.report_type}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

{report_data.get('summary', 'See attached report for details.')}

---
Enterprise CIA - Powered by You.com APIs
        """

        # Send email (simplified - would need to attach PDF)
        # await email_service.send_email(...)
        logger.info(f"📧 Email report prepared for {len(report.recipient_emails)} recipients")

    @staticmethod
    async def _send_slack_report(
        report: ScheduledReport,
        report_data: Dict[str, Any]
    ):
        """Send report notification to Slack"""
        # Get Slack service for workspace
        slack_service = get_slack_service()  # Would get from integration config

        summary = f"Report Type: {report.report_type}\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"

        await slack_service.send_scheduled_report(
            report_name=report.name,
            summary=summary
        )

        logger.info(f"📱 Slack notification sent for report: {report.name}")


# Background task runner (would be called by Celery or scheduler)
async def run_scheduled_reports(db: AsyncSession):
    """Background task to run all due scheduled reports"""
    try:
        service = ScheduledReportsService()
        due_reports = await service.get_due_reports(db)

        logger.info(f"📊 Found {len(due_reports)} due reports")

        results = []
        for report in due_reports:
            result = await service.execute_report(report, db)
            results.append(result)

        return {
            "total_reports": len(due_reports),
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Scheduled reports runner error: {str(e)}")
        return {
            "error": str(e)
        }
