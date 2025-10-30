"""
Benchmarking Models for Advanced Intelligence Suite

Models for storing benchmark results, metrics snapshots, and performance comparisons.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base

class BenchmarkResult(Base):
    """Model for storing benchmark calculation results."""
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String, nullable=False, index=True)
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)  # company, product, market
    metric_value = Column(Float, nullable=False)
    percentile_rank = Column(Float, nullable=False)  # 0-100
    industry_average = Column(Float)
    industry_sector = Column(String, index=True)
    comparison_group = Column(String)  # peer group used for comparison
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
    calculation_method = Column(String)  # method used for calculation
    confidence_score = Column(Float)  # confidence in the benchmark
    meta_data = Column(JSON)  # additional benchmark metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class MetricsSnapshot(Base):
    """Model for storing point-in-time metrics snapshots."""
    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(String, unique=True, nullable=False, index=True)
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    snapshot_timestamp = Column(DateTime, nullable=False, index=True)
    metrics_data = Column(JSON, nullable=False)  # all metrics at this point in time
    data_sources = Column(JSON)  # sources used for metrics
    quality_score = Column(Float)  # data quality score
    completeness_score = Column(Float)  # data completeness score
    created_at = Column(DateTime, default=datetime.utcnow)

class BenchmarkComparison(Base):
    """Model for storing benchmark comparisons between entities."""
    __tablename__ = "benchmark_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    comparison_id = Column(String, unique=True, nullable=False, index=True)
    entity_a_name = Column(String, nullable=False)
    entity_b_name = Column(String, nullable=False)
    comparison_type = Column(String, nullable=False)  # head_to_head, industry_rank, etc.
    metric_type = Column(String, nullable=False)
    entity_a_value = Column(Float, nullable=False)
    entity_b_value = Column(Float, nullable=False)
    difference_absolute = Column(Float)
    difference_percentage = Column(Float)
    statistical_significance = Column(Float)  # p-value if applicable
    winner = Column(String)  # entity_a, entity_b, or tie
    compared_at = Column(DateTime, default=datetime.utcnow, index=True)
    comparison_period_start = Column(DateTime)
    comparison_period_end = Column(DateTime)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class PerformanceAlert(Base):
    """Model for storing performance alerts and anomalies."""
    __tablename__ = "performance_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, nullable=False, index=True)
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # anomaly, threshold, trend
    metric_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high, critical
    current_value = Column(Float, nullable=False)
    expected_value = Column(Float)
    threshold_value = Column(Float)
    deviation_percentage = Column(Float)
    alert_message = Column(Text)
    triggered_at = Column(DateTime, nullable=False, index=True)
    resolved_at = Column(DateTime)
    status = Column(String, default="active")  # active, resolved, suppressed
    resolution_notes = Column(Text)
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrendAnalysis(Base):
    """Model for storing trend analysis results."""
    __tablename__ = "trend_analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String, unique=True, nullable=False, index=True)
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)
    analysis_type = Column(String, nullable=False)  # linear, seasonal, cyclical
    trend_direction = Column(String)  # increasing, decreasing, stable, volatile
    trend_strength = Column(Float)  # 0-1 strength of trend
    trend_slope = Column(Float)  # rate of change
    seasonality_detected = Column(Boolean, default=False)
    seasonality_period = Column(Integer)  # days/weeks/months
    anomalies_detected = Column(Integer, default=0)
    forecast_horizon_days = Column(Integer)
    forecast_values = Column(JSON)  # predicted future values
    confidence_intervals = Column(JSON)  # confidence bands for forecast
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    model_used = Column(String)  # statistical model used
    model_parameters = Column(JSON)
    goodness_of_fit = Column(Float)  # R-squared or similar
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)