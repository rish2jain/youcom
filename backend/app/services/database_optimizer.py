"""
Database Optimization Service

This service provides database query optimization, indexing strategies,
and connection pooling for Advanced Intelligence Suite components.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, inspect, Index, Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.models.sentiment_analysis import SentimentAnalysis, SentimentTrend
from app.models.benchmarking import BenchmarkResult, MetricsSnapshot, TrendAnalysis
from app.models.ml_training import TrainingJob, ModelPerformanceMetric, FeedbackRecord
from app.models.industry_template import IndustryTemplate, TemplateApplication
from app.config import settings

logger = logging.getLogger(__name__)

class IndexType(str, Enum):
    """Types of database indexes."""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    PARTIAL = "partial"
    COMPOSITE = "composite"

class OptimizationType(str, Enum):
    """Types of database optimizations."""
    INDEX_CREATION = "index_creation"
    QUERY_REWRITE = "query_rewrite"
    PARTITION_SETUP = "partition_setup"
    CONNECTION_POOLING = "connection_pooling"
    VACUUM_ANALYZE = "vacuum_analyze"

@dataclass
class IndexRecommendation:
    """Database index recommendation."""
    table_name: str
    columns: List[str]
    index_type: IndexType
    estimated_benefit: float
    creation_cost: float
    maintenance_cost: float
    usage_frequency: int
    selectivity: float
    reason: str

@dataclass
class QueryOptimization:
    """Query optimization recommendation."""
    query_pattern: str
    current_cost: float
    optimized_cost: float
    optimization_type: OptimizationType
    recommendation: str
    estimated_improvement: float

@dataclass
class ConnectionPoolStats:
    """Connection pool statistics."""
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    total_connections: int
    avg_connection_time_ms: float
    max_connection_time_ms: float

class DatabaseOptimizer:
    """Service for database optimization and performance tuning."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = self.db.get_bind()
        
        # Query performance tracking
        self.query_stats: Dict[str, List[float]] = {}
        self.slow_query_threshold_ms = 1000
        self.query_history_size = 1000
        
        # Index recommendations cache
        self.index_recommendations: List[IndexRecommendation] = []
        self.last_analysis_time = datetime.min
        self.analysis_interval = timedelta(hours=6)
        
        # Connection pool configuration
        self.pool_config = {
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True
        }
        
        # Optimization history
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Critical indexes for Advanced Intelligence Suite
        self.critical_indexes = [
            # Sentiment Analysis indexes
            {
                "table": "sentiment_analyses",
                "columns": ["entity_name", "entity_type", "processing_timestamp"],
                "type": IndexType.COMPOSITE,
                "reason": "Frequent queries by entity and time range"
            },
            {
                "table": "sentiment_analyses",
                "columns": ["processing_timestamp"],
                "type": IndexType.BTREE,
                "reason": "Time-based queries and cleanup operations"
            },
            {
                "table": "sentiment_trends",
                "columns": ["entity_name", "entity_type", "timeframe", "period_start"],
                "type": IndexType.COMPOSITE,
                "reason": "Trend analysis queries"
            },
            
            # Benchmarking indexes
            {
                "table": "benchmark_results",
                "columns": ["metric_type", "calculated_at"],
                "type": IndexType.COMPOSITE,
                "reason": "Benchmark queries by type and time"
            },
            {
                "table": "benchmark_results",
                "columns": ["entity_name", "industry_sector"],
                "type": IndexType.COMPOSITE,
                "reason": "Entity and industry comparisons"
            },
            {
                "table": "metrics_snapshots",
                "columns": ["entity_name", "snapshot_timestamp"],
                "type": IndexType.COMPOSITE,
                "reason": "Time-series metrics queries"
            },
            
            # ML Training indexes
            {
                "table": "ml_training_jobs",
                "columns": ["model_type", "status", "created_at"],
                "type": IndexType.COMPOSITE,
                "reason": "Training job monitoring and history"
            },
            {
                "table": "ml_performance_metrics",
                "columns": ["model_version", "metric_name", "evaluation_timestamp"],
                "type": IndexType.COMPOSITE,
                "reason": "Model performance tracking"
            },
            {
                "table": "ml_feedback_records",
                "columns": ["processed", "feedback_type", "feedback_timestamp"],
                "type": IndexType.COMPOSITE,
                "reason": "Feedback processing queries"
            },
            
            # Template indexes
            {
                "table": "industry_templates",
                "columns": ["industry_sector", "rating", "usage_count"],
                "type": IndexType.COMPOSITE,
                "reason": "Template discovery and ranking"
            },
            {
                "table": "template_applications",
                "columns": ["workspace_id", "applied_at"],
                "type": IndexType.COMPOSITE,
                "reason": "User template history"
            }
        ]
    
    async def initialize(self) -> None:
        """Initialize the database optimizer."""
        try:
            # Engine is already set from the session in __init__
            logger.info("Database optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database optimizer: {e}")
            raise
    
    async def analyze_and_optimize(self) -> Dict[str, Any]:
        """Perform comprehensive database analysis and optimization."""
        try:
            optimization_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "indexes_created": 0,
                "queries_optimized": 0,
                "performance_improvement": 0.0,
                "recommendations": [],
                "errors": []
            }
            
            # Analyze current database state
            await self._analyze_database_performance()
            
            # Create missing critical indexes
            indexes_created = await self._create_critical_indexes()
            optimization_results["indexes_created"] = indexes_created
            
            # Analyze and optimize slow queries
            query_optimizations = await self._analyze_slow_queries()
            optimization_results["queries_optimized"] = len(query_optimizations)
            optimization_results["recommendations"].extend(query_optimizations)
            
            # Update table statistics
            await self._update_table_statistics()
            
            # Generate index recommendations
            index_recommendations = await self._generate_index_recommendations()
            optimization_results["recommendations"].extend(index_recommendations)
            
            # Store optimization results
            self.optimization_history.append(optimization_results)
            
            logger.info(f"Database optimization completed: {indexes_created} indexes created, "
                       f"{len(query_optimizations)} queries analyzed")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise
    
    async def _analyze_database_performance(self) -> None:
        """Analyze current database performance metrics."""
        try:
            # Get database size and statistics
            async with self.engine.begin() as conn:
                # Database size
                size_result = await conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """))
                db_size = size_result.scalar()
                
                # Table sizes
                table_sizes_result = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                    LIMIT 20
                """))
                
                table_sizes = [dict(row) for row in table_sizes_result.fetchall()]
                
                # Index usage statistics
                index_usage_result = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 50
                """))
                
                index_usage = [dict(row) for row in index_usage_result.fetchall()]
                
                logger.info(f"Database analysis: Size={db_size}, Tables={len(table_sizes)}, Indexes={len(index_usage)}")
                
        except Exception as e:
            logger.error(f"Database performance analysis failed: {e}")
    
    async def _create_critical_indexes(self) -> int:
        """Create critical indexes for Advanced Intelligence Suite."""
        indexes_created = 0
        
        try:
            async with self.engine.begin() as conn:
                # Check existing indexes
                existing_indexes_result = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                """))
                
                existing_indexes = {
                    f"{row.tablename}_{row.indexname}": row.indexdef
                    for row in existing_indexes_result.fetchall()
                }
                
                # Create missing critical indexes
                for index_spec in self.critical_indexes:
                    index_name = f"idx_{index_spec['table']}_{'_'.join(index_spec['columns'])}"
                    index_key = f"{index_spec['table']}_{index_name}"
                    
                    if index_key not in existing_indexes:
                        try:
                            # Create index
                            columns_str = ", ".join(index_spec['columns'])
                            create_sql = f"""
                                CREATE INDEX CONCURRENTLY {index_name}
                                ON {index_spec['table']} ({columns_str})
                            """
                            
                            await conn.execute(text(create_sql))
                            indexes_created += 1
                            
                            logger.info(f"Created index: {index_name} on {index_spec['table']}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to create index {index_name}: {e}")
                
        except Exception as e:
            logger.error(f"Critical index creation failed: {e}")
        
        return indexes_created
    
    async def _analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze slow queries and provide optimization recommendations."""
        optimizations = []
        
        try:
            async with self.engine.begin() as conn:
                # Get slow queries from pg_stat_statements if available
                try:
                    slow_queries_result = await conn.execute(text("""
                        SELECT 
                            query,
                            calls,
                            total_time,
                            mean_time,
                            rows,
                            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                        FROM pg_stat_statements
                        WHERE mean_time > %s
                        ORDER BY mean_time DESC
                        LIMIT 20
                    """), (self.slow_query_threshold_ms,))
                    
                    slow_queries = [dict(row) for row in slow_queries_result.fetchall()]
                    
                    for query_stat in slow_queries:
                        optimization = {
                            "type": "slow_query",
                            "query_pattern": query_stat["query"][:200] + "..." if len(query_stat["query"]) > 200 else query_stat["query"],
                            "mean_time_ms": float(query_stat["mean_time"]),
                            "calls": query_stat["calls"],
                            "total_time_ms": float(query_stat["total_time"]),
                            "hit_percent": float(query_stat["hit_percent"]) if query_stat["hit_percent"] else 0.0,
                            "recommendation": self._generate_query_recommendation(query_stat)
                        }
                        optimizations.append(optimization)
                
                except Exception as e:
                    logger.info(f"pg_stat_statements not available: {e}")
                    # Fallback to basic query analysis
                    optimizations.append({
                        "type": "analysis_unavailable",
                        "recommendation": "Install pg_stat_statements extension for detailed query analysis"
                    })
            
        except Exception as e:
            logger.error(f"Slow query analysis failed: {e}")
        
        return optimizations
    
    def _generate_query_recommendation(self, query_stat: Dict[str, Any]) -> str:
        """Generate optimization recommendation for a slow query."""
        recommendations = []
        
        query = query_stat["query"].lower()
        mean_time = query_stat["mean_time"]
        hit_percent = query_stat.get("hit_percent", 0)
        
        # High execution time
        if mean_time > 5000:
            recommendations.append("Consider query rewriting or adding indexes")
        
        # Low cache hit rate
        if hit_percent < 90:
            recommendations.append("Low buffer cache hit rate - consider adding indexes or increasing shared_buffers")
        
        # Common patterns
        if "order by" in query and "limit" in query:
            recommendations.append("Consider adding index on ORDER BY columns for LIMIT queries")
        
        if "where" in query and "like" in query:
            recommendations.append("Consider using GIN index for text search or rewriting LIKE patterns")
        
        if "group by" in query:
            recommendations.append("Consider adding composite index on GROUP BY columns")
        
        if "join" in query:
            recommendations.append("Ensure JOIN columns are properly indexed")
        
        return "; ".join(recommendations) if recommendations else "Review query execution plan"
    
    async def _update_table_statistics(self) -> None:
        """Update table statistics for query planner."""
        try:
            async with self.engine.begin() as conn:
                # Run ANALYZE on key tables
                key_tables = [
                    "sentiment_analyses",
                    "sentiment_trends", 
                    "benchmark_results",
                    "ml_training_jobs",
                    "ml_performance_metrics",
                    "industry_templates"
                ]
                
                for table in key_tables:
                    try:
                        await conn.execute(text(f"ANALYZE {table}"))
                        logger.debug(f"Updated statistics for table: {table}")
                    except Exception as e:
                        logger.warning(f"Failed to analyze table {table}: {e}")
                
                logger.info(f"Updated statistics for {len(key_tables)} tables")
                
        except Exception as e:
            logger.error(f"Table statistics update failed: {e}")
    
    async def _generate_index_recommendations(self) -> List[Dict[str, Any]]:
        """Generate index recommendations based on query patterns."""
        recommendations = []
        
        try:
            async with self.engine.begin() as conn:
                # Analyze table access patterns
                table_stats_result = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    ORDER BY seq_scan DESC
                """))
                
                table_stats = [dict(row) for row in table_stats_result.fetchall()]
                
                for table_stat in table_stats:
                    table_name = table_stat["tablename"]
                    seq_scan = table_stat["seq_scan"] or 0
                    idx_scan = table_stat["idx_scan"] or 0
                    
                    # High sequential scan ratio indicates missing indexes
                    if seq_scan > 0 and (seq_scan / max(seq_scan + idx_scan, 1)) > 0.3:
                        recommendations.append({
                            "type": "missing_index",
                            "table": table_name,
                            "seq_scans": seq_scan,
                            "index_scans": idx_scan,
                            "recommendation": f"Table {table_name} has high sequential scan ratio ({seq_scan} seq vs {idx_scan} idx). Consider adding indexes on frequently queried columns."
                        })
                
                # Check for unused indexes
                unused_indexes_result = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size
                    FROM pg_stat_user_indexes
                    WHERE idx_scan < 10
                    AND schemaname = 'public'
                    ORDER BY pg_relation_size(indexrelid) DESC
                """))
                
                unused_indexes = [dict(row) for row in unused_indexes_result.fetchall()]
                
                for unused_index in unused_indexes:
                    recommendations.append({
                        "type": "unused_index",
                        "table": unused_index["tablename"],
                        "index": unused_index["indexname"],
                        "scans": unused_index["idx_scan"],
                        "size": unused_index["size"],
                        "recommendation": f"Index {unused_index['indexname']} is rarely used ({unused_index['idx_scan']} scans) but takes {unused_index['size']}. Consider dropping if not needed."
                    })
                
        except Exception as e:
            logger.error(f"Index recommendation generation failed: {e}")
        
        return recommendations
    
    async def create_time_series_partitions(self, table_name: str, date_column: str) -> bool:
        """Create time-based partitions for large time-series tables."""
        try:
            async with self.engine.begin() as conn:
                # Check if table is already partitioned
                partition_check_result = await conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM pg_partitioned_table 
                    WHERE partrelid = %s::regclass
                """), (table_name,))
                
                is_partitioned = partition_check_result.scalar() > 0
                
                if is_partitioned:
                    logger.info(f"Table {table_name} is already partitioned")
                    return True
                
                # Create partitioned table (this would require more complex logic)
                # For now, just log the recommendation
                logger.info(f"Recommendation: Consider partitioning {table_name} by {date_column} for better performance")
                
                return False
                
        except Exception as e:
            logger.error(f"Partition creation failed for {table_name}: {e}")
            return False
    
    async def optimize_connection_pool(self) -> Dict[str, Any]:
        """Optimize database connection pool settings."""
        try:
            # Get current connection statistics
            async with self.engine.begin() as conn:
                conn_stats_result = await conn.execute(text("""
                    SELECT 
                        state,
                        COUNT(*) as count
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    GROUP BY state
                """))
                
                conn_stats = {row.state: row.count for row in conn_stats_result.fetchall()}
                
                # Get connection pool info (if available)
                pool_info = {
                    "configured_pool_size": self.pool_config["pool_size"],
                    "configured_overflow": self.pool_config["max_overflow"],
                    "current_connections": conn_stats,
                    "recommendations": []
                }
                
                # Generate recommendations
                total_connections = sum(conn_stats.values())
                active_connections = conn_stats.get("active", 0)
                idle_connections = conn_stats.get("idle", 0)
                
                if total_connections > self.pool_config["pool_size"] + self.pool_config["max_overflow"]:
                    pool_info["recommendations"].append("Consider increasing pool size or max_overflow")
                
                if idle_connections > active_connections * 2:
                    pool_info["recommendations"].append("High number of idle connections - consider reducing pool_size")
                
                if active_connections > self.pool_config["pool_size"] * 0.8:
                    pool_info["recommendations"].append("High pool utilization - consider increasing pool_size")
                
                return pool_info
                
        except Exception as e:
            logger.error(f"Connection pool optimization failed: {e}")
            return {"error": str(e)}
    
    async def vacuum_and_reindex(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform VACUUM and REINDEX operations on specified tables."""
        results = {
            "vacuumed_tables": [],
            "reindexed_tables": [],
            "errors": []
        }
        
        try:
            # Default to key tables if none specified
            if not table_names:
                table_names = [
                    "sentiment_analyses",
                    "sentiment_trends",
                    "benchmark_results",
                    "ml_training_jobs",
                    "ml_performance_metrics"
                ]
            
            async with self.engine.begin() as conn:
                for table_name in table_names:
                    try:
                        # VACUUM ANALYZE
                        await conn.execute(text(f"VACUUM ANALYZE {table_name}"))
                        results["vacuumed_tables"].append(table_name)
                        
                        # REINDEX (only if needed - check bloat first)
                        bloat_result = await conn.execute(text("""
                            SELECT 
                                schemaname,
                                tablename,
                                ROUND((CASE WHEN otta=0 THEN 0.0 ELSE sml.relpages::FLOAT/otta END)::NUMERIC,1) AS tbloat
                            FROM (
                                SELECT 
                                    schemaname, tablename, cc.relpages, bs,
                                    CEIL((cc.reltuples*((datahdr+ma-
                                        (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4))/(bs-20::FLOAT)) AS otta
                                FROM (
                                    SELECT 
                                        ma,bs,schemaname,tablename,
                                        (datawidth+(hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)))::NUMERIC AS datahdr,
                                        (maxfracsum*(nullhdr+ma-(CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
                                    FROM (
                                        SELECT 
                                            schemaname, tablename, hdr, ma, bs,
                                            SUM((1-null_frac)*avg_width) AS datawidth,
                                            MAX(null_frac) AS maxfracsum,
                                            hdr+(
                                                SELECT 1+COUNT(*)/8
                                                FROM pg_stats s2
                                                WHERE null_frac<>0 AND s2.schemaname = s.schemaname AND s2.tablename = s.tablename
                                            ) AS nullhdr
                                        FROM pg_stats s, (
                                            SELECT 
                                                (SELECT current_setting('block_size')::NUMERIC) AS bs,
                                                CASE WHEN SUBSTRING(v,12,3) IN ('8.0','8.1','8.2') THEN 27 ELSE 23 END AS hdr,
                                                CASE WHEN v ~ 'mingw32' THEN 8 ELSE 4 END AS ma
                                            FROM (SELECT version() AS v) AS foo
                                        ) AS constants
                                        WHERE schemaname = 'public' AND tablename = %s
                                        GROUP BY 1,2,3,4,5
                                    ) AS foo
                                ) AS rs
                                JOIN pg_class cc ON cc.relname = rs.tablename
                                JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
                            ) AS sml
                            WHERE sml.relpages > 0
                        """), (table_name,))
                        
                        bloat_row = bloat_result.fetchone()
                        if bloat_row and bloat_row.tbloat > 2.0:  # More than 2x bloated
                            await conn.execute(text(f"REINDEX TABLE {table_name}"))
                            results["reindexed_tables"].append(table_name)
                        
                    except Exception as e:
                        error_msg = f"Failed to vacuum/reindex {table_name}: {e}"
                        results["errors"].append(error_msg)
                        logger.warning(error_msg)
            
            logger.info(f"Vacuum/reindex completed: {len(results['vacuumed_tables'])} vacuumed, "
                       f"{len(results['reindexed_tables'])} reindexed")
            
        except Exception as e:
            logger.error(f"Vacuum/reindex operation failed: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def get_database_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive database health metrics."""
        try:
            async with self.engine.begin() as conn:
                # Database size and growth
                size_result = await conn.execute(text("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as current_size,
                        pg_database_size(current_database()) as size_bytes
                """))
                size_info = dict(size_result.fetchone())
                
                # Connection statistics
                conn_result = await conn.execute(text("""
                    SELECT 
                        state,
                        COUNT(*) as count,
                        AVG(EXTRACT(EPOCH FROM (now() - state_change))) as avg_duration_seconds
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                    GROUP BY state
                """))
                conn_stats = [dict(row) for row in conn_result.fetchall()]
                
                # Lock statistics
                lock_result = await conn.execute(text("""
                    SELECT 
                        mode,
                        COUNT(*) as count
                    FROM pg_locks
                    WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
                    GROUP BY mode
                """))
                lock_stats = [dict(row) for row in lock_result.fetchall()]
                
                # Cache hit ratio
                cache_result = await conn.execute(text("""
                    SELECT 
                        ROUND(
                            100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2
                        ) as cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """))
                cache_hit_ratio = cache_result.scalar()
                
                # Transaction statistics
                txn_result = await conn.execute(text("""
                    SELECT 
                        xact_commit,
                        xact_rollback,
                        ROUND(100.0 * xact_rollback / (xact_commit + xact_rollback), 2) as rollback_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """))
                txn_stats = dict(txn_result.fetchone())
                
                return {
                    "database_size": size_info,
                    "connections": conn_stats,
                    "locks": lock_stats,
                    "cache_hit_ratio": float(cache_hit_ratio) if cache_hit_ratio else 0.0,
                    "transactions": txn_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get database health metrics: {e}")
            return {"error": str(e)}
    
    async def monitor_query_performance(self, query: str, params: Optional[Tuple] = None) -> float:
        """Monitor and log query performance."""
        start_time = time.time()
        
        try:
            async with self.db.begin() as conn:
                if params:
                    await conn.execute(text(query), params)
                else:
                    await conn.execute(text(query))
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log slow queries
            if execution_time > self.slow_query_threshold_ms:
                logger.warning(f"Slow query detected: {execution_time:.2f}ms - {query[:100]}...")
            
            # Track query statistics
            query_hash = str(hash(query))
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = []
            
            self.query_stats[query_hash].append(execution_time)
            
            # Keep only recent history
            if len(self.query_stats[query_hash]) > self.query_history_size:
                self.query_stats[query_hash] = self.query_stats[query_hash][-self.query_history_size:]
            
            return execution_time
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query failed after {execution_time:.2f}ms: {e}")
            raise
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive database optimization report."""
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "database_health": await self.get_database_health_metrics(),
                "connection_pool": await self.optimize_connection_pool(),
                "query_performance": {},
                "index_recommendations": await self._generate_index_recommendations(),
                "optimization_history": self.optimization_history[-10:],  # Last 10 optimizations
                "recommendations": []
            }
            
            # Query performance summary
            if self.query_stats:
                total_queries = sum(len(times) for times in self.query_stats.values())
                avg_query_time = sum(sum(times) for times in self.query_stats.values()) / total_queries if total_queries > 0 else 0
                slow_queries = sum(1 for times in self.query_stats.values() for time in times if time > self.slow_query_threshold_ms)
                
                report["query_performance"] = {
                    "total_tracked_queries": total_queries,
                    "average_query_time_ms": round(avg_query_time, 2),
                    "slow_queries_count": slow_queries,
                    "slow_query_percentage": round(100.0 * slow_queries / total_queries, 2) if total_queries > 0 else 0
                }
            
            # Generate high-level recommendations
            health_metrics = report["database_health"]
            
            if health_metrics.get("cache_hit_ratio", 0) < 90:
                report["recommendations"].append("Low cache hit ratio - consider increasing shared_buffers or adding indexes")
            
            if report["query_performance"].get("slow_query_percentage", 0) > 5:
                report["recommendations"].append("High percentage of slow queries - review query patterns and indexes")
            
            conn_stats = health_metrics.get("connections", [])
            total_connections = sum(stat.get("count", 0) for stat in conn_stats)
            if total_connections > 50:
                report["recommendations"].append("High connection count - consider connection pooling optimization")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate optimization report: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old data from time-series tables."""
        cleanup_results = {}
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # Tables and their timestamp columns for cleanup
            cleanup_tables = [
                ("sentiment_analyses", "processing_timestamp"),
                ("benchmark_results", "calculated_at"),
                ("ml_performance_metrics", "evaluation_timestamp"),
                ("metrics_snapshots", "snapshot_timestamp"),
                ("trend_analyses", "analyzed_at")
            ]
            
            async with self.engine.begin() as conn:
                for table_name, timestamp_column in cleanup_tables:
                    try:
                        # Count records to be deleted
                        count_result = await conn.execute(text(f"""
                            SELECT COUNT(*) 
                            FROM {table_name} 
                            WHERE {timestamp_column} < %s
                        """), (cutoff_date,))
                        
                        records_to_delete = count_result.scalar()
                        
                        if records_to_delete > 0:
                            # Delete old records
                            delete_result = await conn.execute(text(f"""
                                DELETE FROM {table_name} 
                                WHERE {timestamp_column} < %s
                            """), (cutoff_date,))
                            
                            cleanup_results[table_name] = records_to_delete
                            logger.info(f"Cleaned up {records_to_delete} old records from {table_name}")
                        else:
                            cleanup_results[table_name] = 0
                            
                    except Exception as e:
                        logger.error(f"Failed to cleanup {table_name}: {e}")
                        cleanup_results[table_name] = -1
            
            total_cleaned = sum(count for count in cleanup_results.values() if count > 0)
            logger.info(f"Data cleanup completed: {total_cleaned} total records removed")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            cleanup_results["error"] = str(e)
        
        return cleanup_results
    
    async def shutdown(self) -> None:
        """Shutdown the database optimizer."""
        try:
            if self.engine:
                await self.engine.dispose()
            
            logger.info("Database optimizer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during database optimizer shutdown: {e}")