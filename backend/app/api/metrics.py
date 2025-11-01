from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch
from app.models.api_call_log import ApiCallLog

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = logging.getLogger(__name__)


def _parse_processing_time(value: str | None) -> float | None:
    if not value:
        return None

    digits = "".join(ch for ch in value if ch.isdigit() or ch == ".")
    try:
        return float(digits)
    except (ValueError, TypeError):
        return None


@router.get("/api-usage")
async def api_usage_metrics(db: AsyncSession = Depends(get_db)) -> Dict[str, object]:
    """Aggregate live API usage metrics from persisted call logs."""
    try:
        now = datetime.now(timezone.utc)

        total_calls: int = await db.scalar(select(func.count(ApiCallLog.id))) or 0
        success_calls: int = await db.scalar(
            select(func.count()).where(ApiCallLog.success.is_(True))
        ) or 0
        average_latency: Optional[float] = await db.scalar(select(func.avg(ApiCallLog.latency_ms)))

        percentile_rows = await db.execute(
            select(ApiCallLog.latency_ms).where(ApiCallLog.latency_ms.isnot(None))
        )
        latency_values = [row[0] for row in percentile_rows if row[0] is not None]

        def percentile(values: List[float], pct: float) -> Optional[float]:
            if not values:
                return None
            sorted_vals = sorted(values)
            k = (len(sorted_vals) - 1) * pct
            f = int(k)
            c = min(f + 1, len(sorted_vals) - 1)
            if f == c:
                return sorted_vals[int(k)]
            d0 = sorted_vals[f] * (c - k)
            d1 = sorted_vals[c] * (k - f)
            return d0 + d1

        p95_latency = percentile(latency_values, 0.95)
        p99_latency = percentile(latency_values, 0.99)

        by_service_rows = await db.execute(
            select(ApiCallLog.api_type, func.count(ApiCallLog.id)).group_by(ApiCallLog.api_type)
        )
        by_service = {service: count for service, count in by_service_rows}
        for key in ("news", "search", "chat", "ari"):
            by_service.setdefault(key, 0)

        # Retrieve logs from the last 24 hours for timeline aggregation
        cutoff = now - timedelta(hours=24)
        recent_logs_result = await db.execute(
            select(ApiCallLog).where(ApiCallLog.created_at >= cutoff)
        )
        recent_logs: List[ApiCallLog] = recent_logs_result.scalars().all()

        usage_by_hour: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"news": 0, "search": 0, "chat": 0, "ari": 0}
        )

        for log in recent_logs:
            timestamp = log.created_at or now
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            bucket = timestamp.astimezone(timezone.utc).strftime("%H:00")
            if log.api_type not in usage_by_hour[bucket]:
                usage_by_hour[bucket][log.api_type] = 0
            usage_by_hour[bucket][log.api_type] += 1

        usage_timeline = [
            {"time": hour, **totals}
            for hour, totals in sorted(usage_by_hour.items())
        ]

        last_call_row = await db.execute(
            select(ApiCallLog).order_by(ApiCallLog.created_at.desc()).limit(1)
        )
        last_call: Optional[ApiCallLog] = last_call_row.scalars().first()

        # Impact card analytics
        impact_cards_result = await db.execute(select(ImpactCard))
        impact_cards: List[ImpactCard] = impact_cards_result.scalars().all()
        processing_times: List[float] = []
        total_sources = 0
        last_generated_at: Optional[datetime] = None

        for card in impact_cards:
            total_sources += card.total_sources or 0
            processing = _parse_processing_time(card.processing_time)
            if processing is not None:
                processing_times.append(processing)
            if card.created_at:
                created_at = (
                    card.created_at
                    if card.created_at.tzinfo
                    else card.created_at.replace(tzinfo=timezone.utc)
                )
                if last_generated_at is None or created_at > last_generated_at:
                    last_generated_at = created_at

        avg_processing = (
            sum(processing_times) / len(processing_times)
            if processing_times
            else None
        )

        company_research_count: int = await db.scalar(
            select(func.count(CompanyResearch.id))
        ) or 0

        success_rate = (success_calls / total_calls) if total_calls else None

        return {
            "impact_cards": len(impact_cards),
            "company_research": company_research_count,
            "total_calls": total_calls,
            "success_rate": success_rate,
            "average_latency_ms": average_latency,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency,
            "by_service": by_service,
            "usage_last_24h": usage_timeline,
            "last_call_at": last_call.created_at.isoformat() if last_call and last_call.created_at else None,
            "total_sources": total_sources,
            "average_processing_seconds": avg_processing,
            "last_generated_at": last_generated_at.isoformat() if last_generated_at else None,
        }
    except Exception as e:
        logger.error(f"Error retrieving API usage metrics: {e}", exc_info=True)
        # Return empty/default metrics instead of failing
        return {
            "impact_cards": 0,
            "company_research": 0,
            "total_calls": 0,
            "success_rate": None,
            "average_latency_ms": None,
            "p95_latency_ms": None,
            "p99_latency_ms": None,
            "by_service": {"news": 0, "search": 0, "chat": 0, "ari": 0},
            "usage_last_24h": [],
            "last_call_at": None,
            "total_sources": 0,
            "average_processing_seconds": None,
            "last_generated_at": None,
        }
