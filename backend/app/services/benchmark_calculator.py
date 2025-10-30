"""
Benchmark Calculation Engine for Advanced Intelligence Suite
Calculates percentile rankings and industry comparisons
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import statistics
import numpy as np

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.benchmarking import (
    BenchmarkMetric, IndustryBenchmark, BenchmarkComparison
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of benchmark calculation"""
    entity_id: str
    entity_type: str
    metric_name: str
    entity_value: float
    benchmark_value: float
    percentile_rank: float
    performance_rating: str
    improvement_potential: float
    competitive_position: str
    key_insights: List[str]
    improvement_recommendations: List[str]


@dataclass
class IndustryBenchmarkData:
    """Industry benchmark data structure"""
    industry_sector: str
    metric_name: str
    percentiles: Dict[int, float]  # 25, 50, 75, 90, 95, 99
    mean: float
    sample_size: int
    confidence_level: float
    data_freshness_days: int


class BenchmarkCalculator:
    """Calculates benchmarks and percentile rankings"""
    
    def __init__(self):
        # Performance rating thresholds (percentile ranks)
        self.rating_thresholds = {
            "excellent": 90,
            "good": 75,
            "average": 50,
            "below_average": 25,
            "poor": 0
        }
        
        # Competitive position thresholds
        self.position_thresholds = {
            "leader": 95,
            "challenger": 80,
            "follower": 50,
            "niche": 0
        }
    
    async def calculate_percentile_rank(
        self,
        value: float,
        benchmark_data: List[float]
    ) -> float:
        """Calculate percentile rank of a value against benchmark data"""
        if not benchmark_data:
            return 50.0  # Default to median if no benchmark data
        
        # Count values less than or equal to the target value
        count_less_equal = sum(1 for x in benchmark_data if x <= value)
        count_less = sum(1 for x in benchmark_data if x < value)
        
        # Use the average rank method for ties
        percentile = ((count_less + count_less_equal) / 2) / len(benchmark_data) * 100
        
        return min(100.0, max(0.0, percentile))
    
    async def get_industry_benchmark(
        self,
        industry_sector: str,
        metric_name: str,
        benchmark_type: str = "percentile"
    ) -> Optional[IndustryBenchmarkData]:
        """Get industry benchmark data for a metric"""
        async with AsyncSessionLocal() as session:
            # Get the most recent benchmark data
            result = await session.execute(
                select(IndustryBenchmark)
                .where(
                    and_(
                        IndustryBenchmark.industry_sector == industry_sector,
                        IndustryBenchmark.metric_name == metric_name,
                        IndustryBenchmark.benchmark_type == benchmark_type
                    )
                )
                .order_by(desc(IndustryBenchmark.created_at))
                .limit(1)
            )
            
            benchmark = result.scalar_one_or_none()
            
            if not benchmark:
                return None
            
            # Get all percentile data for this industry/metric
            percentile_result = await session.execute(
                select(IndustryBenchmark)
                .where(
                    and_(
                        IndustryBenchmark.industry_sector == industry_sector,
                        IndustryBenchmark.metric_name == metric_name,
                        IndustryBenchmark.benchmark_type == "percentile",
                        IndustryBenchmark.percentile_rank.isnot(None)
                    )
                )
                .order_by(IndustryBenchmark.percentile_rank)
            )
            
            percentile_benchmarks = percentile_result.scalars().all()
            
            # Build percentiles dictionary
            percentiles = {}
            mean_value = 0.0
            
            for pb in percentile_benchmarks:
                if pb.percentile_rank:
                    percentiles[pb.percentile_rank] = pb.benchmark_value
            
            # Get the actual mean value from the benchmark record
            mean_value = benchmark.mean_value if hasattr(benchmark, 'mean_value') and benchmark.mean_value else 0.0
            
            return IndustryBenchmarkData(
                industry_sector=industry_sector,
                metric_name=metric_name,
                percentiles=percentiles,
                mean=mean_value,
                sample_size=benchmark.sample_size,
                confidence_level=benchmark.confidence_level,
                data_freshness_days=benchmark.data_freshness_days
            )
    
    async def create_industry_benchmarks(
        self,
        industry_sector: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> IndustryBenchmarkData:
        """Create industry benchmarks from historical data"""
        async with AsyncSessionLocal() as session:
            # Get all metric values for the industry in the time period
            result = await session.execute(
                select(BenchmarkMetric.metric_value)
                .where(
                    and_(
                        BenchmarkMetric.industry_sector == industry_sector,
                        BenchmarkMetric.metric_name == metric_name,
                        BenchmarkMetric.measurement_timestamp >= start_date,
                        BenchmarkMetric.measurement_timestamp <= end_date
                    )
                )
            )
            
            values = [row[0] for row in result.fetchall()]
            
            if len(values) < 10:  # Need minimum sample size
                raise ValueError(f"Insufficient data for benchmark creation: {len(values)} samples")
            
            # Calculate percentiles
            percentiles = {
                25: np.percentile(values, 25),
                50: np.percentile(values, 50),
                75: np.percentile(values, 75),
                90: np.percentile(values, 90),
                95: np.percentile(values, 95),
                99: np.percentile(values, 99)
            }
            
            mean_value = np.mean(values)
            
            # Store benchmark data in database
            benchmark_records = []
            
            for percentile, value in percentiles.items():
                benchmark = IndustryBenchmark(
                    industry_sector=industry_sector,
                    metric_name=metric_name,
                    benchmark_type="percentile",
                    benchmark_value=float(value),
                    percentile_rank=percentile,
                    sample_size=len(values),
                    confidence_level=0.95,
                    data_freshness_days=0,
                    benchmark_period_start=start_date,
                    benchmark_period_end=end_date,
                    data_sources=["internal_metrics"],
                    calculation_method="numpy_percentile",
                    benchmark_metadata={
                        "mean": float(mean_value),
                        "std_dev": float(np.std(values)),
                        "min": float(np.min(values)),
                        "max": float(np.max(values))
                    }
                )
                benchmark_records.append(benchmark)
            
            # Store mean as separate benchmark
            mean_benchmark = IndustryBenchmark(
                industry_sector=industry_sector,
                metric_name=metric_name,
                benchmark_type="mean",
                benchmark_value=float(mean_value),
                percentile_rank=None,
                sample_size=len(values),
                confidence_level=0.95,
                data_freshness_days=0,
                benchmark_period_start=start_date,
                benchmark_period_end=end_date,
                data_sources=["internal_metrics"],
                calculation_method="numpy_mean"
            )
            benchmark_records.append(mean_benchmark)
            
            # Batch insert
            session.add_all(benchmark_records)
            await session.commit()
            
            logger.info(f"Created industry benchmarks for {industry_sector}/{metric_name}")
            
            return IndustryBenchmarkData(
                industry_sector=industry_sector,
                metric_name=metric_name,
                percentiles=percentiles,
                mean=float(mean_value),
                sample_size=len(values),
                confidence_level=0.95,
                data_freshness_days=0
            )
    
    async def calculate_entity_benchmark(
        self,
        entity_id: str,
        entity_type: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        industry_sector: Optional[str] = None
    ) -> BenchmarkResult:
        """Calculate benchmark comparison for an entity"""
        async with AsyncSessionLocal() as session:
            # Get entity's metric values
            conditions = [
                BenchmarkMetric.metric_name == metric_name,
                BenchmarkMetric.measurement_timestamp >= start_date,
                BenchmarkMetric.measurement_timestamp <= end_date
            ]
            
            if entity_type == "workspace":
                conditions.append(BenchmarkMetric.workspace_id == entity_id)
            elif entity_type == "user":
                conditions.append(BenchmarkMetric.user_id == entity_id)
            
            result = await session.execute(
                select(BenchmarkMetric.metric_value)
                .where(and_(*conditions))
            )
            
            entity_values = [row[0] for row in result.fetchall()]
            
            if not entity_values:
                raise ValueError(f"No metric data found for entity {entity_id}")
            
            # Calculate entity's average performance
            entity_value = statistics.mean(entity_values)
            
            # Get industry benchmark
            benchmark_data = None
            if industry_sector:
                benchmark_data = await self.get_industry_benchmark(
                    industry_sector, metric_name
                )
            
            # If no industry benchmark, create one from all available data
            if not benchmark_data:
                # Get all values for this metric (system-wide benchmark)
                all_values_result = await session.execute(
                    select(BenchmarkMetric.metric_value)
                    .where(
                        and_(
                            BenchmarkMetric.metric_name == metric_name,
                            BenchmarkMetric.measurement_timestamp >= start_date,
                            BenchmarkMetric.measurement_timestamp <= end_date
                        )
                    )
                )
                
                all_values = [row[0] for row in all_values_result.fetchall()]
                
                if len(all_values) < 5:
                    # Not enough data for meaningful comparison
                    return BenchmarkResult(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        metric_name=metric_name,
                        entity_value=entity_value,
                        benchmark_value=entity_value,
                        percentile_rank=50.0,
                        performance_rating="average",
                        improvement_potential=0.0,
                        competitive_position="niche",
                        key_insights=["Insufficient benchmark data available"],
                        improvement_recommendations=["Collect more performance data"]
                    )
                
                # Calculate percentile rank against all values
                percentile_rank = await self.calculate_percentile_rank(
                    entity_value, all_values
                )
                benchmark_value = statistics.median(all_values)
                
            else:
                # Use industry benchmark
                benchmark_values = list(benchmark_data.percentiles.values())
                percentile_rank = await self.calculate_percentile_rank(
                    entity_value, benchmark_values
                )
                benchmark_value = benchmark_data.mean
            
            # Determine performance rating
            performance_rating = self._get_performance_rating(percentile_rank)
            
            # Calculate improvement potential
            improvement_potential = self._calculate_improvement_potential(
                entity_value, benchmark_value, percentile_rank
            )
            
            # Determine competitive position
            competitive_position = self._get_competitive_position(percentile_rank)
            
            # Generate insights and recommendations
            key_insights = self._generate_insights(
                entity_value, benchmark_value, percentile_rank, metric_name
            )
            
            improvement_recommendations = self._generate_recommendations(
                performance_rating, metric_name, improvement_potential
            )
            
            return BenchmarkResult(
                entity_id=entity_id,
                entity_type=entity_type,
                metric_name=metric_name,
                entity_value=entity_value,
                benchmark_value=benchmark_value,
                percentile_rank=percentile_rank,
                performance_rating=performance_rating,
                improvement_potential=improvement_potential,
                competitive_position=competitive_position,
                key_insights=key_insights,
                improvement_recommendations=improvement_recommendations
            )
    
    def _get_performance_rating(self, percentile_rank: float) -> str:
        """Get performance rating based on percentile rank"""
        for rating, threshold in self.rating_thresholds.items():
            if percentile_rank >= threshold:
                return rating
        return "poor"
    
    def _get_competitive_position(self, percentile_rank: float) -> str:
        """Get competitive position based on percentile rank"""
        for position, threshold in self.position_thresholds.items():
            if percentile_rank >= threshold:
                return position
        return "niche"
    
    def _calculate_improvement_potential(
        self,
        entity_value: float,
        benchmark_value: float,
        percentile_rank: float
    ) -> float:
        """Calculate improvement potential (0.0 to 1.0)"""
        if percentile_rank >= 95:
            return 0.1  # Already excellent, minimal improvement potential
        elif percentile_rank >= 75:
            return 0.3  # Good performance, moderate improvement potential
        elif percentile_rank >= 50:
            return 0.6  # Average performance, significant improvement potential
        else:
            return 0.9  # Below average, high improvement potential
    
    def _generate_insights(
        self,
        entity_value: float,
        benchmark_value: float,
        percentile_rank: float,
        metric_name: str
    ) -> List[str]:
        """Generate key insights based on benchmark comparison"""
        insights = []
        
        # Performance comparison
        if entity_value > benchmark_value:
            improvement = ((entity_value - benchmark_value) / benchmark_value) * 100
            insights.append(f"Performance is {improvement:.1f}% above industry average")
        else:
            gap = ((benchmark_value - entity_value) / benchmark_value) * 100
            insights.append(f"Performance is {gap:.1f}% below industry average")
        
        # Percentile insights
        if percentile_rank >= 90:
            insights.append("Top 10% performer in this metric")
        elif percentile_rank >= 75:
            insights.append("Above-average performer, in top quartile")
        elif percentile_rank >= 50:
            insights.append("Average performer, room for improvement")
        else:
            insights.append("Below-average performer, significant improvement needed")
        
        # Metric-specific insights
        if "response_time" in metric_name.lower():
            if percentile_rank < 50:
                insights.append("Slow response times may impact user experience")
        elif "accuracy" in metric_name.lower():
            if percentile_rank < 75:
                insights.append("Accuracy improvements could enhance trust and reliability")
        elif "coverage" in metric_name.lower():
            if percentile_rank < 50:
                insights.append("Limited coverage may result in missed competitive intelligence")
        
        return insights
    
    def _generate_recommendations(
        self,
        performance_rating: str,
        metric_name: str,
        improvement_potential: float
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # General recommendations based on performance rating
        if performance_rating == "poor":
            recommendations.append("Immediate attention required - performance is significantly below average")
        elif performance_rating == "below_average":
            recommendations.append("Focus on systematic improvements to reach industry standards")
        elif performance_rating == "average":
            recommendations.append("Optimize processes to move into top quartile performance")
        elif performance_rating == "good":
            recommendations.append("Fine-tune operations to achieve excellence")
        else:  # excellent
            recommendations.append("Maintain current performance and share best practices")
        
        # Metric-specific recommendations
        if "response_time" in metric_name.lower():
            if improvement_potential > 0.5:
                recommendations.extend([
                    "Implement caching strategies to reduce response times",
                    "Optimize database queries and API calls",
                    "Consider CDN implementation for faster content delivery"
                ])
        elif "accuracy" in metric_name.lower():
            if improvement_potential > 0.5:
                recommendations.extend([
                    "Enhance data validation and quality checks",
                    "Implement machine learning model improvements",
                    "Increase training data quality and quantity"
                ])
        elif "coverage" in metric_name.lower():
            if improvement_potential > 0.5:
                recommendations.extend([
                    "Expand monitoring scope to include more competitors",
                    "Add additional data sources for comprehensive coverage",
                    "Implement automated competitor discovery"
                ])
        
        return recommendations
    
    async def store_benchmark_comparison(
        self,
        result: BenchmarkResult,
        industry_sector: Optional[str] = None,
        comparison_period_start: datetime = None,
        comparison_period_end: datetime = None
    ) -> int:
        """Store benchmark comparison result in database"""
        async with AsyncSessionLocal() as session:
            comparison = BenchmarkComparison(
                entity_id=result.entity_id,
                entity_type=result.entity_type,
                metric_name=result.metric_name,
                entity_value=result.entity_value,
                benchmark_value=result.benchmark_value,
                percentile_rank=result.percentile_rank,
                performance_rating=result.performance_rating,
                improvement_potential=result.improvement_potential,
                industry_sector=industry_sector,
                comparison_period_start=comparison_period_start or datetime.utcnow() - timedelta(days=30),
                comparison_period_end=comparison_period_end or datetime.utcnow(),
                key_insights=result.key_insights,
                improvement_recommendations=result.improvement_recommendations,
                competitive_position=result.competitive_position,
                benchmark_source="industry_average",
                confidence_level=0.95,
                comparison_metadata={
                    "calculation_timestamp": datetime.utcnow().isoformat(),
                    "benchmark_type": "percentile_ranking"
                }
            )
            
            session.add(comparison)
            await session.commit()
            
            logger.info(f"Stored benchmark comparison for {result.entity_id}/{result.metric_name}")
            return comparison.id


# Global instance
benchmark_calculator = BenchmarkCalculator()


async def calculate_workspace_benchmarks(
    workspace_id: str,
    industry_sector: Optional[str] = None,
    days_back: int = 30
) -> Dict[str, BenchmarkResult]:
    """Calculate benchmarks for all metrics for a workspace"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Common metrics to benchmark
    metrics_to_benchmark = [
        "api_response_time_news",
        "api_response_time_search",
        "api_success_rate_news",
        "intelligence_confidence",
        "detection_speed",
        "source_diversity",
        "intelligence_generation_rate"
    ]
    
    results = {}
    
    for metric_name in metrics_to_benchmark:
        try:
            result = await benchmark_calculator.calculate_entity_benchmark(
                entity_id=workspace_id,
                entity_type="workspace",
                metric_name=metric_name,
                start_date=start_date,
                end_date=end_date,
                industry_sector=industry_sector
            )
            
            results[metric_name] = result
            
            # Store the comparison
            await benchmark_calculator.store_benchmark_comparison(
                result, industry_sector, start_date, end_date
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate benchmark for {metric_name}: {e}")
    
    return results