"""
Performance and Production Readiness API Endpoints

API endpoints for monitoring, optimization, and production readiness features.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.services.ml_performance_optimizer import MLPerformanceOptimizer, OptimizationLevel
from app.services.advanced_cache_manager import AdvancedCacheManager, CacheType
from app.services.production_monitor import ProductionMonitor, ComponentType
from app.services.database_optimizer import DatabaseOptimizer
from app.services.security_manager import SecurityManager
from app.models.user import User
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/health")
async def get_system_health(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive system health status."""
    try:
        # Initialize production monitor
        monitor = ProductionMonitor(db)
        await monitor.initialize()
        
        # Get health status
        health_status = await monitor.get_health_status()
        
        return {
            "status": "success",
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/metrics")
async def get_performance_metrics(
    component: Optional[str] = None,
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for monitoring."""
    try:
        # Initialize production monitor
        monitor = ProductionMonitor(db)
        await monitor.initialize()
        
        # Convert component string to enum if provided
        component_type = None
        if component:
            try:
                component_type = ComponentType(component)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid component type: {component}"
                )
        
        # Get metrics
        metrics = await monitor.get_metrics(component_type, hours=hours)
        
        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "component": component,
                "timeframe_hours": hours
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}"
        )

@router.post("/ml/optimize")
async def optimize_ml_models(
    model_version: str,
    model_type: str,
    optimization_level: str = "basic",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimize ML models for better performance."""
    try:
        # Validate optimization level
        try:
            opt_level = OptimizationLevel(optimization_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid optimization level: {optimization_level}"
            )
        
        # Validate model type
        from app.services.ml_training_service import ModelType
        try:
            model_type_enum = ModelType(model_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model type: {model_type}"
            )
        
        # Initialize optimizer
        optimizer = MLPerformanceOptimizer(db)
        await optimizer.initialize()
        
        # Optimize model
        optimization_results = await optimizer.optimize_model(
            model_version=model_version,
            model_type=model_type_enum,
            optimization_level=opt_level
        )
        
        return {
            "status": "success",
            "data": optimization_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML optimization failed: {str(e)}"
        )

@router.get("/ml/performance")
async def get_ml_performance_metrics(
    prediction_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ML performance metrics."""
    try:
        # Initialize optimizer
        optimizer = MLPerformanceOptimizer(db)
        await optimizer.initialize()
        
        # Get performance metrics
        metrics = await optimizer.get_performance_metrics(prediction_type)
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"ML performance metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML performance metrics retrieval failed: {str(e)}"
        )

@router.get("/cache/stats")
async def get_cache_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cache statistics and performance metrics."""
    try:
        # Initialize cache manager
        cache_manager = AdvancedCacheManager(db)
        await cache_manager.initialize()
        
        # Get cache statistics
        stats = await cache_manager.get_cache_statistics()
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Cache statistics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache statistics retrieval failed: {str(e)}"
        )

@router.post("/cache/invalidate")
async def invalidate_cache(
    cache_type: str,
    pattern: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invalidate cache entries."""
    try:
        # Validate cache type
        try:
            cache_type_enum = CacheType(cache_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cache type: {cache_type}"
            )
        
        # Initialize cache manager
        cache_manager = AdvancedCacheManager(db)
        await cache_manager.initialize()
        
        # Invalidate cache
        invalidated_count = await cache_manager.invalidate_cache(cache_type_enum, pattern)
        
        return {
            "status": "success",
            "data": {
                "cache_type": cache_type,
                "pattern": pattern,
                "invalidated_count": invalidated_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache invalidation failed: {str(e)}"
        )

@router.post("/database/optimize")
async def optimize_database(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run database optimization and analysis."""
    try:
        # Initialize database optimizer
        optimizer = DatabaseOptimizer(db)
        await optimizer.initialize()
        
        # Run optimization
        optimization_results = await optimizer.analyze_and_optimize()
        
        return {
            "status": "success",
            "data": optimization_results
        }
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database optimization failed: {str(e)}"
        )

@router.get("/database/health")
async def get_database_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get database health metrics."""
    try:
        # Initialize database optimizer
        optimizer = DatabaseOptimizer(db)
        await optimizer.initialize()
        
        # Get health metrics
        health_metrics = await optimizer.get_database_health_metrics()
        
        return {
            "status": "success",
            "data": health_metrics
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database health check failed: {str(e)}"
        )

@router.post("/database/vacuum")
async def vacuum_database(
    table_names: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run VACUUM and REINDEX operations on database tables."""
    try:
        # Initialize database optimizer
        optimizer = DatabaseOptimizer(db)
        await optimizer.initialize()
        
        # Run vacuum and reindex
        results = await optimizer.vacuum_and_reindex(table_names)
        
        return {
            "status": "success",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Database vacuum failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database vacuum failed: {str(e)}"
        )

@router.get("/security/metrics")
async def get_security_metrics(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get security metrics and statistics."""
    try:
        # Initialize security manager
        security_manager = SecurityManager(db)
        await security_manager.initialize()
        
        # Get security metrics
        metrics = await security_manager.get_security_metrics()
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Security metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security metrics retrieval failed: {str(e)}"
        )

@router.post("/security/audit")
async def run_security_audit(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run comprehensive security audit."""
    try:
        # Initialize security manager
        security_manager = SecurityManager(db)
        await security_manager.initialize()
        
        # Run security audit
        audit_report = await security_manager.run_security_audit()
        
        return {
            "status": "success",
            "data": audit_report
        }
        
    except Exception as e:
        logger.error(f"Security audit failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security audit failed: {str(e)}"
        )

@router.get("/alerts")
async def get_alerts(
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system alerts."""
    try:
        # Initialize production monitor
        monitor = ProductionMonitor(db)
        await monitor.initialize()
        
        # Get alerts
        alerts = await monitor.get_alerts(include_resolved)
        
        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "include_resolved": include_resolved
            }
        }
        
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alerts retrieval failed: {str(e)}"
        )

@router.get("/report")
async def get_optimization_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive optimization and performance report."""
    try:
        # Initialize services
        monitor = ProductionMonitor(db)
        await monitor.initialize()
        
        cache_manager = AdvancedCacheManager(db)
        await cache_manager.initialize()
        
        db_optimizer = DatabaseOptimizer(db)
        await db_optimizer.initialize()
        
        ml_optimizer = MLPerformanceOptimizer(db)
        await ml_optimizer.initialize()
        
        security_manager = SecurityManager(db)
        await security_manager.initialize()
        
        # Gather comprehensive report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "system_health": await monitor.get_health_status(),
            "cache_statistics": await cache_manager.get_cache_statistics(),
            "database_optimization": await db_optimizer.get_optimization_report(),
            "ml_performance": await ml_optimizer.get_performance_metrics(),
            "security_metrics": await security_manager.get_security_metrics(),
            "alerts": await monitor.get_alerts(include_resolved=False)
        }
        
        return {
            "status": "success",
            "data": report
        }
        
    except Exception as e:
        logger.error(f"Optimization report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization report generation failed: {str(e)}"
        )