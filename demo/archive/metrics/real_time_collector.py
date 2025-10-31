"""Real-time metrics collection for demo system."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil

from src.utils.logging import get_logger


logger = get_logger("demo.metrics")


class MetricsCollector:
    """
    Real-time metrics collector for demo scenarios.

    Collects:
    - Performance metrics (latency, throughput)
    - Resource utilization (CPU, memory)
    - Agent execution metrics
    - Business impact metrics
    """

    def __init__(self):
        self._collecting = False
        self._start_time: Optional[float] = None
        self._scenario_name: Optional[str] = None
        self._metrics: Dict[str, Any] = {}
        self._samples: List[Dict[str, Any]] = []

    def start_collection(self, scenario_name: str) -> None:
        """Start collecting metrics for a scenario."""
        self._collecting = True
        self._start_time = time.time()
        self._scenario_name = scenario_name
        self._metrics = {
            "scenario": scenario_name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "samples": [],
        }
        self._samples = []
        logger.info(f"Started metrics collection for scenario: {scenario_name}")

    def stop_collection(self) -> Dict[str, Any]:
        """Stop collecting metrics and return results."""
        if not self._collecting:
            logger.warning("Attempted to stop collection when not collecting")
            return {}

        self._collecting = False
        end_time = time.time()
        duration = end_time - self._start_time if self._start_time else 0

        # Collect final system metrics
        final_metrics = self._collect_system_metrics()

        # Calculate aggregate metrics
        aggregated = self._aggregate_samples()

        result = {
            "scenario": self._scenario_name,
            "start_time": self._metrics.get("start_time"),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "samples_collected": len(self._samples),
            "system_metrics": final_metrics,
            "aggregated": aggregated,
        }

        logger.info(
            f"Stopped metrics collection for scenario: {self._scenario_name}",
            extra={"duration_seconds": duration, "samples": len(self._samples)},
        )

        # Reset state
        self._metrics = {}
        self._samples = []
        self._start_time = None
        self._scenario_name = None

        return result

    def record_sample(self, metrics: Dict[str, Any]) -> None:
        """Record a metrics sample during collection."""
        if not self._collecting:
            return

        sample = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.time() - self._start_time if self._start_time else 0,
            **metrics,
        }
        self._samples.append(sample)

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "memory_available_mb": round(memory.available / (1024 * 1024), 2),
                "disk_percent": round(disk.percent, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return {"error": str(e)}

    def _aggregate_samples(self) -> Dict[str, Any]:
        """Aggregate metrics from collected samples."""
        if not self._samples:
            return {}

        # Extract numeric metrics
        numeric_keys = set()
        for sample in self._samples:
            for key, value in sample.items():
                if isinstance(value, (int, float)) and key != "elapsed_seconds":
                    numeric_keys.add(key)

        aggregated = {}
        for key in numeric_keys:
            values = [s[key] for s in self._samples if key in s and isinstance(s[key], (int, float))]
            if values:
                aggregated[key] = {
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "count": len(values),
                }

        return aggregated

    @property
    def is_collecting(self) -> bool:
        """Check if currently collecting metrics."""
        return self._collecting


class PerformanceTracker:
    """Tracks performance metrics for incident processing."""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "detection_latency_ms": [],
            "diagnosis_latency_ms": [],
            "prediction_latency_ms": [],
            "consensus_latency_ms": [],
            "resolution_latency_ms": [],
            "communication_latency_ms": [],
            "total_processing_time_ms": [],
        }

    def record_phase_latency(self, phase: str, latency_ms: float) -> None:
        """Record latency for a specific phase."""
        key = f"{phase}_latency_ms"
        if key in self.metrics:
            self.metrics[key].append(latency_ms)
        else:
            logger.warning(f"Unknown phase: {phase}")

    def record_total_time(self, time_ms: float) -> None:
        """Record total processing time."""
        self.metrics["total_processing_time_ms"].append(time_ms)

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics."""
        summary = {}
        for key, values in self.metrics.items():
            if values:
                summary[key] = {
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "p50": round(self._percentile(values, 0.5), 2),
                    "p95": round(self._percentile(values, 0.95), 2),
                    "p99": round(self._percentile(values, 0.99), 2),
                    "count": len(values),
                }
        return summary

    @staticmethod
    def _percentile(values: List[float], p: float) -> float:
        """Calculate percentile."""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def reset(self) -> None:
        """Reset all metrics."""
        for key in self.metrics:
            self.metrics[key] = []
