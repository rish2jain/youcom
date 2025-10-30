"""
Trend Analysis and Anomaly Detection Service for Advanced Intelligence Suite
Identifies patterns and anomalies in performance data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import statistics
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.benchmarking import (
    BenchmarkMetric, TrendAnalysis, AnomalyDetection
)
from app.realtime import emit_progress

# Note: sklearn warnings are suppressed locally in ML methods

logger = logging.getLogger(__name__)


@dataclass
class TrendResult:
    """Result of trend analysis"""
    metric_name: str
    entity_id: Optional[str]
    entity_type: str
    trend_direction: str  # improving, declining, stable, volatile
    trend_strength: float  # 0.0 to 1.0
    trend_confidence: float  # 0.0 to 1.0
    slope: float
    r_squared: float
    volatility: float
    key_insights: List[str]
    anomalies_detected: List[str]
    recommendations: List[str]
    data_points_count: int
    analysis_period_start: datetime
    analysis_period_end: datetime


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    metric_name: str
    entity_id: Optional[str]
    entity_type: str
    anomaly_type: str  # spike, drop, outlier, pattern_break
    severity: str  # low, medium, high, critical
    anomaly_score: float  # 0.0 to 1.0
    expected_value: float
    actual_value: float
    deviation_percentage: float
    detected_at: datetime
    context: Dict[str, Any]
    root_cause_analysis: str
    recommendations: List[str]


class TrendAnalyzer:
    """Analyzes trends in performance metrics"""
    
    def __init__(self):
        self.min_data_points = 5  # Minimum points needed for trend analysis
        self.volatility_threshold = 0.2  # Threshold for volatile classification
        self.trend_strength_threshold = 0.3  # Minimum strength for significant trend
    
    async def analyze_metric_trend(
        self,
        metric_name: str,
        entity_id: Optional[str] = None,
        entity_type: str = "system",
        start_date: datetime = None,
        end_date: datetime = None,
        min_data_points: int = None
    ) -> TrendResult:
        """Analyze trend for a specific metric"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        if min_data_points:
            self.min_data_points = min_data_points
        
        # Get metric data
        data_points = await self._get_metric_data(
            metric_name, entity_id, entity_type, start_date, end_date
        )
        
        if len(data_points) < self.min_data_points:
            raise ValueError(f"Insufficient data points: {len(data_points)} < {self.min_data_points}")
        
        # Prepare data for analysis
        timestamps = [dp['timestamp'] for dp in data_points]
        values = [dp['value'] for dp in data_points]
        
        # Convert timestamps to numeric values (days since start)
        start_timestamp = min(timestamps)
        x_values = [(ts - start_timestamp).total_seconds() / 86400 for ts in timestamps]
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, values)
        r_squared = r_value ** 2
        
        # Calculate volatility (coefficient of variation)
        mean_value = statistics.mean(values)
        std_value = statistics.stdev(values) if len(values) > 1 else 0
        volatility = std_value / mean_value if mean_value != 0 else 0
        
        # Determine trend direction and strength
        trend_direction, trend_strength = self._classify_trend(
            slope, r_squared, volatility, values
        )
        
        # Calculate trend confidence based on statistical significance
        trend_confidence = min(1.0, max(0.0, r_squared * (1 - p_value)))
        
        # Generate insights and recommendations
        key_insights = self._generate_trend_insights(
            metric_name, trend_direction, trend_strength, slope, volatility
        )
        
        recommendations = self._generate_trend_recommendations(
            metric_name, trend_direction, trend_strength, volatility
        )
        
        # Detect anomalies in the data
        anomalies = await self._detect_trend_anomalies(
            metric_name, entity_id, entity_type, data_points
        )
        
        anomalies_detected = [f"{a.anomaly_type}: {a.actual_value:.2f}" for a in anomalies]
        
        return TrendResult(
            metric_name=metric_name,
            entity_id=entity_id,
            entity_type=entity_type,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_confidence=trend_confidence,
            slope=slope,
            r_squared=r_squared,
            volatility=volatility,
            key_insights=key_insights,
            anomalies_detected=anomalies_detected,
            recommendations=recommendations,
            data_points_count=len(data_points),
            analysis_period_start=start_date,
            analysis_period_end=end_date
        )
    
    async def _get_metric_data(
        self,
        metric_name: str,
        entity_id: Optional[str],
        entity_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get metric data from database"""
        async with AsyncSessionLocal() as session:
            conditions = [
                BenchmarkMetric.metric_name == metric_name,
                BenchmarkMetric.measurement_timestamp >= start_date,
                BenchmarkMetric.measurement_timestamp <= end_date
            ]
            
            if entity_id:
                if entity_type == "workspace":
                    conditions.append(BenchmarkMetric.workspace_id == entity_id)
                elif entity_type == "user":
                    conditions.append(BenchmarkMetric.user_id == entity_id)
            
            result = await session.execute(
                select(
                    BenchmarkMetric.metric_value,
                    BenchmarkMetric.measurement_timestamp,
                    BenchmarkMetric.metric_metadata
                )
                .where(and_(*conditions))
                .order_by(BenchmarkMetric.measurement_timestamp)
            )
            
            return [
                {
                    'value': row[0],
                    'timestamp': row[1],
                    'metadata': row[2] or {}
                }
                for row in result.fetchall()
            ]
    
    def _classify_trend(
        self,
        slope: float,
        r_squared: float,
        volatility: float,
        values: List[float]
    ) -> Tuple[str, float]:
        """Classify trend direction and calculate strength"""
        # Determine if trend is significant
        is_significant = r_squared > 0.1 and abs(slope) > 0.01
        
        # Check for high volatility
        if volatility > self.volatility_threshold:
            return "volatile", volatility
        
        # Classify trend direction
        if not is_significant:
            return "stable", 0.0
        
        # Calculate trend strength (0.0 to 1.0) with division by zero protection
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        denominator = max(stdev, 1e-8)  # Avoid division by zero
        strength = min(1.0, r_squared * abs(slope) / denominator)
        
        # If stdev is zero (all values identical), set strength to 0
        if stdev == 0.0:
            strength = 0.0
        
        if slope > 0:
            return "improving", strength
        else:
            return "declining", strength
    
    def _generate_trend_insights(
        self,
        metric_name: str,
        trend_direction: str,
        trend_strength: float,
        slope: float,
        volatility: float
    ) -> List[str]:
        """Generate insights based on trend analysis"""
        insights = []
        
        # Direction insights
        if trend_direction == "improving":
            insights.append(f"Positive trend detected with {trend_strength:.1%} strength")
        elif trend_direction == "declining":
            insights.append(f"Declining trend detected with {trend_strength:.1%} strength")
        elif trend_direction == "volatile":
            insights.append(f"High volatility detected ({volatility:.1%})")
        else:
            insights.append("Performance is stable with no significant trend")
        
        # Metric-specific insights
        if "response_time" in metric_name.lower():
            if trend_direction == "declining":
                insights.append("Response times are getting slower - investigate performance bottlenecks")
            elif trend_direction == "improving":
                insights.append("Response times are improving - optimizations are working")
        
        elif "accuracy" in metric_name.lower():
            if trend_direction == "improving":
                insights.append("Model accuracy is improving - training is effective")
            elif trend_direction == "declining":
                insights.append("Model accuracy is declining - may need retraining")
        
        elif "success_rate" in metric_name.lower():
            if trend_direction == "declining":
                insights.append("Success rate is declining - investigate error patterns")
        
        # Volatility insights
        if volatility > 0.3:
            insights.append("High variability suggests inconsistent performance")
        elif volatility < 0.1:
            insights.append("Low variability indicates consistent performance")
        
        return insights
    
    def _generate_trend_recommendations(
        self,
        metric_name: str,
        trend_direction: str,
        trend_strength: float,
        volatility: float
    ) -> List[str]:
        """Generate recommendations based on trend analysis"""
        recommendations = []
        
        # Direction-based recommendations
        if trend_direction == "declining" and trend_strength > 0.3:
            recommendations.append("Immediate investigation required - performance is declining")
            recommendations.append("Identify root causes and implement corrective measures")
        
        elif trend_direction == "volatile":
            recommendations.append("Stabilize performance by identifying variability sources")
            recommendations.append("Implement consistent processes and monitoring")
        
        elif trend_direction == "stable":
            recommendations.append("Monitor for changes and optimize for improvement")
        
        elif trend_direction == "improving":
            recommendations.append("Continue current optimizations")
            recommendations.append("Document successful practices for replication")
        
        # Metric-specific recommendations
        if "response_time" in metric_name.lower():
            if trend_direction == "declining":
                recommendations.extend([
                    "Optimize database queries and API calls",
                    "Implement caching strategies",
                    "Scale infrastructure if needed"
                ])
        
        elif "accuracy" in metric_name.lower():
            if trend_direction == "declining":
                recommendations.extend([
                    "Review and improve training data quality",
                    "Retrain models with recent data",
                    "Validate model performance regularly"
                ])
        
        # Volatility recommendations
        if volatility > 0.3:
            recommendations.extend([
                "Implement performance monitoring and alerting",
                "Standardize processes to reduce variability",
                "Investigate external factors affecting performance"
            ])
        
        return recommendations
    
    async def _detect_trend_anomalies(
        self,
        metric_name: str,
        entity_id: Optional[str],
        entity_type: str,
        data_points: List[Dict[str, Any]]
    ) -> List[AnomalyResult]:
        """Detect anomalies within trend data"""
        if len(data_points) < 5:
            return []
        
        values = [dp['value'] for dp in data_points]
        timestamps = [dp['timestamp'] for dp in data_points]
        
        anomalies = []
        
        # Statistical outlier detection using Z-score
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_val > 0:
            for i, (value, timestamp) in enumerate(zip(values, timestamps)):
                z_score = abs((value - mean_val) / std_val)
                
                if z_score > 3:  # 3-sigma rule
                    severity = "critical" if z_score > 4 else "high"
                    anomaly_type = "spike" if value > mean_val else "drop"
                    
                    anomaly = AnomalyResult(
                        metric_name=metric_name,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        anomaly_type=anomaly_type,
                        severity=severity,
                        anomaly_score=min(1.0, z_score / 5.0),
                        expected_value=mean_val,
                        actual_value=value,
                        deviation_percentage=((value - mean_val) / mean_val) * 100,
                        detected_at=timestamp,
                        context={
                            "z_score": z_score,
                            "data_point_index": i,
                            "total_points": len(values)
                        },
                        root_cause_analysis=f"Statistical outlier detected: {z_score:.2f} standard deviations from mean",
                        recommendations=[
                            "Investigate data collection process",
                            "Verify measurement accuracy",
                            "Check for external factors"
                        ]
                    )
                    
                    anomalies.append(anomaly)
        
        return anomalies
    
    async def store_trend_analysis(
        self,
        result: TrendResult
    ) -> int:
        """Store trend analysis result in database"""
        async with AsyncSessionLocal() as session:
            trend_analysis = TrendAnalysis(
                metric_name=result.metric_name,
                entity_id=result.entity_id,
                entity_type=result.entity_type,
                trend_direction=result.trend_direction,
                trend_strength=result.trend_strength,
                trend_confidence=result.trend_confidence,
                slope=result.slope,
                r_squared=result.r_squared,
                volatility=result.volatility,
                analysis_period_start=result.analysis_period_start,
                analysis_period_end=result.analysis_period_end,
                data_points_count=result.data_points_count,
                key_insights=result.key_insights,
                anomalies_detected=result.anomalies_detected,
                recommendations=result.recommendations,
                analysis_method="linear_regression",
                parameters={
                    "min_data_points": self.min_data_points,
                    "volatility_threshold": self.volatility_threshold,
                    "trend_strength_threshold": self.trend_strength_threshold
                }
            )
            
            session.add(trend_analysis)
            await session.commit()
            
            logger.info(f"Stored trend analysis for {result.metric_name}")
            return trend_analysis.id


class AnomalyDetector:
    """Detects anomalies in performance metrics"""
    
    def __init__(self):
        self.z_score_threshold = 3.0  # Standard deviations for outlier detection
        self.pattern_break_threshold = 0.5  # Threshold for pattern break detection
        self.spike_threshold = 2.0  # Multiplier for spike detection
    
    async def detect_anomalies(
        self,
        metric_name: str,
        entity_id: Optional[str] = None,
        entity_type: str = "system",
        start_date: datetime = None,
        end_date: datetime = None,
        detection_method: str = "statistical"
    ) -> List[AnomalyResult]:
        """Detect anomalies in metric data"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get metric data
        data_points = await self._get_metric_data(
            metric_name, entity_id, entity_type, start_date, end_date
        )
        
        if len(data_points) < 5:
            return []
        
        if detection_method == "statistical":
            return await self._statistical_anomaly_detection(
                metric_name, entity_id, entity_type, data_points
            )
        elif detection_method == "ml_based":
            return await self._ml_anomaly_detection(
                metric_name, entity_id, entity_type, data_points
            )
        else:
            return await self._threshold_anomaly_detection(
                metric_name, entity_id, entity_type, data_points
            )
    
    async def _get_metric_data(
        self,
        metric_name: str,
        entity_id: Optional[str],
        entity_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get metric data from database"""
        async with AsyncSessionLocal() as session:
            conditions = [
                BenchmarkMetric.metric_name == metric_name,
                BenchmarkMetric.measurement_timestamp >= start_date,
                BenchmarkMetric.measurement_timestamp <= end_date
            ]
            
            if entity_id:
                if entity_type == "workspace":
                    conditions.append(BenchmarkMetric.workspace_id == entity_id)
                elif entity_type == "user":
                    conditions.append(BenchmarkMetric.user_id == entity_id)
            
            result = await session.execute(
                select(
                    BenchmarkMetric.metric_value,
                    BenchmarkMetric.measurement_timestamp,
                    BenchmarkMetric.metric_metadata
                )
                .where(and_(*conditions))
                .order_by(BenchmarkMetric.measurement_timestamp)
            )
            
            return [
                {
                    'value': row[0],
                    'timestamp': row[1],
                    'metadata': row[2] or {}
                }
                for row in result.fetchall()
            ]
    
    async def _statistical_anomaly_detection(
        self,
        metric_name: str,
        entity_id: Optional[str],
        entity_type: str,
        data_points: List[Dict[str, Any]]
    ) -> List[AnomalyResult]:
        """Statistical anomaly detection using Z-score and IQR"""
        values = [dp['value'] for dp in data_points]
        timestamps = [dp['timestamp'] for dp in data_points]
        
        anomalies = []
        
        # Z-score based detection
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        
        # IQR based detection
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            is_anomaly = False
            anomaly_type = "outlier"
            severity = "low"
            anomaly_score = 0.0
            detection_reason = ""
            
            # Z-score check
            if std_val > 0:
                z_score = abs((value - mean_val) / std_val)
                if z_score > self.z_score_threshold:
                    is_anomaly = True
                    anomaly_score = max(anomaly_score, min(1.0, z_score / 5.0))
                    detection_reason += f"Z-score: {z_score:.2f}; "
                    
                    if z_score > 4:
                        severity = "critical"
                    elif z_score > 3.5:
                        severity = "high"
                    else:
                        severity = "medium"
            
            # IQR check
            if value < lower_bound or value > upper_bound:
                is_anomaly = True
                iqr_score = max(
                    abs(value - lower_bound) / iqr if value < lower_bound else 0,
                    abs(value - upper_bound) / iqr if value > upper_bound else 0
                )
                anomaly_score = max(anomaly_score, min(1.0, iqr_score / 3.0))
                detection_reason += f"IQR outlier; "
            
            # Spike detection (sudden large changes)
            if i > 0:
                prev_value = values[i-1]
                if prev_value != 0:
                    change_ratio = abs(value - prev_value) / abs(prev_value)
                    if change_ratio > self.spike_threshold:
                        is_anomaly = True
                        anomaly_type = "spike" if value > prev_value else "drop"
                        spike_score = min(1.0, change_ratio / 5.0)
                        anomaly_score = max(anomaly_score, spike_score)
                        detection_reason += f"Sudden change: {change_ratio:.1%}; "
                        
                        if change_ratio > 5.0:
                            severity = "critical"
                        elif change_ratio > 3.0:
                            severity = "high"
                        else:
                            severity = "medium"
            
            if is_anomaly:
                anomaly = AnomalyResult(
                    metric_name=metric_name,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    anomaly_score=anomaly_score,
                    expected_value=mean_val,
                    actual_value=value,
                    deviation_percentage=((value - mean_val) / mean_val) * 100 if mean_val != 0 else 0,
                    detected_at=timestamp,
                    context={
                        "detection_method": "statistical",
                        "z_score": z_score if std_val > 0 else None,
                        "iqr_bounds": [lower_bound, upper_bound],
                        "data_point_index": i
                    },
                    root_cause_analysis=f"Statistical anomaly: {detection_reason.strip('; ')}",
                    recommendations=self._generate_anomaly_recommendations(
                        anomaly_type, severity, metric_name
                    )
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _ml_anomaly_detection(
        self,
        metric_name: str,
        entity_id: Optional[str],
        entity_type: str,
        data_points: List[Dict[str, Any]]
    ) -> List[AnomalyResult]:
        """ML-based anomaly detection using DBSCAN clustering"""
        if len(data_points) < 10:  # Need more data for ML methods
            return []
        
        values = np.array([dp['value'] for dp in data_points]).reshape(-1, 1)
        timestamps = [dp['timestamp'] for dp in data_points]
        
        # Standardize the data
        scaler = StandardScaler()
        scaled_values = scaler.fit_transform(values)
        
        # Apply DBSCAN clustering with local warning suppression
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)
            dbscan = DBSCAN(eps=0.5, min_samples=3)
            clusters = dbscan.fit_predict(scaled_values)
        
        anomalies = []
        
        # Points labeled as -1 are considered anomalies by DBSCAN
        for i, (cluster_label, value, timestamp) in enumerate(zip(clusters, values.flatten(), timestamps)):
            if cluster_label == -1:  # Anomaly
                # Calculate anomaly score based on distance to nearest cluster
                distances = []
                for j, other_cluster in enumerate(clusters):
                    if other_cluster != -1:
                        distances.append(abs(scaled_values[i][0] - scaled_values[j][0]))
                
                if distances:
                    min_distance = min(distances)
                    anomaly_score = min(1.0, min_distance / 2.0)
                else:
                    anomaly_score = 1.0
                
                # Determine severity based on anomaly score
                if anomaly_score > 0.8:
                    severity = "critical"
                elif anomaly_score > 0.6:
                    severity = "high"
                elif anomaly_score > 0.4:
                    severity = "medium"
                else:
                    severity = "low"
                
                mean_val = np.mean(values)
                anomaly_type = "spike" if value > mean_val else "drop"
                
                anomaly = AnomalyResult(
                    metric_name=metric_name,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    anomaly_score=anomaly_score,
                    expected_value=float(mean_val),
                    actual_value=float(value),
                    deviation_percentage=((value - mean_val) / mean_val) * 100 if mean_val != 0 else 0,
                    detected_at=timestamp,
                    context={
                        "detection_method": "ml_dbscan",
                        "cluster_label": int(cluster_label),
                        "min_distance": min_distance if distances else None,
                        "data_point_index": i
                    },
                    root_cause_analysis=f"ML-based anomaly detection: isolated data point (cluster {cluster_label})",
                    recommendations=self._generate_anomaly_recommendations(
                        anomaly_type, severity, metric_name
                    )
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _threshold_anomaly_detection(
        self,
        metric_name: str,
        entity_id: Optional[str],
        entity_type: str,
        data_points: List[Dict[str, Any]]
    ) -> List[AnomalyResult]:
        """Threshold-based anomaly detection using predefined limits"""
        # Define metric-specific thresholds
        thresholds = {
            "api_response_time": {"critical": 10000, "high": 5000, "medium": 2000},  # milliseconds
            "api_success_rate": {"critical": 0.8, "high": 0.9, "medium": 0.95},  # percentage (inverted)
            "intelligence_confidence": {"critical": 0.5, "high": 0.7, "medium": 0.8},  # percentage (inverted)
            "detection_speed": {"critical": 300, "high": 120, "medium": 60},  # minutes
        }
        
        # Find matching threshold
        threshold_config = None
        for key, config in thresholds.items():
            if key in metric_name.lower():
                threshold_config = config
                break
        
        if not threshold_config:
            return []  # No thresholds defined for this metric
        
        anomalies = []
        values = [dp['value'] for dp in data_points]
        timestamps = [dp['timestamp'] for dp in data_points]
        
        # Determine if lower values are worse (for success rates, confidence)
        lower_is_worse = any(term in metric_name.lower() for term in ["success_rate", "confidence", "accuracy"])
        
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            severity = None
            
            if lower_is_worse:
                # For metrics where lower values are worse
                if value <= threshold_config["critical"]:
                    severity = "critical"
                elif value <= threshold_config["high"]:
                    severity = "high"
                elif value <= threshold_config["medium"]:
                    severity = "medium"
            else:
                # For metrics where higher values are worse
                if value >= threshold_config["critical"]:
                    severity = "critical"
                elif value >= threshold_config["high"]:
                    severity = "high"
                elif value >= threshold_config["medium"]:
                    severity = "medium"
            
            if severity:
                expected_value = threshold_config["medium"]  # Use medium threshold as expected
                anomaly_score = self._calculate_threshold_score(
                    value, threshold_config, lower_is_worse
                )
                
                anomaly_type = "drop" if lower_is_worse else "spike"
                
                anomaly = AnomalyResult(
                    metric_name=metric_name,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    anomaly_score=anomaly_score,
                    expected_value=expected_value,
                    actual_value=value,
                    deviation_percentage=((value - expected_value) / expected_value) * 100 if expected_value != 0 else 0,
                    detected_at=timestamp,
                    context={
                        "detection_method": "threshold",
                        "threshold_config": threshold_config,
                        "lower_is_worse": lower_is_worse,
                        "data_point_index": i
                    },
                    root_cause_analysis=f"Threshold violation: {value} {'below' if lower_is_worse else 'above'} {severity} threshold",
                    recommendations=self._generate_anomaly_recommendations(
                        anomaly_type, severity, metric_name
                    )
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_threshold_score(
        self,
        value: float,
        threshold_config: Dict[str, float],
        lower_is_worse: bool
    ) -> float:
        """Calculate anomaly score based on threshold violation"""
        if lower_is_worse:
            if value <= threshold_config["critical"]:
                return 1.0
            elif value <= threshold_config["high"]:
                return 0.8
            elif value <= threshold_config["medium"]:
                return 0.6
        else:
            if value >= threshold_config["critical"]:
                return 1.0
            elif value >= threshold_config["high"]:
                return 0.8
            elif value >= threshold_config["medium"]:
                return 0.6
        
        return 0.0
    
    def _generate_anomaly_recommendations(
        self,
        anomaly_type: str,
        severity: str,
        metric_name: str
    ) -> List[str]:
        """Generate recommendations based on anomaly type and severity"""
        recommendations = []
        
        # Severity-based recommendations
        if severity == "critical":
            recommendations.append("Immediate investigation required - critical anomaly detected")
            recommendations.append("Consider emergency response procedures")
        elif severity == "high":
            recommendations.append("High priority investigation needed")
            recommendations.append("Monitor closely for additional anomalies")
        else:
            recommendations.append("Monitor and investigate when resources allow")
        
        # Anomaly type recommendations
        if anomaly_type == "spike":
            recommendations.extend([
                "Investigate sudden increase in metric value",
                "Check for external factors or system changes",
                "Verify data collection accuracy"
            ])
        elif anomaly_type == "drop":
            recommendations.extend([
                "Investigate sudden decrease in metric value",
                "Check for system failures or performance issues",
                "Verify service availability"
            ])
        
        # Metric-specific recommendations
        if "response_time" in metric_name.lower():
            recommendations.extend([
                "Check server performance and resource utilization",
                "Investigate database query performance",
                "Review recent deployments or configuration changes"
            ])
        elif "success_rate" in metric_name.lower():
            recommendations.extend([
                "Investigate error patterns and failure modes",
                "Check API endpoint health and dependencies",
                "Review error logs for root cause analysis"
            ])
        elif "confidence" in metric_name.lower():
            recommendations.extend([
                "Review model performance and training data",
                "Check for data quality issues",
                "Consider model retraining if needed"
            ])
        
        return recommendations
    
    async def store_anomaly(
        self,
        anomaly: AnomalyResult
    ) -> int:
        """Store anomaly detection result in database"""
        async with AsyncSessionLocal() as session:
            anomaly_record = AnomalyDetection(
                metric_name=anomaly.metric_name,
                entity_id=anomaly.entity_id,
                entity_type=anomaly.entity_type,
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
                anomaly_score=anomaly.anomaly_score,
                expected_value=anomaly.expected_value,
                actual_value=anomaly.actual_value,
                deviation_percentage=anomaly.deviation_percentage,
                detected_at=anomaly.detected_at,
                context=anomaly.context,
                root_cause_analysis=anomaly.root_cause_analysis,
                detection_method=anomaly.context.get("detection_method", "unknown"),
                detection_parameters=anomaly.context,
                alert_sent=False,  # Will be updated when alert is sent
                resolution_status="open"
            )
            
            session.add(anomaly_record)
            await session.commit()
            
            logger.info(f"Stored anomaly for {anomaly.metric_name}: {anomaly.anomaly_type} ({anomaly.severity})")
            return anomaly_record.id
    
    async def send_anomaly_alert(
        self,
        anomaly: AnomalyResult,
        recipients: List[str] = None
    ):
        """Send real-time alert for detected anomaly"""
        alert_data = {
            "type": "anomaly_detected",
            "metric_name": anomaly.metric_name,
            "anomaly_type": anomaly.anomaly_type,
            "severity": anomaly.severity,
            "actual_value": anomaly.actual_value,
            "expected_value": anomaly.expected_value,
            "deviation_percentage": anomaly.deviation_percentage,
            "detected_at": anomaly.detected_at.isoformat(),
            "recommendations": anomaly.recommendations[:3],  # Top 3 recommendations
            "entity_id": anomaly.entity_id,
            "entity_type": anomaly.entity_type
        }
        
        # Emit via WebSocket
        await emit_progress("anomaly_alert", alert_data)
        
        logger.info(f"Sent anomaly alert for {anomaly.metric_name}: {anomaly.severity} {anomaly.anomaly_type}")


# Global instances
trend_analyzer = TrendAnalyzer()
anomaly_detector = AnomalyDetector()


async def analyze_all_metrics_trends(
    entity_id: Optional[str] = None,
    entity_type: str = "system",
    days_back: int = 30
) -> Dict[str, TrendResult]:
    """Analyze trends for all available metrics"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get list of available metrics
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BenchmarkMetric.metric_name)
            .distinct()
            .where(
                BenchmarkMetric.measurement_timestamp >= start_date
            )
        )
        
        metric_names = [row[0] for row in result.fetchall()]
    
    trends = {}
    
    for metric_name in metric_names:
        try:
            trend_result = await trend_analyzer.analyze_metric_trend(
                metric_name=metric_name,
                entity_id=entity_id,
                entity_type=entity_type,
                start_date=start_date,
                end_date=end_date
            )
            
            trends[metric_name] = trend_result
            
            # Store the trend analysis
            await trend_analyzer.store_trend_analysis(trend_result)
            
        except Exception as e:
            logger.warning(f"Failed to analyze trend for {metric_name}: {e}")
    
    return trends


async def detect_all_metrics_anomalies(
    entity_id: Optional[str] = None,
    entity_type: str = "system",
    days_back: int = 7,
    detection_method: str = "statistical"
) -> Dict[str, List[AnomalyResult]]:
    """Detect anomalies for all available metrics"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get list of available metrics
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BenchmarkMetric.metric_name)
            .distinct()
            .where(
                BenchmarkMetric.measurement_timestamp >= start_date
            )
        )
        
        metric_names = [row[0] for row in result.fetchall()]
    
    all_anomalies = {}
    
    for metric_name in metric_names:
        try:
            anomalies = await anomaly_detector.detect_anomalies(
                metric_name=metric_name,
                entity_id=entity_id,
                entity_type=entity_type,
                start_date=start_date,
                end_date=end_date,
                detection_method=detection_method
            )
            
            if anomalies:
                all_anomalies[metric_name] = anomalies
                
                # Store and alert for each anomaly
                for anomaly in anomalies:
                    await anomaly_detector.store_anomaly(anomaly)
                    
                    # Send alert for high and critical severity anomalies
                    if anomaly.severity in ["high", "critical"]:
                        await anomaly_detector.send_anomaly_alert(anomaly)
            
        except Exception as e:
            logger.warning(f"Failed to detect anomalies for {metric_name}: {e}")
    
    return all_anomalies