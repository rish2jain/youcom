"""
Benchmarking Dashboard API endpoints for Advanced Intelligence Suite
Provides access to performance metrics, benchmarks, and trend analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.benchmarking import (
    BenchmarkMetric, IndustryBenchmark, TrendAnalysis, 
    AnomalyDetection, BenchmarkComparison
)
from app.services.metrics_aggregator import metrics_aggregator, run_metrics_collection
from app.services.benchmark_calculator import benchmark_calculator, calculate_workspace_benchmarks
from app.services.trend_analyzer import (
    trend_analyzer, anomaly_detector, analyze_all_metrics_trends, 
    detect_all_metrics_anomalies
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benchmarking", tags=["benchmarking"])


# Pydantic models for API responses


class MetricSummary(BaseModel):
    metric_name: str
    current_value: float
    benchmark_value: float
    percentile_rank: float
    performance_rating: str
    trend_direction: str
    change_percentage: float


class BenchmarkDashboardResponse(BaseModel):
    workspace_id: str
    industry_sector: Optional[str]
    overall_score: float
    performance_rating: str
    metrics_summary: List[MetricSummary]
    key_insights: List[str]
    recommendations: List[str]
    last_updated: datetime


class TrendAnalysisResponse(BaseModel):
    metric_name: str
    trend_direction: str
    trend_strength: float
    trend_confidence: float
    volatility: float
    key_insights: List[str]
    recommendations: List[str]
    data_points_count: int
    analysis_period_days: int


class AnomalyResponse(BaseModel):
    metric_name: str
    anomaly_type: str
    severity: str
    anomaly_score: float
    actual_value: float
    expected_value: float
    deviation_percentage: float
    detected_at: datetime
    recommendations: List[str]


class MetricsCollectionResponse(BaseModel):
    metrics_collected: int
    time_period: str
    collection_timestamp: datetime
    metrics_by_category: Dict[str, int]


@router.get("/dashboard/{workspace_id}", response_model=BenchmarkDashboardResponse)
async def get_benchmarking_dashboard(
    workspace_id: str,
    industry_sector: Optional[str] = None,
    days_back: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive benchmarking dashboard for a workspace"""
    try:
        # Calculate benchmarks for the workspace
        benchmark_results = await calculate_workspace_benchmarks(
            workspace_id=workspace_id,
            industry_sector=industry_sector,
            days_back=days_back
        )
        
        if not benchmark_results:
            raise HTTPException(
                status_code=404,
                detail="No benchmark data available for this workspace"
            )
        
        # Calculate overall performance score
        percentile_ranks = [result.percentile_rank for result in benchmark_results.values()]
        overall_score = sum(percentile_ranks) / len(percentile_ranks) if percentile_ranks else 0
        
        # Determine overall performance rating
        if overall_score >= 90:
            performance_rating = "excellent"
        elif overall_score >= 75:
            performance_rating = "good"
        elif overall_score >= 50:
            performance_rating = "average"
        elif overall_score >= 25:
            performance_rating = "below_average"
        else:
            performance_rating = "poor"
        
        # Get trend data for change percentages
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        trends = await analyze_all_metrics_trends(
            entity_id=workspace_id,
            entity_type="workspace",
            days_back=days_back
        )
        
        # Build metrics summary
        metrics_summary = []
        all_insights = []
        all_recommendations = []
        
        for metric_name, benchmark_result in benchmark_results.items():
            # Get trend information
            trend = trends.get(metric_name)
            change_percentage = 0.0
            trend_direction = "stable"
            
            if trend:
                trend_direction = trend.trend_direction
                # Calculate approximate change percentage from slope
                if trend.slope != 0:
                    change_percentage = trend.slope * days_back
            
            metrics_summary.append(MetricSummary(
                metric_name=metric_name,
                current_value=benchmark_result.entity_value,
                benchmark_value=benchmark_result.benchmark_value,
                percentile_rank=benchmark_result.percentile_rank,
                performance_rating=benchmark_result.performance_rating,
                trend_direction=trend_direction,
                change_percentage=change_percentage
            ))
            
            # Collect insights and recommendations
            all_insights.extend(benchmark_result.key_insights)
            all_recommendations.extend(benchmark_result.improvement_recommendations)
        
        # Deduplicate and limit insights/recommendations
        unique_insights = list(dict.fromkeys(all_insights))[:5]
        unique_recommendations = list(dict.fromkeys(all_recommendations))[:5]
        
        return BenchmarkDashboardResponse(
            workspace_id=workspace_id,
            industry_sector=industry_sector,
            overall_score=overall_score,
            performance_rating=performance_rating,
            metrics_summary=metrics_summary,
            key_insights=unique_insights,
            recommendations=unique_recommendations,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error generating benchmarking dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{workspace_id}")
async def get_workspace_metrics(
    workspace_id: str,
    metric_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    aggregation: str = Query("hourly", regex="^(raw|hourly|daily|weekly)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed metrics data for a workspace"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build query conditions
        conditions = [
            BenchmarkMetric.workspace_id == workspace_id,
            BenchmarkMetric.measurement_timestamp >= start_date,
            BenchmarkMetric.measurement_timestamp <= end_date
        ]
        
        if metric_name:
            conditions.append(BenchmarkMetric.metric_name == metric_name)
        
        if aggregation != "raw":
            conditions.append(BenchmarkMetric.time_period == aggregation)
        
        # Execute query
        result = await db.execute(
            select(BenchmarkMetric)
            .where(and_(*conditions))
            .order_by(BenchmarkMetric.measurement_timestamp.desc())
            .limit(1000)  # Limit to prevent large responses
        )
        
        metrics = result.scalars().all()
        
        # Format response
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "metric_name": metric.metric_name,
                "value": metric.metric_value,
                "unit": metric.unit,
                "timestamp": metric.measurement_timestamp,
                "category": metric.metric_category,
                "source_system": metric.source_system,
                "metadata": metric.metric_metadata
            })
        
        return {
            "workspace_id": workspace_id,
            "metrics": metrics_data,
            "total_count": len(metrics_data),
            "period": {
                "start": start_date,
                "end": end_date
            },
            "aggregation": aggregation
        }
        
    except Exception as e:
        logger.error(f"Error retrieving workspace metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{workspace_id}")
async def get_trend_analysis(
    workspace_id: str,
    metric_name: Optional[str] = None,
    days_back: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get trend analysis for workspace metrics"""
    try:
        if metric_name:
            # Analyze specific metric
            trend_result = await trend_analyzer.analyze_metric_trend(
                metric_name=metric_name,
                entity_id=workspace_id,
                entity_type="workspace",
                start_date=datetime.utcnow() - timedelta(days=days_back),
                end_date=datetime.utcnow()
            )
            
            return TrendAnalysisResponse(
                metric_name=trend_result.metric_name,
                trend_direction=trend_result.trend_direction,
                trend_strength=trend_result.trend_strength,
                trend_confidence=trend_result.trend_confidence,
                volatility=trend_result.volatility,
                key_insights=trend_result.key_insights,
                recommendations=trend_result.recommendations,
                data_points_count=trend_result.data_points_count,
                analysis_period_days=days_back
            )
        else:
            # Analyze all metrics
            trends = await analyze_all_metrics_trends(
                entity_id=workspace_id,
                entity_type="workspace",
                days_back=days_back
            )
            
            trend_responses = []
            for metric_name, trend_result in trends.items():
                trend_responses.append(TrendAnalysisResponse(
                    metric_name=trend_result.metric_name,
                    trend_direction=trend_result.trend_direction,
                    trend_strength=trend_result.trend_strength,
                    trend_confidence=trend_result.trend_confidence,
                    volatility=trend_result.volatility,
                    key_insights=trend_result.key_insights,
                    recommendations=trend_result.recommendations,
                    data_points_count=trend_result.data_points_count,
                    analysis_period_days=days_back
                ))
            
            return {
                "workspace_id": workspace_id,
                "trends": trend_responses,
                "analysis_period_days": days_back,
                "analyzed_at": datetime.utcnow()
            }
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/{workspace_id}")
async def get_anomaly_detection(
    workspace_id: str,
    metric_name: Optional[str] = None,
    days_back: int = Query(7, ge=1, le=30),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    detection_method: str = Query("statistical", regex="^(statistical|ml_based|threshold)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get anomaly detection results for workspace metrics"""
    try:
        if metric_name:
            # Detect anomalies for specific metric
            anomalies = await anomaly_detector.detect_anomalies(
                metric_name=metric_name,
                entity_id=workspace_id,
                entity_type="workspace",
                start_date=datetime.utcnow() - timedelta(days=days_back),
                end_date=datetime.utcnow(),
                detection_method=detection_method
            )
            
            # Filter by severity if specified
            if severity:
                anomalies = [a for a in anomalies if a.severity == severity]
            
            anomaly_responses = []
            for anomaly in anomalies:
                anomaly_responses.append(AnomalyResponse(
                    metric_name=anomaly.metric_name,
                    anomaly_type=anomaly.anomaly_type,
                    severity=anomaly.severity,
                    anomaly_score=anomaly.anomaly_score,
                    actual_value=anomaly.actual_value,
                    expected_value=anomaly.expected_value,
                    deviation_percentage=anomaly.deviation_percentage,
                    detected_at=anomaly.detected_at,
                    recommendations=anomaly.recommendations
                ))
            
            return {
                "workspace_id": workspace_id,
                "metric_name": metric_name,
                "anomalies": anomaly_responses,
                "detection_method": detection_method,
                "analysis_period_days": days_back
            }
        else:
            # Detect anomalies for all metrics
            all_anomalies = await detect_all_metrics_anomalies(
                entity_id=workspace_id,
                entity_type="workspace",
                days_back=days_back,
                detection_method=detection_method
            )
            
            # Flatten and filter anomalies
            flat_anomalies = []
            for metric_anomalies in all_anomalies.values():
                for anomaly in metric_anomalies:
                    if not severity or anomaly.severity == severity:
                        flat_anomalies.append(AnomalyResponse(
                            metric_name=anomaly.metric_name,
                            anomaly_type=anomaly.anomaly_type,
                            severity=anomaly.severity,
                            anomaly_score=anomaly.anomaly_score,
                            actual_value=anomaly.actual_value,
                            expected_value=anomaly.expected_value,
                            deviation_percentage=anomaly.deviation_percentage,
                            detected_at=anomaly.detected_at,
                            recommendations=anomaly.recommendations
                        ))
            
            # Sort by severity and anomaly score
            severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            flat_anomalies.sort(
                key=lambda x: (severity_order.get(x.severity, 0), x.anomaly_score),
                reverse=True
            )
            
            return {
                "workspace_id": workspace_id,
                "anomalies": flat_anomalies,
                "detection_method": detection_method,
                "analysis_period_days": days_back,
                "total_anomalies": len(flat_anomalies),
                "severity_breakdown": {
                    severity: len([a for a in flat_anomalies if a.severity == severity])
                    for severity in ["critical", "high", "medium", "low"]
                }
            }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry-benchmarks")
async def get_industry_benchmarks(
    industry_sector: str,
    metric_name: Optional[str] = None,
    benchmark_type: str = Query("percentile", regex="^(percentile|mean|median)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get industry benchmark data"""
    try:
        conditions = [
            IndustryBenchmark.industry_sector == industry_sector,
            IndustryBenchmark.benchmark_type == benchmark_type
        ]
        
        if metric_name:
            conditions.append(IndustryBenchmark.metric_name == metric_name)
        
        result = await db.execute(
            select(IndustryBenchmark)
            .where(and_(*conditions))
            .order_by(desc(IndustryBenchmark.created_at))
        )
        
        benchmarks = result.scalars().all()
        
        # Group by metric name
        benchmarks_by_metric = {}
        for benchmark in benchmarks:
            if benchmark.metric_name not in benchmarks_by_metric:
                benchmarks_by_metric[benchmark.metric_name] = []
            
            benchmarks_by_metric[benchmark.metric_name].append({
                "benchmark_value": benchmark.benchmark_value,
                "percentile_rank": benchmark.percentile_rank,
                "sample_size": benchmark.sample_size,
                "confidence_level": benchmark.confidence_level,
                "data_freshness_days": benchmark.data_freshness_days,
                "benchmark_period": {
                    "start": benchmark.benchmark_period_start,
                    "end": benchmark.benchmark_period_end
                },
                "data_sources": benchmark.data_sources,
                "calculation_method": benchmark.calculation_method
            })
        
        return {
            "industry_sector": industry_sector,
            "benchmark_type": benchmark_type,
            "benchmarks": benchmarks_by_metric,
            "total_metrics": len(benchmarks_by_metric)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving industry benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-metrics", response_model=MetricsCollectionResponse)
async def trigger_metrics_collection(
    workspace_id: Optional[str] = None,
    hours_back: int = Query(1, ge=1, le=24)
):
    """Manually trigger metrics collection"""
    try:
        # Run metrics collection
        aggregated_metrics = await run_metrics_collection(
            hours_back=hours_back,
            workspace_id=workspace_id
        )
        
        # Count metrics by category
        metrics_by_category = {}
        total_metrics = 0
        
        for metric_name, aggregated in aggregated_metrics.items():
            # Determine category from metric name
            if "api_" in metric_name:
                category = "api_performance"
            elif "ml_" in metric_name:
                category = "ml_performance"
            elif "intelligence_" in metric_name:
                category = "intelligence_quality"
            elif any(term in metric_name for term in ["coverage", "generation"]):
                category = "coverage"
            else:
                category = "other"
            
            metrics_by_category[category] = metrics_by_category.get(category, 0) + 1
            total_metrics += 1
        
        return MetricsCollectionResponse(
            metrics_collected=total_metrics,
            time_period=f"{hours_back} hours",
            collection_timestamp=datetime.utcnow(),
            metrics_by_category=metrics_by_category
        )
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison/{workspace_id}")
async def get_benchmark_comparisons(
    workspace_id: str,
    metric_name: Optional[str] = None,
    days_back: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get historical benchmark comparisons for a workspace"""
    try:
        conditions = [
            BenchmarkComparison.entity_id == workspace_id,
            BenchmarkComparison.entity_type == "workspace",
            BenchmarkComparison.comparison_period_end >= datetime.utcnow() - timedelta(days=days_back)
        ]
        
        if metric_name:
            conditions.append(BenchmarkComparison.metric_name == metric_name)
        
        result = await db.execute(
            select(BenchmarkComparison)
            .where(and_(*conditions))
            .order_by(desc(BenchmarkComparison.created_at))
        )
        
        comparisons = result.scalars().all()
        
        comparison_data = []
        for comp in comparisons:
            comparison_data.append({
                "metric_name": comp.metric_name,
                "entity_value": comp.entity_value,
                "benchmark_value": comp.benchmark_value,
                "percentile_rank": comp.percentile_rank,
                "performance_rating": comp.performance_rating,
                "improvement_potential": comp.improvement_potential,
                "competitive_position": comp.competitive_position,
                "industry_sector": comp.industry_sector,
                "comparison_period": {
                    "start": comp.comparison_period_start,
                    "end": comp.comparison_period_end
                },
                "key_insights": comp.key_insights,
                "improvement_recommendations": comp.improvement_recommendations,
                "benchmark_source": comp.benchmark_source,
                "confidence_level": comp.confidence_level,
                "created_at": comp.created_at
            })
        
        return {
            "workspace_id": workspace_id,
            "comparisons": comparison_data,
            "total_comparisons": len(comparison_data),
            "analysis_period_days": days_back
        }
        
    except Exception as e:
        logger.error(f"Error retrieving benchmark comparisons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def benchmarking_health_check(session: AsyncSession = Depends(get_db)):
    """Health check endpoint for benchmarking service"""
    try:
        # Test database connection
        result = await session.execute(select(func.count(BenchmarkMetric.id)))
        metric_count = result.scalar()
        
        return {
            "status": "healthy",
            "service": "benchmarking_dashboard",
            "timestamp": datetime.utcnow(),
            "metrics_count": metric_count,
            "features": [
                "metrics_collection",
                "benchmark_calculation",
                "trend_analysis",
                "anomaly_detection",
                "dashboard_api"
            ]
        }
        
    except Exception as e:
        logger.error(f"Benchmarking health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "benchmarking_dashboard",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@router.get("/integration/status")
async def get_benchmarking_integration_status(db: AsyncSession = Depends(get_db)):
    """Get benchmarking integration status with performance monitoring."""
    try:
        from app.services.benchmarking_integration import BenchmarkingIntegrationService
        
        integration_service = BenchmarkingIntegrationService(db)
        status = await integration_service.get_integration_status()
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting benchmarking integration status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration status: {str(e)}")

@router.post("/integration/sync")
async def sync_benchmarking_with_performance_monitor(db: AsyncSession = Depends(get_db)):
    """Manually sync benchmarking with performance monitoring."""
    try:
        from app.services.benchmarking_integration import BenchmarkingIntegrationService
        
        integration_service = BenchmarkingIntegrationService(db)
        result = await integration_service.integrate_with_performance_monitor()
        
        return {
            "message": "Benchmarking integration sync completed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error syncing benchmarking integration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync integration: {str(e)}")

@router.get("/integration/alerts")
async def get_benchmark_alerts(db: AsyncSession = Depends(get_db)):
    """Get benchmark-based alerts."""
    try:
        from app.services.benchmarking_integration import BenchmarkingIntegrationService
        
        integration_service = BenchmarkingIntegrationService(db)
        alert_status = await integration_service.connect_with_alert_system()
        
        return alert_status
        
    except Exception as e:
        logger.error(f"Error getting benchmark alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmark alerts: {str(e)}")