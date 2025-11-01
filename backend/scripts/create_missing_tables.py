"""
Script to create missing tables: notification_rules, notification_logs, and api_call_logs
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


async def create_missing_tables():
    """Create the missing tables directly"""
    
    async with engine.begin() as conn:
        # Create notification_rules table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_rules (
                id SERIAL PRIMARY KEY,
                competitor_name VARCHAR(255) NOT NULL,
                condition_type VARCHAR(50) NOT NULL,
                threshold_value FLOAT,
                channel VARCHAR(50) NOT NULL,
                target VARCHAR(255) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT true,
                last_triggered_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_notification_rules_id ON notification_rules(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_notification_rules_competitor_name ON notification_rules(competitor_name);
        """))
        
        # Create notification_logs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id SERIAL PRIMARY KEY,
                rule_id INTEGER,
                competitor_name VARCHAR(255) NOT NULL,
                message VARCHAR(1024) NOT NULL,
                channel VARCHAR(50) NOT NULL,
                target VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_notification_logs_id ON notification_logs(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_notification_logs_rule_id ON notification_logs(rule_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_notification_logs_created_at ON notification_logs(created_at);
        """))
        
        # Create api_call_logs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_call_logs (
                id SERIAL PRIMARY KEY,
                api_type VARCHAR(50) NOT NULL,
                endpoint VARCHAR(255) NOT NULL,
                status_code INTEGER,
                success BOOLEAN NOT NULL DEFAULT true,
                latency_ms FLOAT NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_api_call_logs_id ON api_call_logs(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_api_call_logs_api_type ON api_call_logs(api_type);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_api_call_logs_success ON api_call_logs(success);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_api_call_logs_created_at ON api_call_logs(created_at);
        """))
        
        # Create ml_performance_metrics table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ml_performance_metrics (
                id SERIAL PRIMARY KEY,
                model_version VARCHAR(100) NOT NULL,
                model_type VARCHAR(50) NOT NULL,
                metric_name VARCHAR(50) NOT NULL,
                metric_value FLOAT NOT NULL,
                evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                dataset_size INTEGER,
                evaluation_type VARCHAR(30),
                metric_metadata JSON
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ml_performance_metrics_id ON ml_performance_metrics(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ml_performance_metrics_model_version ON ml_performance_metrics(model_version);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ml_performance_metrics_model_type ON ml_performance_metrics(model_type);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ml_performance_metrics_metric_name ON ml_performance_metrics(metric_name);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_ml_performance_metrics_evaluation_timestamp ON ml_performance_metrics(evaluation_timestamp);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_performance_model_timestamp ON ml_performance_metrics(model_version, evaluation_timestamp);
        """))
        
        # Create benchmark_results table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS benchmark_results (
                id SERIAL PRIMARY KEY,
                metric_type VARCHAR NOT NULL,
                entity_name VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                metric_value FLOAT NOT NULL,
                percentile_rank FLOAT NOT NULL,
                industry_average FLOAT,
                industry_sector VARCHAR,
                comparison_group VARCHAR,
                calculated_at TIMESTAMP DEFAULT NOW(),
                calculation_method VARCHAR,
                confidence_score FLOAT,
                meta_data JSON,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_results_id ON benchmark_results(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_results_metric_type ON benchmark_results(metric_type);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_results_entity_name ON benchmark_results(entity_name);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_results_industry_sector ON benchmark_results(industry_sector);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_results_calculated_at ON benchmark_results(calculated_at);
        """))
        
        # Create benchmark_comparisons table (if it doesn't exist)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS benchmark_comparisons (
                id SERIAL PRIMARY KEY,
                comparison_id VARCHAR UNIQUE NOT NULL,
                entity_a_name VARCHAR NOT NULL,
                entity_b_name VARCHAR NOT NULL,
                comparison_type VARCHAR NOT NULL,
                metric_type VARCHAR NOT NULL,
                entity_a_value FLOAT NOT NULL,
                entity_b_value FLOAT NOT NULL,
                difference_absolute FLOAT,
                difference_percentage FLOAT,
                statistical_significance FLOAT,
                winner VARCHAR,
                compared_at TIMESTAMP DEFAULT NOW(),
                comparison_period_start TIMESTAMP,
                comparison_period_end TIMESTAMP,
                meta_data JSON,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_comparisons_id ON benchmark_comparisons(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_comparisons_comparison_id ON benchmark_comparisons(comparison_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_benchmark_comparisons_compared_at ON benchmark_comparisons(compared_at);
        """))
        
        # Create metrics_snapshots table (referenced in code)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id SERIAL PRIMARY KEY,
                snapshot_id VARCHAR UNIQUE NOT NULL,
                entity_name VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                snapshot_timestamp TIMESTAMP NOT NULL,
                metrics_data JSON NOT NULL,
                data_sources JSON,
                quality_score FLOAT,
                completeness_score FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_metrics_snapshots_id ON metrics_snapshots(id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_metrics_snapshots_snapshot_id ON metrics_snapshots(snapshot_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_metrics_snapshots_entity_name ON metrics_snapshots(entity_name);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_metrics_snapshots_snapshot_timestamp ON metrics_snapshots(snapshot_timestamp);
        """))
        
        print("✅ Successfully created missing tables: notification_rules, notification_logs, api_call_logs, ml_performance_metrics, benchmark_results, benchmark_comparisons, and metrics_snapshots")


if __name__ == "__main__":
    asyncio.run(create_missing_tables())

