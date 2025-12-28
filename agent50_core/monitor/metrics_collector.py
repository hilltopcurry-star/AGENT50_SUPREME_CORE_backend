"""
metrics_collector.py - Multi-layer metrics collection and analysis for Agent 50
Collects infrastructure, application, and business metrics with anomaly detection
"""

import asyncio
import time
import json
import statistics
import os
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque, defaultdict
import psutil
import aiohttp

# Import existing MemoryManager
from agent50_core.memory.memory_manager import MemoryManager


class MetricType(Enum):
    """Types of metrics collected"""
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    BUSINESS = "business"
    SYNTHETIC = "synthetic"


class MetricSource(Enum):
    """Sources of metrics"""
    DOCKER = "docker"
    PROMETHEUS = "prometheus"
    PLATFORM_API = "platform_api"
    HTTP_ENDPOINT = "http_endpoint"
    CUSTOM_CHECK = "custom_check"
    SYSTEM = "system"


@dataclass
class MetricDefinition:
    """Definition of a metric to collect"""
    name: str
    type: MetricType
    source: MetricSource
    collection_interval: int  # seconds
    retention_period: int  # seconds
    thresholds: Dict[str, float] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    transform_fn: Optional[Callable] = None


@dataclass
class MetricSample:
    """Single metric sample"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric samples"""
    definition: MetricDefinition
    samples: deque = field(default_factory=lambda: deque(maxlen=1000))
    baseline: Optional[Dict[str, float]] = None
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_sample(self, sample: MetricSample):
        """Add sample to series"""
        self.samples.append(sample)
    
    def get_recent(self, window_seconds: int = 300) -> List[MetricSample]:
        """Get recent samples within time window"""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        return [s for s in self.samples if s.timestamp >= cutoff]
    
    def calculate_statistics(self, window_seconds: int = 300) -> Dict[str, float]:
        """Calculate statistics for recent samples"""
        recent = self.get_recent(window_seconds)
        if not recent:
            return {}
        
        values = [s.value for s in recent]
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
            "count": len(values)
        }


class MetricsCollector:
    """
    Multi-layer metrics collection and analysis engine
    Collects infrastructure, application, and business metrics with anomaly detection
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.metrics_registry: Dict[str, MetricSeries] = {}
        self.collection_tasks = {}
        self.running = False
        self.lock = threading.Lock()
        self.session = None
        
        # Health monitor integration
        self.health_monitor = None
        
        # Anomaly detection configuration
        self.anomaly_config = {
            "z_score_threshold": 3.0,
            "moving_avg_window": 10,
            "min_samples_for_baseline": 50,
            "seasonality_periods": {
                "hourly": 3600,
                "daily": 86400,
                "weekly": 604800
            }
        }
        
        # Prometheus configuration
        self.prometheus_enabled = False
        self.prometheus_url = None
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def set_health_monitor(self, health_monitor):
        """Set reference to health monitor for integration"""
        self.health_monitor = health_monitor
    
    def _initialize_default_metrics(self):
        """Initialize default metrics for collection"""
        default_metrics = [
            # Infrastructure metrics
            MetricDefinition(
                name="cpu_percent",
                type=MetricType.INFRASTRUCTURE,
                source=MetricSource.SYSTEM,
                collection_interval=30,
                retention_period=3600,
                thresholds={"warning": 80, "critical": 95}
            ),
            MetricDefinition(
                name="memory_percent",
                type=MetricType.INFRASTRUCTURE,
                source=MetricSource.SYSTEM,
                collection_interval=30,
                retention_period=3600,
                thresholds={"warning": 85, "critical": 95}
            ),
            MetricDefinition(
                name="disk_usage_percent",
                type=MetricType.INFRASTRUCTURE,
                source=MetricSource.SYSTEM,
                collection_interval=60,
                retention_period=7200,
                thresholds={"warning": 80, "critical": 90}
            ),
            MetricDefinition(
                name="network_bytes_sent",
                type=MetricType.INFRASTRUCTURE,
                source=MetricSource.SYSTEM,
                collection_interval=30,
                retention_period=3600
            ),
            MetricDefinition(
                name="network_bytes_recv",
                type=MetricType.INFRASTRUCTURE,
                source=MetricSource.SYSTEM,
                collection_interval=30,
                retention_period=3600
            ),
            
            # Synthetic metrics (health checks)
            MetricDefinition(
                name="endpoint_response_time",
                type=MetricType.SYNTHETIC,
                source=MetricSource.HTTP_ENDPOINT,
                collection_interval=30,
                retention_period=1800,
                thresholds={"warning": 1000, "critical": 3000}  # milliseconds
            ),
            MetricDefinition(
                name="endpoint_availability",
                type=MetricType.SYNTHETIC,
                source=MetricSource.HTTP_ENDPOINT,
                collection_interval=30,
                retention_period=1800,
                thresholds={"warning": 0.99, "critical": 0.95}  # 99% availability
            )
        ]
        
        for metric_def in default_metrics:
            self.register_metric(metric_def)
    
    def configure_prometheus(self, url: Optional[str] = None):
        """Configure Prometheus integration"""
        if url:
            self.prometheus_url = url
            self.prometheus_enabled = True
            print(f"[Metrics] Prometheus enabled: {url}")
            
            # Register Prometheus-based metrics
            prom_metrics = [
                MetricDefinition(
                    name="http_request_duration_seconds",
                    type=MetricType.APPLICATION,
                    source=MetricSource.PROMETHEUS,
                    collection_interval=15,
                    retention_period=1800,
                    thresholds={"warning": 1.0, "critical": 3.0},
                    labels={"prometheus_url": url}
                ),
                MetricDefinition(
                    name="http_requests_total",
                    type=MetricType.APPLICATION,
                    source=MetricSource.PROMETHEUS,
                    collection_interval=15,
                    retention_period=1800,
                    labels={"prometheus_url": url}
                ),
                MetricDefinition(
                    name="database_query_duration_seconds",
                    type=MetricType.APPLICATION,
                    source=MetricSource.PROMETHEUS,
                    collection_interval=30,
                    retention_period=3600,
                    thresholds={"warning": 0.5, "critical": 2.0},
                    labels={"prometheus_url": url}
                ),
            ]
            
            for metric_def in prom_metrics:
                self.register_metric(metric_def)
        else:
            self.prometheus_enabled = False
            print("[Metrics] Prometheus disabled")
    
    def register_custom_metric(self, name: str, metric_type: MetricType, 
                             collection_fn: Callable, interval: int = 60,
                             thresholds: Optional[Dict[str, float]] = None):
        """Register a custom metric with collection function"""
        
        async def custom_collector_wrapper():
            """Wrapper for custom collection function"""
            try:
                if asyncio.iscoroutinefunction(collection_fn):
                    return await collection_fn()
                else:
                    return collection_fn()
            except Exception as e:
                print(f"[Metrics] Custom metric {name} failed: {e}")
                return None, {"error": str(e)}
        
        definition = MetricDefinition(
            name=name,
            type=metric_type,
            source=MetricSource.CUSTOM_CHECK,
            collection_interval=interval,
            retention_period=3600,
            thresholds=thresholds or {},
            transform_fn=lambda v, m: v  # Identity transform
        )
        
        # Store custom collector
        definition.custom_collector = custom_collector_wrapper
        
        self.register_metric(definition)
        return definition
    
    def register_business_metric(self, name: str, collection_fn: Callable, 
                                interval: int = 300, thresholds: Optional[Dict[str, float]] = None):
        """Register a business metric"""
        return self.register_custom_metric(
            name=name,
            metric_type=MetricType.BUSINESS,
            collection_fn=collection_fn,
            interval=interval,
            thresholds=thresholds
        )
    
    def register_metric(self, definition: MetricDefinition):
        """Register a new metric for collection"""
        with self.lock:
            if definition.name in self.metrics_registry:
                print(f"[Metrics] Metric already registered: {definition.name}")
                return
            
            series = MetricSeries(definition=definition)
            self.metrics_registry[definition.name] = series
            
            # Start collection task if collector is running
            if self.running:
                self._start_collection_task(definition)
            
            print(f"[Metrics] Registered metric: {definition.name} "
                  f"({definition.type.value}, every {definition.collection_interval}s)")
    
    def unregister_metric(self, metric_name: str):
        """Stop collecting a metric"""
        with self.lock:
            if metric_name in self.metrics_registry:
                # Stop collection task
                if metric_name in self.collection_tasks:
                    task = self.collection_tasks.pop(metric_name)
                    task.cancel()
                
                # Remove from registry
                del self.metrics_registry[metric_name]
                print(f"[Metrics] Unregistered metric: {metric_name}")
    
    async def start(self):
        """Start metrics collection"""
        if self.running:
            print("[Metrics] Collector already running")
            return
        
        print("[Metrics] Starting metrics collector...")
        self.running = True
        
        # Create aiohttp session for async HTTP requests
        self.session = aiohttp.ClientSession()
        
        # Start collection tasks for all registered metrics
        for metric_name, series in self.metrics_registry.items():
            self._start_collection_task(series.definition)
        
        # Start baseline calculation task
        asyncio.create_task(self._baseline_calculation_loop())
        
        # Start anomaly detection task
        asyncio.create_task(self._anomaly_detection_loop())
        
        print(f"[Metrics] Started collecting {len(self.metrics_registry)} metrics")
    
    async def stop(self):
        """Stop metrics collection"""
        if not self.running:
            return
        
        print("[Metrics] Stopping metrics collector...")
        self.running = False
        
        # Cancel all collection tasks
        for task_name, task in self.collection_tasks.items():
            task.cancel()
        self.collection_tasks.clear()
        
        # Close aiohttp session
        if self.session:
            await self.session.close()
        
        # Save current state to memory
        await self._save_state_to_memory()
        
        print("[Metrics] Metrics collector stopped")
    
    def _start_collection_task(self, definition: MetricDefinition):
        """Start collection task for a metric"""
        async def collection_loop():
            while self.running:
                try:
                    await self._collect_metric(definition)
                    await asyncio.sleep(definition.collection_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[Metrics] Error collecting {definition.name}: {e}")
                    await asyncio.sleep(min(60, definition.collection_interval * 2))
        
        task = asyncio.create_task(collection_loop())
        self.collection_tasks[definition.name] = task
    
    async def _collect_metric(self, definition: MetricDefinition):
        """Collect a single metric sample"""
        try:
            value = None
            metadata = {}
            
            if definition.source == MetricSource.SYSTEM:
                value, metadata = await self._collect_system_metric(definition)
            elif definition.source == MetricSource.HTTP_ENDPOINT:
                value, metadata = await self._collect_http_metric(definition)
            elif definition.source == MetricSource.PROMETHEUS:
                value, metadata = await self._collect_prometheus_metric(definition)
            elif definition.source == MetricSource.DOCKER:
                value, metadata = await self._collect_docker_metric(definition)
            elif definition.source == MetricSource.PLATFORM_API:
                value, metadata = await self._collect_platform_metric(definition)
            elif definition.source == MetricSource.CUSTOM_CHECK:
                value, metadata = await self._collect_custom_metric(definition)
            
            if value is not None:
                # Apply transform function if defined
                if definition.transform_fn:
                    value = definition.transform_fn(value, metadata)
                
                # Create sample
                sample = MetricSample(
                    timestamp=datetime.now(),
                    value=value,
                    labels=definition.labels.copy(),
                    metadata=metadata
                )
                
                # Add to series
                with self.lock:
                    series = self.metrics_registry.get(definition.name)
                    if series:
                        series.add_sample(sample)
                
                # Check thresholds
                await self._check_thresholds(definition, value, metadata)
                
                # Debug logging (reduced frequency)
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    print(f"[Metrics] Collected {definition.name}: {value}")
            
        except Exception as e:
            print(f"[Metrics] Failed to collect {definition.name}: {e}")
    
    async def _collect_system_metric(self, definition: MetricDefinition) -> Tuple[Optional[float], Dict[str, Any]]:
        """Collect system-level metrics"""
        try:
            if definition.name == "cpu_percent":
                value = psutil.cpu_percent(interval=1)
                metadata = {"cores": psutil.cpu_count()}
                return value, metadata
            
            elif definition.name == "memory_percent":
                memory = psutil.virtual_memory()
                value = memory.percent
                metadata = {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3)
                }
                return value, metadata
            
            elif definition.name == "disk_usage_percent":
                disk = psutil.disk_usage('/')
                value = disk.percent
                metadata = {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3)
                }
                return value, metadata
            
            elif definition.name == "network_bytes_sent":
                net = psutil.net_io_counters()
                value = net.bytes_sent
                metadata = {"packets_sent": net.packets_sent}
                return value, metadata
            
            elif definition.name == "network_bytes_recv":
                net = psutil.net_io_counters()
                value = net.bytes_recv
                metadata = {"packets_recv": net.packets_recv}
                return value, metadata
            
        except Exception as e:
            print(f"[Metrics] System metric collection error: {e}")
        
        return None, {}
    
    async def _collect_http_metric(self, definition: MetricDefinition) -> Tuple[Optional[float], Dict[str, Any]]:
        """Collect HTTP endpoint metrics"""
        try:
            # Extract URL from labels or use default
            url = definition.labels.get("url", "http://localhost:8080")
            
            start_time = time.time()
            async with self.session.get(url, timeout=10) as response:
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                if definition.name == "endpoint_response_time":
                    value = response_time
                    metadata = {
                        "status_code": response.status,
                        "url": url,
                        "success": response.status < 400
                    }
                    return value, metadata
                
                elif definition.name == "endpoint_availability":
                    value = 1.0 if response.status < 400 else 0.0
                    metadata = {
                        "status_code": response.status,
                        "url": url,
                        "response_time_ms": response_time
                    }
                    return value, metadata
            
        except Exception as e:
            # Endpoint unavailable
            if definition.name == "endpoint_availability":
                return 0.0, {"error": str(e), "url": url}
            elif definition.name == "endpoint_response_time":
                return 3000.0, {"error": str(e), "url": url}  # 3s timeout
        
        return None, {}
    
    async def _collect_prometheus_metric(self, definition: MetricDefinition) -> Tuple[Optional[float], Dict[str, Any]]:
        """Collect metrics from Prometheus endpoint"""
        if not self.prometheus_enabled or not self.prometheus_url:
            return None, {"error": "Prometheus not configured"}
        
        try:
            # Use configured Prometheus URL
            query = definition.labels.get("query", definition.name)
            
            # Execute Prometheus query
            async with self.session.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=10
            ) as response:
                if response.status != 200:
                    return None, {"error": f"Prometheus returned {response.status}"}
                
                data = await response.json()
                
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        # Get the first result
                        value_str = results[0].get("value", [None, None])[1]
                        if value_str:
                            value = float(value_str)
                            metadata = {
                                "metric": results[0].get("metric", {}),
                                "result_count": len(results)
                            }
                            return value, metadata
            
        except Exception as e:
            print(f"[Metrics] Prometheus query failed: {e}")
        
        return None, {}
    
    async def _collect_docker_metric(self, definition: MetricDefinition) -> Tuple[Optional[float], Dict[str, Any]]:
        """Collect Docker container metrics"""
        try:
            import docker
            client = docker.from_env()
            
            container_id = definition.labels.get("container_id", "agent50")
            
            # Get container stats
            containers = client.containers.list(all=True)
            for container in containers:
                if container.id.startswith(container_id) or container.name == container_id:
                    stats = container.stats(stream=False)
                    
                    if definition.name == "container_cpu_percent":
                        # Calculate CPU percentage
                        cpu_stats = stats.get("cpu_stats", {})
                        precpu_stats = stats.get("precpu_stats", {})
                        
                        cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - \
                                  precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                        system_delta = cpu_stats.get("system_cpu_usage", 0) - \
                                     precpu_stats.get("system_cpu_usage", 0)
                        
                        if system_delta > 0:
                            value = (cpu_delta / system_delta) * 100.0
                        else:
                            value = 0.0
                        
                        metadata = {
                            "container_id": container.id[:12],
                            "container_name": container.name
                        }
                        return value, metadata
                    
                    elif definition.name == "container_memory_usage":
                        memory_stats = stats.get("memory_stats", {})
                        value = memory_stats.get("usage", 0) / (1024 * 1024)  # Convert to MB
                        limit = memory_stats.get("limit", 0) / (1024 * 1024)  # Convert to MB
                        
                        metadata = {
                            "container_id": container.id[:12],
                            "container_name": container.name,
                            "memory_limit_mb": limit,
                            "memory_percent": (value / limit * 100) if limit > 0 else 0
                        }
                        return value, metadata
            
        except Exception as e:
            print(f"[Metrics] Docker metric collection error: {e}")
        
        return None, {}
    
    async def _collect_platform_metric(self, definition: MetricDefinition) -> Tuple[Optional[float], Dict[str, Any]]:
        """Collect metrics from platform APIs (Render, Railway, Fly.io)"""
        try:
            platform = definition.labels.get("platform", "unknown")
            
            if platform == "render":
                # Render.com API metrics
                api_key = os.getenv("RENDER_API_KEY")
                service_id = definition.labels.get("service_id")
                
                if api_key and service_id:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    async with self.session.get(
                        f"https://api.render.com/v1/services/{service_id}/metrics",
                        headers=headers,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            value = data.get(definition.name, 0)
                            return value, {"platform": "render", "service_id": service_id}
            
            elif platform == "railway":
                # Railway.app GraphQL API
                api_token = os.getenv("RAILWAY_API_TOKEN")
                deployment_id = definition.labels.get("deployment_id")
                
                if api_token and deployment_id:
                    query = """
                    query($deploymentId: String!) {
                        deployment(id: $deploymentId) {
                            stats {
                                cpu
                                memory
                            }
                        }
                    }
                    """
                    
                    headers = {
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with self.session.post(
                        "https://backboard.railway.app/graphql/v2",
                        json={"query": query, "variables": {"deploymentId": deployment_id}},
                        headers=headers,
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            stats = data.get("data", {}).get("deployment", {}).get("stats", {})
                            
                            if definition.name == "railway_cpu_percent":
                                value = stats.get("cpu", 0)
                                return value, {"platform": "railway", "deployment_id": deployment_id}
                            elif definition.name == "railway_memory_mb":
                                value = stats.get("memory", 0)
                                return value, {"platform": "railway", "deployment_id": deployment_id}
            
            elif platform == "flyio":
                # Fly.io metrics via flyctl or API
                app_name = definition.labels.get("app_name")
                
                if app_name:
                    # Use flyctl command-line
                    import subprocess
                    result = subprocess.run(
                        ["flyctl", "metrics", "show", "--app", app_name, "--json"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        value = data.get(definition.name, 0)
                        return value, {"platform": "flyio", "app_name": app_name}
        
        except Exception as e:
            print(f"[Metrics] Platform metric collection error: {e}")
        
        return None, {}
    
    async def _collect_custom_metric(self, definition: MetricDefinition) -> Tuple[Optional[float], Dict[str, Any]]:
        """Collect custom metrics"""
        try:
            # Check if custom collector is defined
            if hasattr(definition, 'custom_collector'):
                result = await definition.custom_collector()
                if result and isinstance(result, tuple) and len(result) == 2:
                    return result
                else:
                    raise NotImplementedError(f"Custom metric {definition.name} collector must return (value, metadata) tuple")
            else:
                raise NotImplementedError(f"No collector defined for custom metric: {definition.name}")
        
        except Exception as e:
            print(f"[Metrics] Custom metric collection error: {e}")
        
        return None, {}
    
    async def _check_thresholds(self, definition: MetricDefinition, value: float, metadata: Dict[str, Any]):
        """Check if metric value exceeds thresholds"""
        thresholds = definition.thresholds
        
        if not thresholds:
            return
        
        warning = thresholds.get("warning")
        critical = thresholds.get("critical")
        
        alert_level = None
        if critical is not None and value >= critical:
            alert_level = "critical"
        elif warning is not None and value >= warning:
            alert_level = "warning"
        
        if alert_level:
            alert_data = {
                "id": f"metric_alert_{definition.name}_{int(time.time())}",
                "metric": definition.name,
                "value": value,
                "threshold": thresholds[alert_level],
                "level": alert_level,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
                "type": "threshold_exceeded"
            }
            
            # Record alert using proper monitoring schema
            self._record_metric_alert(alert_data)
            
            # Emit health degradation signal to health monitor
            if self.health_monitor:
                await self._emit_health_degradation(definition, value, alert_level)
            
            print(f"[Metrics] THRESHOLD ALERT: {definition.name}={value} ({alert_level})")
    
    def _record_metric_alert(self, alert_data: Dict[str, Any]):
        """Record metric alert using proper monitoring schema"""
        try:
            # Load current project status
            project_status = self.memory.get_project_status() or {}
            
            # Initialize monitoring section if not exists
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            # Initialize alerts list if not exists
            if "alerts" not in project_status["monitoring"]:
                project_status["monitoring"]["alerts"] = []
            
            # Add new alert
            project_status["monitoring"]["alerts"].append(alert_data)
            
            # Keep only last 100 alerts
            if len(project_status["monitoring"]["alerts"]) > 100:
                project_status["monitoring"]["alerts"] = project_status["monitoring"]["alerts"][-100:]
            
            # Update project status
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
        except Exception as e:
            print(f"[Metrics] Failed to record alert: {e}")
    
    async def _emit_health_degradation(self, definition: MetricDefinition, value: float, level: str):
        """Emit health degradation signal to health monitor"""
        if not self.health_monitor or not hasattr(self.health_monitor, 'record_health_degradation'):
            return
        
        try:
            degradation_data = {
                "component": f"metric:{definition.name}",
                "metric": definition.name,
                "value": value,
                "threshold_level": level,
                "metric_type": definition.type.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Call health monitor's degradation handler
            await self.health_monitor.record_health_degradation(degradation_data)
            
        except Exception as e:
            print(f"[Metrics] Failed to emit health degradation: {e}")
    
    async def _baseline_calculation_loop(self):
        """Calculate baselines for metrics"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                with self.lock:
                    for metric_name, series in self.metrics_registry.items():
                        if len(series.samples) >= self.anomaly_config["min_samples_for_baseline"]:
                            # Calculate baseline statistics
                            stats = series.calculate_statistics(window_seconds=3600)  # 1 hour window
                            
                            if stats:
                                series.baseline = {
                                    "mean": stats["mean"],
                                    "stddev": stats["stddev"],
                                    "min": stats["min"],
                                    "max": stats["max"],
                                    "p95": stats["p95"],
                                    "calculated_at": datetime.now().isoformat(),
                                    "sample_count": stats["count"]
                                }
                
                # Save baselines to memory periodically
                await self._save_state_to_memory()
                
            except Exception as e:
                print(f"[Metrics] Baseline calculation error: {e}")
                await asyncio.sleep(60)
    
    async def _anomaly_detection_loop(self):
        """Detect anomalies in metric values"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Every minute
                
                with self.lock:
                    for metric_name, series in self.metrics_registry.items():
                        if not series.samples:
                            continue
                        
                        # Get most recent sample
                        recent_sample = series.samples[-1]
                        
                        # Check for anomalies using z-score method
                        if series.baseline and series.baseline["stddev"] > 0:
                            z_score = abs(recent_sample.value - series.baseline["mean"]) / series.baseline["stddev"]
                            
                            if z_score > self.anomaly_config["z_score_threshold"]:
                                anomaly = {
                                    "id": f"metric_anomaly_{metric_name}_{int(time.time())}",
                                    "timestamp": recent_sample.timestamp.isoformat(),
                                    "metric": metric_name,
                                    "value": recent_sample.value,
                                    "z_score": z_score,
                                    "baseline_mean": series.baseline["mean"],
                                    "baseline_stddev": series.baseline["stddev"],
                                    "detected_at": datetime.now().isoformat(),
                                    "type": "statistical_anomaly"
                                }
                                
                                series.anomalies.append(anomaly)
                                
                                # Keep only recent anomalies
                                if len(series.anomalies) > 100:
                                    series.anomalies = series.anomalies[-100:]
                                
                                # Record anomaly as incident
                                self._record_metric_alert(anomaly)
                                
                                print(f"[Metrics] ANOMALY DETECTED: {metric_name}={recent_sample.value} "
                                      f"(z-score={z_score:.2f})")
            
            except Exception as e:
                print(f"[Metrics] Anomaly detection error: {e}")
                await asyncio.sleep(30)
    
    async def _save_state_to_memory(self):
        """Save current metrics state to memory"""
        try:
            state = {
                "metrics_registered": list(self.metrics_registry.keys()),
                "collection_status": {
                    "running": self.running,
                    "tasks_active": len(self.collection_tasks),
                    "last_updated": datetime.now().isoformat()
                },
                "baselines": {}
            }
            
            # Save baselines
            for metric_name, series in self.metrics_registry.items():
                if series.baseline:
                    state["baselines"][metric_name] = series.baseline
            
            # Update project status with metrics summary
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            project_status["monitoring"]["metrics"] = {
                "summary": self.get_summary(),
                "state": state,
                "last_updated": datetime.now().isoformat()
            }
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
        except Exception as e:
            print(f"[Metrics] Failed to save state to memory: {e}")
    
    def get_metric(self, metric_name: str, window_seconds: int = 300) -> Optional[Dict[str, Any]]:
        """Get recent metric data"""
        with self.lock:
            series = self.metrics_registry.get(metric_name)
            if not series:
                return None
            
            recent = series.get_recent(window_seconds)
            stats = series.calculate_statistics(window_seconds)
            
            return {
                "name": metric_name,
                "type": series.definition.type.value,
                "samples": [
                    {
                        "timestamp": s.timestamp.isoformat(),
                        "value": s.value,
                        "labels": s.labels
                    }
                    for s in recent[-50:]  # Last 50 samples
                ],
                "statistics": stats,
                "baseline": series.baseline,
                "recent_anomalies": series.anomalies[-10:] if series.anomalies else []
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self.lock:
            summary = {
                "total_metrics": len(self.metrics_registry),
                "by_type": defaultdict(int),
                "by_source": defaultdict(int),
                "health_status": "unknown",
                "alerts": []
            }
            
            for metric_name, series in self.metrics_registry.items():
                summary["by_type"][series.definition.type.value] += 1
                summary["by_source"][series.definition.source.value] += 1
            
            # Calculate overall health based on thresholds
            critical_alerts = 0
            warning_alerts = 0
            
            for metric_name, series in self.metrics_registry.items():
                if series.samples:
                    latest = series.samples[-1].value
                    thresholds = series.definition.thresholds
                    
                    if thresholds.get("critical") and latest >= thresholds["critical"]:
                        critical_alerts += 1
                    elif thresholds.get("warning") and latest >= thresholds["warning"]:
                        warning_alerts += 1
            
            # Determine overall health
            if critical_alerts > 0:
                summary["health_status"] = "critical"
            elif warning_alerts > 0:
                summary["health_status"] = "warning"
            else:
                summary["health_status"] = "healthy"
            
            summary["critical_alerts"] = critical_alerts
            summary["warning_alerts"] = warning_alerts
            
            return summary
    
    def discover_application_metrics(self, app_url: str = "http://localhost:8080"):
        """Discover available metrics from application"""
        try:
            # Try to find Prometheus metrics endpoint
            endpoints_to_try = [
                f"{app_url}/metrics",
                f"{app_url}/actuator/prometheus",
                f"{app_url}/prometheus/metrics"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    import requests
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        print(f"[Metrics] Discovered Prometheus endpoint: {endpoint}")
                        
                        # Configure Prometheus
                        prom_url = endpoint.replace("/metrics", "").replace("/actuator/prometheus", "")
                        self.configure_prometheus(prom_url)
                        break
                
                except (requests.RequestException, ImportError):
                    continue
            
            # Also try to discover health endpoints
            health_endpoints = [
                f"{app_url}/health",
                f"{app_url}/actuator/health",
                f"{app_url}/api/health"
            ]
            
            for endpoint in health_endpoints:
                try:
                    import requests
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        print(f"[Metrics] Discovered health endpoint: {endpoint}")
                        
                        # Register health check metrics
                        definition = MetricDefinition(
                            name=f"health_{endpoint.split('/')[-1]}",
                            type=MetricType.SYNTHETIC,
                            source=MetricSource.HTTP_ENDPOINT,
                            collection_interval=30,
                            retention_period=1800,
                            labels={"url": endpoint}
                        )
                        
                        self.register_metric(definition)
                        break
                
                except (requests.RequestException, ImportError):
                    continue
        
        except Exception as e:
            print(f"[Metrics] Discovery error: {e}")
    
    def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """Export metrics in specified format"""
        with self.lock:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {}
            }
            
            for metric_name, series in self.metrics_registry.items():
                export_data["metrics"][metric_name] = {
                    "type": series.definition.type.value,
                    "source": series.definition.source.value,
                    "samples_count": len(series.samples),
                    "latest_value": series.samples[-1].value if series.samples else None,
                    "statistics": series.calculate_statistics(300),
                    "baseline": series.baseline
                }
            
            return export_data
    
    # Health Monitor Plugin Interface
    async def check_health(self) -> Dict[str, Any]:
        """Health check for the metrics collector itself"""
        with self.lock:
            return {
                "status": "healthy" if self.running else "stopped",
                "metrics_collected": len(self.metrics_registry),
                "active_tasks": len(self.collection_tasks),
                "last_check": datetime.now().isoformat(),
                "details": {
                    "prometheus_enabled": self.prometheus_enabled,
                    "prometheus_url": self.prometheus_url
                }
            }


# Async context manager for easy usage
class MetricsCollectorContext:
    """Context manager for metrics collector"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.collector = MetricsCollector(memory_manager)
    
    async def __aenter__(self):
        await self.collector.start()
        return self.collector
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.collector.stop()