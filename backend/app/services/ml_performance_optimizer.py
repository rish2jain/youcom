"""
ML Performance Optimizer Service

This service provides model inference optimization, quantization, compression,
and batch processing capabilities to meet <500ms response time targets.
"""

import asyncio
import logging
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import queue

import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler
import onnx
import onnxruntime as ort
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.ml_training import TrainingJob, ModelPerformanceMetric
from app.services.ml_prediction_service import PredictionRequest, PredictionResult, PredictionType, ModelInfo
from app.services.ml_training_service import ModelType
from app.config import settings

logger = logging.getLogger(__name__)

class OptimizationLevel(str, Enum):
    """Levels of model optimization."""
    NONE = "none"
    BASIC = "basic"
    AGGRESSIVE = "aggressive"
    ULTRA = "ultra"

class CompressionMethod(str, Enum):
    """Model compression methods."""
    QUANTIZATION = "quantization"
    PRUNING = "pruning"
    DISTILLATION = "distillation"
    ONNX_CONVERSION = "onnx_conversion"

@dataclass
class OptimizationConfig:
    """Configuration for model optimization."""
    level: OptimizationLevel
    target_latency_ms: float
    max_memory_mb: float
    compression_methods: List[CompressionMethod]
    batch_size: int
    enable_caching: bool
    cache_ttl_seconds: int

@dataclass
class PerformanceMetrics:
    """Performance metrics for model inference."""
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_qps: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float

@dataclass
class BatchRequest:
    """Batch prediction request."""
    requests: List[PredictionRequest]
    batch_id: str
    priority: int
    submitted_at: datetime

class MLPerformanceOptimizer:
    """Service for optimizing ML model inference performance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_storage_path = os.path.join(settings.data_dir, "ml_models")
        self.optimized_models_path = os.path.join(settings.data_dir, "ml_models_optimized")
        
        # Ensure optimized models directory exists
        os.makedirs(self.optimized_models_path, exist_ok=True)
        
        # Performance monitoring
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.latency_history: Dict[str, List[float]] = {}
        self.max_history_size = 1000
        
        # Batch processing
        self.batch_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.batch_processor_running = False
        self.batch_size = 32
        self.batch_timeout_ms = 100
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Model cache for optimized models
        self.optimized_model_cache: Dict[str, Any] = {}
        self.cache_ttl = timedelta(hours=2)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # ONNX runtime sessions
        self.onnx_sessions: Dict[str, ort.InferenceSession] = {}
        
        # Default optimization configs
        self.optimization_configs = {
            OptimizationLevel.BASIC: OptimizationConfig(
                level=OptimizationLevel.BASIC,
                target_latency_ms=500.0,
                max_memory_mb=512.0,
                compression_methods=[CompressionMethod.QUANTIZATION],
                batch_size=16,
                enable_caching=True,
                cache_ttl_seconds=3600
            ),
            OptimizationLevel.AGGRESSIVE: OptimizationConfig(
                level=OptimizationLevel.AGGRESSIVE,
                target_latency_ms=200.0,
                max_memory_mb=256.0,
                compression_methods=[CompressionMethod.QUANTIZATION, CompressionMethod.ONNX_CONVERSION],
                batch_size=32,
                enable_caching=True,
                cache_ttl_seconds=7200
            ),
            OptimizationLevel.ULTRA: OptimizationConfig(
                level=OptimizationLevel.ULTRA,
                target_latency_ms=100.0,
                max_memory_mb=128.0,
                compression_methods=[CompressionMethod.QUANTIZATION, CompressionMethod.PRUNING, CompressionMethod.ONNX_CONVERSION],
                batch_size=64,
                enable_caching=True,
                cache_ttl_seconds=14400
            )
        }
    
    async def optimize_model(
        self,
        model_version: str,
        model_type: ModelType,
        optimization_level: OptimizationLevel = OptimizationLevel.BASIC
    ) -> Dict[str, Any]:
        """Optimize a model for better inference performance."""
        try:
            config = self.optimization_configs[optimization_level]
            
            # Load original model
            model_path = os.path.join(self.model_storage_path, f"{model_version}.joblib")
            scaler_path = os.path.join(self.model_storage_path, f"{model_version}_scaler.joblib")
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                raise FileNotFoundError(f"Model files not found for version {model_version}")
            
            original_model = await asyncio.to_thread(joblib.load, model_path)
            scaler = await asyncio.to_thread(joblib.load, scaler_path)
            
            # Benchmark original model
            original_metrics = await self._benchmark_model(original_model, scaler, model_version)
            
            optimized_model = original_model
            optimization_results = {
                "original_metrics": original_metrics,
                "optimizations_applied": [],
                "final_metrics": None,
                "compression_ratio": 1.0,
                "speedup_factor": 1.0
            }
            
            # Apply optimizations
            for method in config.compression_methods:
                if method == CompressionMethod.QUANTIZATION:
                    optimized_model = await self._apply_quantization(optimized_model, model_type)
                    optimization_results["optimizations_applied"].append("quantization")
                
                elif method == CompressionMethod.PRUNING:
                    optimized_model = await self._apply_pruning(optimized_model, model_type)
                    optimization_results["optimizations_applied"].append("pruning")
                
                elif method == CompressionMethod.ONNX_CONVERSION:
                    onnx_path = await self._convert_to_onnx(optimized_model, scaler, model_version)
                    if onnx_path:
                        optimization_results["optimizations_applied"].append("onnx_conversion")
                        optimization_results["onnx_path"] = onnx_path
            
            # Save optimized model
            optimized_path = os.path.join(
                self.optimized_models_path, 
                f"{model_version}_optimized_{optimization_level.value}.joblib"
            )
            await asyncio.to_thread(joblib.dump, optimized_model, optimized_path)
            
            # Benchmark optimized model
            final_metrics = await self._benchmark_model(optimized_model, scaler, f"{model_version}_optimized")
            optimization_results["final_metrics"] = final_metrics
            
            # Calculate improvements
            if original_metrics["avg_latency_ms"] > 0:
                optimization_results["speedup_factor"] = (
                    original_metrics["avg_latency_ms"] / final_metrics["avg_latency_ms"]
                )
            
            optimization_results["compression_ratio"] = (
                original_metrics["memory_usage_mb"] / final_metrics["memory_usage_mb"]
                if final_metrics["memory_usage_mb"] > 0 else 1.0
            )
            
            logger.info(f"Optimized model {model_version} with {optimization_level.value} level")
            logger.info(f"Speedup: {optimization_results['speedup_factor']:.2f}x, "
                       f"Compression: {optimization_results['compression_ratio']:.2f}x")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Failed to optimize model {model_version}: {e}")
            raise
    
    async def _apply_quantization(self, model: BaseEstimator, model_type: ModelType) -> BaseEstimator:
        """Apply quantization to reduce model size and improve inference speed."""
        try:
            # For tree-based models, we can reduce precision of thresholds
            if isinstance(model, (DecisionTreeClassifier, RandomForestClassifier)):
                # Create a copy to avoid modifying original
                quantized_model = joblib.loads(await asyncio.to_thread(joblib.dumps, model))
                
                # Quantize decision thresholds (simplified approach)
                if hasattr(quantized_model, 'tree_'):
                    # Single tree
                    tree = quantized_model.tree_
                    if hasattr(tree, 'threshold'):
                        tree.threshold = np.round(tree.threshold, decimals=4).astype(np.float32)
                
                elif hasattr(quantized_model, 'estimators_'):
                    # Ensemble of trees
                    for estimator in quantized_model.estimators_:
                        if hasattr(estimator, 'tree_'):
                            tree = estimator.tree_
                            if hasattr(tree, 'threshold'):
                                tree.threshold = np.round(tree.threshold, decimals=4).astype(np.float32)
                
                return quantized_model
            
            # For other models, return as-is (could implement more sophisticated quantization)
            return model
            
        except Exception as e:
            logger.warning(f"Quantization failed: {e}")
            return model
    
    async def _apply_pruning(self, model: BaseEstimator, model_type: ModelType) -> BaseEstimator:
        """Apply pruning to reduce model complexity."""
        try:
            # For tree-based models, we can prune small branches
            if isinstance(model, RandomForestClassifier):
                # Create a copy
                pruned_model = joblib.loads(await asyncio.to_thread(joblib.dumps, model))
                
                # Keep only the most important trees (simplified pruning)
                if hasattr(pruned_model, 'estimators_') and len(pruned_model.estimators_) > 10:
                    # Keep top 80% of trees (simple heuristic)
                    n_keep = max(10, int(len(pruned_model.estimators_) * 0.8))
                    pruned_model.estimators_ = pruned_model.estimators_[:n_keep]
                    pruned_model.n_estimators = n_keep
                
                return pruned_model
            
            return model
            
        except Exception as e:
            logger.warning(f"Pruning failed: {e}")
            return model
    
    async def _convert_to_onnx(
        self, 
        model: BaseEstimator, 
        scaler: StandardScaler, 
        model_version: str
    ) -> Optional[str]:
        """Convert model to ONNX format for optimized inference."""
        try:
            # This is a simplified implementation
            # In practice, you'd use skl2onnx or similar libraries
            
            onnx_path = os.path.join(
                self.optimized_models_path,
                f"{model_version}_model.onnx"
            )
            
            # For now, just return None as ONNX conversion requires additional dependencies
            # In production, implement proper ONNX conversion:
            # from skl2onnx import convert_sklearn
            # from skl2onnx.common.data_types import FloatTensorType
            # 
            # initial_type = [('float_input', FloatTensorType([None, n_features]))]
            # onnx_model = convert_sklearn(model, initial_types=initial_type)
            # 
            # with open(onnx_path, "wb") as f:
            #     f.write(onnx_model.SerializeToString())
            
            logger.info(f"ONNX conversion skipped for {model_version} (requires additional dependencies)")
            return None
            
        except Exception as e:
            logger.warning(f"ONNX conversion failed: {e}")
            return None
    
    async def _benchmark_model(
        self, 
        model: BaseEstimator, 
        scaler: StandardScaler, 
        model_id: str,
        n_samples: int = 1000
    ) -> Dict[str, float]:
        """Benchmark model performance."""
        try:
            # Infer feature count from model
            n_features = None
            
            # Try different ways to get feature count
            if hasattr(model, 'n_features_in_'):
                n_features = model.n_features_in_
            elif hasattr(model, 'coef_') and hasattr(model.coef_, 'shape'):
                n_features = model.coef_.shape[1] if len(model.coef_.shape) > 1 else model.coef_.shape[0]
            elif hasattr(model, 'input_shape') and model.input_shape:
                # For Keras/TensorFlow models
                input_shape = model.input_shape
                if isinstance(input_shape, tuple) and len(input_shape) > 1:
                    n_features = input_shape[1]
                elif isinstance(input_shape, int):
                    n_features = input_shape
            elif hasattr(model, 'named_parameters'):
                # For PyTorch models, check first layer
                try:
                    first_layer = next(iter(model.named_parameters()))[1]
                    if hasattr(first_layer, 'in_features'):
                        n_features = first_layer.in_features
                    elif len(first_layer.shape) > 1:
                        n_features = first_layer.shape[1]
                except (StopIteration, AttributeError):
                    pass
            
            # Handle wrapped pipelines by checking the final estimator
            if n_features is None and hasattr(model, 'steps'):
                # For sklearn pipelines
                final_estimator = model.steps[-1][1]
                if hasattr(final_estimator, 'n_features_in_'):
                    n_features = final_estimator.n_features_in_
                elif hasattr(final_estimator, 'coef_') and hasattr(final_estimator.coef_, 'shape'):
                    n_features = final_estimator.coef_.shape[1] if len(final_estimator.coef_.shape) > 1 else final_estimator.coef_.shape[0]
            
            # Fallback to default if we can't determine feature count
            if n_features is None:
                logger.warning(f"Could not determine feature count for model {model_id}, using default of 20")
                n_features = 20
            
            # Generate synthetic test data
            X_test = np.random.randn(n_samples, n_features)
            X_test_scaled = scaler.transform(X_test)
            
            # Warm up
            for _ in range(10):
                _ = model.predict(X_test_scaled[:1])
            
            # Measure latency
            latencies = []
            start_time = time.time()
            
            for i in range(n_samples):
                sample_start = time.time()
                _ = model.predict(X_test_scaled[i:i+1])
                sample_end = time.time()
                latencies.append((sample_end - sample_start) * 1000)  # Convert to ms
            
            total_time = time.time() - start_time
            
            # Calculate metrics
            latencies = np.array(latencies)
            avg_latency = np.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            p99_latency = np.percentile(latencies, 99)
            throughput = n_samples / total_time
            
            # Estimate memory usage (simplified)
            model_size_mb = len(await asyncio.to_thread(joblib.dumps, model)) / (1024 * 1024)
            
            metrics = {
                "avg_latency_ms": float(avg_latency),
                "p95_latency_ms": float(p95_latency),
                "p99_latency_ms": float(p99_latency),
                "throughput_qps": float(throughput),
                "memory_usage_mb": float(model_size_mb),
                "cpu_usage_percent": 0.0,  # Would need system monitoring
                "cache_hit_rate": 0.0
            }
            
            # Store metrics
            self.performance_metrics[model_id] = PerformanceMetrics(**metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Benchmarking failed for {model_id}: {e}")
            return {
                "avg_latency_ms": 1000.0,
                "p95_latency_ms": 1500.0,
                "p99_latency_ms": 2000.0,
                "throughput_qps": 1.0,
                "memory_usage_mb": 100.0,
                "cpu_usage_percent": 0.0,
                "cache_hit_rate": 0.0
            }
    
    async def predict_optimized(
        self, 
        request: PredictionRequest,
        use_optimized: bool = True
    ) -> PredictionResult:
        """Make prediction using optimized model if available."""
        start_time = time.time()
        
        try:
            # Check for optimized model
            if use_optimized:
                optimized_result = await self._try_optimized_prediction(request)
                if optimized_result:
                    return optimized_result
            
            # Fall back to regular prediction
            from app.services.ml_prediction_service import MLPredictionService
            prediction_service = MLPredictionService(self.db)
            result = await prediction_service.predict(request)
            
            # Record latency
            latency_ms = (time.time() - start_time) * 1000
            self._record_latency(request.prediction_type.value, latency_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Optimized prediction failed: {e}")
            raise
    
    async def _try_optimized_prediction(self, request: PredictionRequest) -> Optional[PredictionResult]:
        """Try to make prediction using optimized model."""
        try:
            # Look for optimized model
            model_type = self._get_model_type_for_prediction(request.prediction_type)
            
            # Get latest model version
            result = await self.db.execute(
                select(TrainingJob.new_model_version)
                .where(TrainingJob.model_type == model_type.value)
                .where(TrainingJob.status == "completed")
                .order_by(desc(TrainingJob.completed_at))
                .limit(1)
            )
            
            model_version = result.scalar_one_or_none()
            if not model_version:
                return None
            
            # Check for optimized model file
            optimized_path = os.path.join(
                self.optimized_models_path,
                f"{model_version}_optimized_basic.joblib"
            )
            
            if not os.path.exists(optimized_path):
                return None
            
            # Load optimized model (with caching)
            cache_key = f"{model_version}_optimized"
            optimized_model = await self._get_cached_model(cache_key, optimized_path)
            
            if not optimized_model:
                return None
            
            # Load scaler
            scaler_path = os.path.join(self.model_storage_path, f"{model_version}_scaler.joblib")
            if not os.path.exists(scaler_path):
                return None
            
            scaler = await asyncio.to_thread(joblib.load, scaler_path)
            
            # Extract features and make prediction
            # (This would use the same feature extraction logic as the regular prediction service)
            # For now, return None to indicate optimized prediction not available
            return None
            
        except Exception as e:
            logger.warning(f"Optimized prediction attempt failed: {e}")
            return None
    
    def _get_model_type_for_prediction(self, prediction_type: PredictionType) -> ModelType:
        """Map prediction type to model type."""
        mapping = {
            PredictionType.IMPACT_CLASSIFICATION: ModelType.IMPACT_CLASSIFIER,
            PredictionType.RISK_SCORING: ModelType.RISK_SCORER,
            PredictionType.CONFIDENCE_PREDICTION: ModelType.CONFIDENCE_PREDICTOR,
            PredictionType.RELEVANCE_CLASSIFICATION: ModelType.RELEVANCE_CLASSIFIER
        }
        model_type = mapping.get(prediction_type)
        if model_type is None:
            raise ValueError(f"Unsupported PredictionType: {prediction_type}")
        return model_type
    
    async def _get_cached_model(self, cache_key: str, model_path: str) -> Optional[BaseEstimator]:
        """Get model from cache or load and cache it."""
        # Check cache
        if cache_key in self.optimized_model_cache:
            cache_time = self.cache_timestamps.get(cache_key, datetime.min)
            if datetime.now(timezone.utc) - cache_time < self.cache_ttl:
                return self.optimized_model_cache[cache_key]
        
        # Load model
        try:
            model = await asyncio.to_thread(joblib.load, model_path)
            self.optimized_model_cache[cache_key] = model
            self.cache_timestamps[cache_key] = datetime.now(timezone.utc)
            return model
        except Exception as e:
            logger.error(f"Failed to load cached model {cache_key}: {e}")
            return None
    
    def _record_latency(self, prediction_type: str, latency_ms: float) -> None:
        """Record latency for performance monitoring."""
        if prediction_type not in self.latency_history:
            self.latency_history[prediction_type] = []
        
        history = self.latency_history[prediction_type]
        history.append(latency_ms)
        
        # Keep only recent history
        if len(history) > self.max_history_size:
            history.pop(0)
    
    async def start_batch_processor(self) -> None:
        """Start the batch processing service."""
        if self.batch_processor_running:
            return
        
        self.batch_processor_running = True
        asyncio.create_task(self._batch_processor_loop())
        logger.info("Started batch processor")
    
    async def stop_batch_processor(self) -> None:
        """Stop the batch processing service."""
        self.batch_processor_running = False
        logger.info("Stopped batch processor")
    
    async def _batch_processor_loop(self) -> None:
        """Main loop for batch processing."""
        while self.batch_processor_running:
            try:
                # Collect batch requests
                batch_requests = []
                deadline = time.time() + (self.batch_timeout_ms / 1000)
                
                while (len(batch_requests) < self.batch_size and 
                       time.time() < deadline and 
                       self.batch_processor_running):
                    
                    try:
                        # Get request with timeout
                        timeout = max(0.01, deadline - time.time())
                        priority, batch_request = self.batch_queue.get(timeout=timeout)
                        batch_requests.append(batch_request)
                    except queue.Empty:
                        break
                
                # Process batch if we have requests
                if batch_requests:
                    await self._process_batch(batch_requests)
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_batch(self, batch_requests: List[BatchRequest]) -> None:
        """Process a batch of prediction requests."""
        try:
            # Group requests by prediction type for efficiency
            grouped_requests = {}
            for batch_req in batch_requests:
                for req in batch_req.requests:
                    pred_type = req.prediction_type
                    if pred_type not in grouped_requests:
                        grouped_requests[pred_type] = []
                    grouped_requests[pred_type].append((batch_req.batch_id, req))
            
            # Process each group
            results = {}
            for pred_type, type_requests in grouped_requests.items():
                # Load model once for all requests of this type
                model_type = self._get_model_type_for_prediction(pred_type)
                
                # Process requests in parallel
                tasks = []
                for batch_id, request in type_requests:
                    task = asyncio.create_task(self.predict_optimized(request))
                    tasks.append((batch_id, task))
                
                # Wait for all tasks to complete concurrently
                task_list = [task for batch_id, task in tasks]
                batch_id_list = [batch_id for batch_id, task in tasks]
                
                gathered_results = await asyncio.gather(*task_list, return_exceptions=True)
                
                # Process results and handle exceptions
                for batch_id, result in zip(batch_id_list, gathered_results):
                    try:
                        if isinstance(result, Exception):
                            logger.error(f"Task failed for batch_id {batch_id}: {result}")
                            continue
                        
                        if batch_id not in results:
                            results[batch_id] = []
                        results[batch_id].append(result)
                    except Exception as e:
                        logger.error(f"Batch prediction failed for {batch_id}: {e}")
            
            logger.debug(f"Processed batch with {len(batch_requests)} requests")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
    
    async def submit_batch_request(
        self, 
        requests: List[PredictionRequest],
        priority: int = 1
    ) -> str:
        """Submit a batch of requests for processing."""
        batch_id = f"batch_{int(time.time() * 1000)}"
        
        batch_request = BatchRequest(
            requests=requests,
            batch_id=batch_id,
            priority=priority,
            submitted_at=datetime.now(timezone.utc)
        )
        
        # Add to queue (lower priority number = higher priority)
        self.batch_queue.put((priority, batch_request))
        
        return batch_id
    
    async def get_performance_metrics(self, prediction_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        if prediction_type and prediction_type in self.performance_metrics:
            return asdict(self.performance_metrics[prediction_type])
        
        # Return aggregated metrics
        all_metrics = {}
        for pred_type, metrics in self.performance_metrics.items():
            all_metrics[pred_type] = asdict(metrics)
        
        # Add latency statistics
        latency_stats = {}
        for pred_type, latencies in self.latency_history.items():
            if latencies:
                latency_stats[pred_type] = {
                    "count": len(latencies),
                    "avg_ms": np.mean(latencies),
                    "p95_ms": np.percentile(latencies, 95),
                    "p99_ms": np.percentile(latencies, 99),
                    "min_ms": np.min(latencies),
                    "max_ms": np.max(latencies)
                }
        
        return {
            "model_metrics": all_metrics,
            "latency_stats": latency_stats,
            "batch_queue_size": self.batch_queue.qsize(),
            "batch_processor_running": self.batch_processor_running,
            "cache_size": len(self.optimized_model_cache)
        }
    
    async def cleanup_cache(self) -> int:
        """Clean up expired cache entries."""
        expired_keys = []
        current_time = datetime.now(timezone.utc)
        
        for cache_key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            if key in self.optimized_model_cache:
                del self.optimized_model_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)