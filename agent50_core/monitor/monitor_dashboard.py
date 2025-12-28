"""
monitor_dashboard.py - Real-time monitoring dashboard and reporting for Agent 50
Provides human-readable interface for monitoring, control, and historical analysis
"""

import asyncio
import time
import json
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict
import math

# Import existing MemoryManager
from agent50_core.memory.memory_manager import MemoryManager


class DashboardView(Enum):
    """Dashboard view types"""
    OVERVIEW = "overview"
    HEALTH = "health"
    METRICS = "metrics"
    ALERTS = "alerts"
    INCIDENTS = "incidents"
    REMEDIATIONS = "remediations"
    DEPLOYMENTS = "deployments"
    CUSTOM = "custom"


class TimeRange(Enum):
    """Time ranges for data display"""
    LAST_HOUR = "1h"
    LAST_4_HOURS = "4h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    CUSTOM = "custom"


class WidgetType(Enum):
    """Dashboard widget types"""
    METRIC_GAUGE = "metric_gauge"
    METRIC_GRAPH = "metric_graph"
    HEALTH_STATUS = "health_status"
    ALERT_FEED = "alert_feed"
    INCIDENT_LIST = "incident_list"
    REMEDIATION_STATUS = "remediation_status"
    DEPLOYMENT_STATUS = "deployment_status"
    STATS_CARD = "stats_card"
    TIMELINE = "timeline"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    id: str
    type: WidgetType
    title: str
    position: Dict[str, int]  # x, y, width, height
    config: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 30  # seconds
    last_refresh: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "position": self.position,
            "config": self.config,
            "refresh_interval": self.refresh_interval,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None
        }


@dataclass
class DashboardLayout:
    """Dashboard layout configuration"""
    id: str
    name: str
    description: str
    view: DashboardView
    widgets: List[DashboardWidget]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "view": self.view.value,
            "widget_count": len(self.widgets),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_default": self.is_default
        }


@dataclass
class DashboardReport:
    """Dashboard report configuration"""
    id: str
    name: str
    description: str
    schedule: str  # cron expression or "manual"
    recipients: List[str]
    format: str = "html"  # html, pdf, json
    last_sent: Optional[datetime] = None
    next_send: Optional[datetime] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schedule": self.schedule,
            "recipient_count": len(self.recipients),
            "format": self.format,
            "last_sent": self.last_sent.isoformat() if self.last_sent else None,
            "next_send": self.next_send.isoformat() if self.next_send else None,
            "enabled": self.enabled
        }


class MonitorDashboard:
    """
    Real-time monitoring dashboard and reporting system
    Provides human interface for monitoring, control, and historical analysis
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.layouts: Dict[str, DashboardLayout] = {}
        self.reports: Dict[str, DashboardReport] = {}
        self.active_connections: Dict[str, Dict[str, Any]] = {}  # WebSocket connections
        self.dashboard_lock = threading.Lock()
        self.running = False
        
        # Data sources (will be set by other components)
        self.health_monitor = None
        self.metrics_collector = None
        self.alert_correlator = None
        self.incident_response = None
        self.auto_remediation = None
        
        # Configuration
        self.config = {
            "auto_refresh_interval": 30,  # seconds
            "max_data_points": 1000,
            "retention_days": 90,
            "theme": "dark",
            "timezone": "UTC"
        }
        
        # Statistics
        self.stats = {
            "connections_total": 0,
            "active_connections": 0,
            "widgets_rendered": 0,
            "data_requests": 0,
            "reports_generated": 0,
            "avg_response_time_ms": 0
        }
        
        # Load dashboard configuration
        self._load_configuration()
        self._create_default_layouts()
        
        print(f"[Dashboard] Initialized with {len(self.layouts)} layouts and {len(self.reports)} reports")
    
    def set_data_sources(self, health_monitor=None, metrics_collector=None,
                        alert_correlator=None, incident_response=None,
                        auto_remediation=None):
        """Set references to other monitoring components"""
        self.health_monitor = health_monitor
        self.metrics_collector = metrics_collector
        self.alert_correlator = alert_correlator
        self.incident_response = incident_response
        self.auto_remediation = auto_remediation
        
        print("[Dashboard] Data sources configured")
    
    def _load_configuration(self):
        """Load dashboard configuration from memory"""
        try:
            project_status = self.memory.get_project_status() or {}
            monitoring_config = project_status.get("monitoring", {})
            
            # Load dashboard config
            if "dashboard_config" in monitoring_config:
                self.config.update(monitoring_config["dashboard_config"])
            
            # Load layouts
            if "dashboard_layouts" in monitoring_config:
                layouts_data = monitoring_config["dashboard_layouts"]
                for layout_id, layout_data in layouts_data.items():
                    try:
                        layout = self._create_layout_from_dict(layout_data)
                        self.layouts[layout_id] = layout
                    except Exception as e:
                        print(f"[Dashboard] Failed to load layout {layout_id}: {e}")
            
            # Load reports
            if "dashboard_reports" in monitoring_config:
                reports_data = monitoring_config["dashboard_reports"]
                for report_id, report_data in reports_data.items():
                    try:
                        report = self._create_report_from_dict(report_data)
                        self.reports[report_id] = report
                    except Exception as e:
                        print(f"[Dashboard] Failed to load report {report_id}: {e}")
            
            print(f"[Dashboard] Configuration loaded")
            
        except Exception as e:
            print(f"[Dashboard] Failed to load configuration: {e}")
    
    def _create_default_layouts(self):
        """Create default dashboard layouts"""
        if self.layouts:
            return  # Already have layouts
        
        # Overview Dashboard
        overview_widgets = [
            DashboardWidget(
                id="overall_health",
                type=WidgetType.HEALTH_STATUS,
                title="Overall System Health",
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                config={"component": "overall", "show_history": True}
            ),
            DashboardWidget(
                id="critical_alerts",
                type=WidgetType.ALERT_FEED,
                title="Critical Alerts",
                position={"x": 6, "y": 0, "width": 6, "height": 4},
                config={"severity": "critical", "limit": 10}
            ),
            DashboardWidget(
                id="cpu_usage",
                type=WidgetType.METRIC_GAUGE,
                title="CPU Usage",
                position={"x": 0, "y": 4, "width": 3, "height": 3},
                config={"metric": "cpu_percent", "thresholds": {"warning": 80, "critical": 95}}
            ),
            DashboardWidget(
                id="memory_usage",
                type=WidgetType.METRIC_GAUGE,
                title="Memory Usage",
                position={"x": 3, "y": 4, "width": 3, "height": 3},
                config={"metric": "memory_percent", "thresholds": {"warning": 85, "critical": 95}}
            ),
            DashboardWidget(
                id="active_incidents",
                type=WidgetType.INCIDENT_LIST,
                title="Active Incidents",
                position={"x": 6, "y": 4, "width": 6, "height": 3},
                config={"state": "active", "limit": 5}
            ),
            DashboardWidget(
                id="response_times",
                type=WidgetType.METRIC_GRAPH,
                title="Response Times",
                position={"x": 0, "y": 7, "width": 12, "height": 5},
                config={"metric": "http_request_duration_seconds", "time_range": "1h"}
            )
        ]
        
        overview_layout = DashboardLayout(
            id="overview",
            name="Overview Dashboard",
            description="High-level overview of system health and alerts",
            view=DashboardView.OVERVIEW,
            widgets=overview_widgets,
            is_default=True
        )
        
        # Health Dashboard
        health_widgets = [
            DashboardWidget(
                id="service_health_grid",
                type=WidgetType.HEALTH_STATUS,
                title="Service Health Grid",
                position={"x": 0, "y": 0, "width": 12, "height": 6},
                config={"layout": "grid", "services": "all"}
            ),
            DashboardWidget(
                id="health_timeline",
                type=WidgetType.TIMELINE,
                title="Health Timeline",
                position={"x": 0, "y": 6, "width": 12, "height": 6},
                config={"component": "overall", "time_range": "24h"}
            )
        ]
        
        health_layout = DashboardLayout(
            id="health",
            name="Health Dashboard",
            description="Detailed service health monitoring",
            view=DashboardView.HEALTH,
            widgets=health_widgets
        )
        
        # Metrics Dashboard
        metrics_widgets = [
            DashboardWidget(
                id="cpu_graph",
                type=WidgetType.METRIC_GRAPH,
                title="CPU Usage Over Time",
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                config={"metric": "cpu_percent", "time_range": "1h"}
            ),
            DashboardWidget(
                id="memory_graph",
                type=WidgetType.METRIC_GRAPH,
                title="Memory Usage Over Time",
                position={"x": 6, "y": 0, "width": 6, "height": 4},
                config={"metric": "memory_percent", "time_range": "1h"}
            ),
            DashboardWidget(
                id="network_graph",
                type=WidgetType.METRIC_GRAPH,
                title="Network Traffic",
                position={"x": 0, "y": 4, "width": 6, "height": 4},
                config={"metric": "network_bytes", "time_range": "1h"}
            ),
            DashboardWidget(
                id="disk_graph",
                type=WidgetType.METRIC_GRAPH,
                title="Disk Usage",
                position={"x": 6, "y": 4, "width": 6, "height": 4},
                config={"metric": "disk_usage_percent", "time_range": "24h"}
            )
        ]
        
        metrics_layout = DashboardLayout(
            id="metrics",
            name="Metrics Dashboard",
            description="System metrics and performance monitoring",
            view=DashboardView.METRICS,
            widgets=metrics_widgets
        )
        
        # Incidents Dashboard
        incidents_widgets = [
            DashboardWidget(
                id="incident_stats",
                type=WidgetType.STATS_CARD,
                title="Incident Statistics",
                position={"x": 0, "y": 0, "width": 12, "height": 3},
                config={"type": "incident_stats"}
            ),
            DashboardWidget(
                id="active_incidents_list",
                type=WidgetType.INCIDENT_LIST,
                title="Active Incidents",
                position={"x": 0, "y": 3, "width": 6, "height": 9},
                config={"state": "active", "limit": 20, "show_details": True}
            ),
            DashboardWidget(
                id="recent_incidents",
                type=WidgetType.INCIDENT_LIST,
                title="Recent Incidents",
                position={"x": 6, "y": 3, "width": 6, "height": 9},
                config={"state": "resolved", "limit": 10, "time_range": "7d"}
            )
        ]
        
        incidents_layout = DashboardLayout(
            id="incidents",
            name="Incidents Dashboard",
            description="Incident monitoring and management",
            view=DashboardView.INCIDENTS,
            widgets=incidents_widgets
        )
        
        # Store layouts
        self.layouts = {
            "overview": overview_layout,
            "health": health_layout,
            "metrics": metrics_layout,
            "incidents": incidents_layout
        }
    
    def _create_layout_from_dict(self, data: Dict[str, Any]) -> DashboardLayout:
        """Create DashboardLayout from dictionary"""
        widgets = []
        for widget_data in data.get("widgets", []):
            widget = DashboardWidget(
                id=widget_data["id"],
                type=WidgetType(widget_data["type"]),
                title=widget_data["title"],
                position=widget_data["position"],
                config=widget_data.get("config", {}),
                refresh_interval=widget_data.get("refresh_interval", 30)
            )
            widgets.append(widget)
        
        return DashboardLayout(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            view=DashboardView(data["view"]),
            widgets=widgets,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            is_default=data.get("is_default", False)
        )
    
    def _create_report_from_dict(self, data: Dict[str, Any]) -> DashboardReport:
        """Create DashboardReport from dictionary"""
        return DashboardReport(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            schedule=data["schedule"],
            recipients=data.get("recipients", []),
            format=data.get("format", "html"),
            last_sent=datetime.fromisoformat(data["last_sent"]) if data.get("last_sent") else None,
            next_send=datetime.fromisoformat(data["next_send"]) if data.get("next_send") else None,
            enabled=data.get("enabled", True)
        )
    
    async def start(self):
        """Start the dashboard server"""
        if self.running:
            print("[Dashboard] Dashboard already running")
            return
        
        print("[Dashboard] Starting monitoring dashboard...")
        self.running = True
        
        # Start WebSocket server (in production)
        # For now, start data refresh loop
        asyncio.create_task(self._data_refresh_loop())
        
        # Start report scheduler
        asyncio.create_task(self._report_scheduler())
        
        print("[Dashboard] Dashboard started")
    
    async def stop(self):
        """Stop the dashboard server"""
        if not self.running:
            return
        
        print("[Dashboard] Stopping monitoring dashboard...")
        self.running = False
        
        # Close all connections
        with self.dashboard_lock:
            self.active_connections.clear()
        
        print("[Dashboard] Dashboard stopped")
    
    async def _data_refresh_loop(self):
        """Periodically refresh dashboard data"""
        while self.running:
            try:
                await asyncio.sleep(self.config["auto_refresh_interval"])
                
                # Refresh data for active connections
                with self.dashboard_lock:
                    for connection_id, connection in list(self.active_connections.items()):
                        if time.time() - connection.get("last_activity", 0) > 300:  # 5 minutes
                            # Close stale connection
                            del self.active_connections[connection_id]
                            continue
                        
                        # Refresh dashboard data
                        await self._refresh_connection_data(connection_id, connection)
                
            except Exception as e:
                print(f"[Dashboard] Error in data refresh loop: {e}")
                await asyncio.sleep(30)
    
    async def _refresh_connection_data(self, connection_id: str, connection: Dict[str, Any]):
        """Refresh data for a specific connection"""
        try:
            layout_id = connection.get("layout_id")
            if not layout_id or layout_id not in self.layouts:
                return
            
            layout = self.layouts[layout_id]
            
            # Refresh each widget
            for widget in layout.widgets:
                # Check if widget needs refresh
                if widget.last_refresh and (
                    time.time() - widget.last_refresh.timestamp() < widget.refresh_interval
                ):
                    continue
                
                # Get widget data
                widget_data = await self._get_widget_data(widget)
                widget.data = widget_data
                widget.last_refresh = datetime.now()
                
                self.stats["widgets_rendered"] += 1
            
            # Send updated data to client (in production via WebSocket)
            # For now, just update in memory
            
        except Exception as e:
            print(f"[Dashboard] Error refreshing connection {connection_id}: {e}")
    
    async def _get_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for a widget"""
        start_time = time.time()
        
        try:
            if widget.type == WidgetType.METRIC_GAUGE:
                data = await self._get_metric_gauge_data(widget)
            
            elif widget.type == WidgetType.METRIC_GRAPH:
                data = await self._get_metric_graph_data(widget)
            
            elif widget.type == WidgetType.HEALTH_STATUS:
                data = await self._get_health_status_data(widget)
            
            elif widget.type == WidgetType.ALERT_FEED:
                data = await self._get_alert_feed_data(widget)
            
            elif widget.type == WidgetType.INCIDENT_LIST:
                data = await self._get_incident_list_data(widget)
            
            elif widget.type == WidgetType.REMEDIATION_STATUS:
                data = await self._get_remediation_status_data(widget)
            
            elif widget.type == WidgetType.DEPLOYMENT_STATUS:
                data = await self._get_deployment_status_data(widget)
            
            elif widget.type == WidgetType.STATS_CARD:
                data = await self._get_stats_card_data(widget)
            
            elif widget.type == WidgetType.TIMELINE:
                data = await self._get_timeline_data(widget)
            
            else:
                data = {"error": f"Unknown widget type: {widget.type}"}
            
            # Update response time statistics
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            self.stats["data_requests"] += 1
            old_avg = self.stats["avg_response_time_ms"]
            count = self.stats["data_requests"]
            self.stats["avg_response_time_ms"] = (
                (old_avg * (count - 1) + response_time) / count
            ) if count > 1 else response_time
            
            return {
                "widget_id": widget.id,
                "type": widget.type.value,
                "title": widget.title,
                "data": data,
                "refreshed_at": datetime.now().isoformat(),
                "response_time_ms": response_time
            }
            
        except Exception as e:
            return {
                "widget_id": widget.id,
                "type": widget.type.value,
                "title": widget.title,
                "error": str(e),
                "refreshed_at": datetime.now().isoformat()
            }
    
    async def _get_metric_gauge_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for metric gauge widget"""
        metric_name = widget.config.get("metric", "cpu_percent")
        thresholds = widget.config.get("thresholds", {})
        
        # Get current metric value
        current_value = 0
        status = "unknown"
        
        if self.metrics_collector and hasattr(self.metrics_collector, 'get_metric'):
            metric_data = self.metrics_collector.get_metric(metric_name, window_seconds=300)
            if metric_data and metric_data.get("samples"):
                latest_sample = metric_data["samples"][-1]
                current_value = latest_sample.get("value", 0)
        
        # Determine status based on thresholds
        warning = thresholds.get("warning")
        critical = thresholds.get("critical")
        
        if critical is not None and current_value >= critical:
            status = "critical"
        elif warning is not None and current_value >= warning:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "metric": metric_name,
            "value": current_value,
            "status": status,
            "thresholds": thresholds,
            "unit": self._get_metric_unit(metric_name)
        }
    
    async def _get_metric_graph_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for metric graph widget"""
        metric_name = widget.config.get("metric")
        time_range = widget.config.get("time_range", "1h")
        
        if not metric_name:
            return {"error": "Metric not specified"}
        
        # Calculate time window
        window_seconds = self._time_range_to_seconds(time_range)
        
        # Get metric data
        data_points = []
        if self.metrics_collector and hasattr(self.metrics_collector, 'get_metric'):
            metric_data = self.metrics_collector.get_metric(metric_name, window_seconds)
            if metric_data and metric_data.get("samples"):
                for sample in metric_data["samples"]:
                    data_points.append({
                        "timestamp": sample.get("timestamp"),
                        "value": sample.get("value", 0)
                    })
        
        return {
            "metric": metric_name,
            "time_range": time_range,
            "data_points": data_points[-self.config["max_data_points"]:],  # Limit data points
            "unit": self._get_metric_unit(metric_name),
            "statistics": metric_data.get("statistics", {}) if metric_data else {}
        }
    
    async def _get_health_status_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for health status widget"""
        component = widget.config.get("component", "overall")
        layout = widget.config.get("layout", "grid")
        
        if component == "overall":
            # Get overall health status
            project_status = self.memory.get_project_status() or {}
            monitoring = project_status.get("monitoring", {})
            
            health_status = monitoring.get("health_status", {})
            metrics = monitoring.get("metrics", {}).get("summary", {})
            
            return {
                "component": "overall",
                "status": health_status.get("overall", "unknown"),
                "details": {
                    "health_score": health_status.get("score", 0),
                    "critical_alerts": metrics.get("critical_alerts", 0),
                    "warning_alerts": metrics.get("warning_alerts", 0)
                },
                "services": []  # Would populate with service health in production
            }
        
        else:
            # Get specific component health
            if self.health_monitor and hasattr(self.health_monitor, 'check_component_health'):
                health_data = await self.health_monitor.check_component_health(component)
                return {
                    "component": component,
                    "status": health_data.get("status", "unknown"),
                    "details": health_data.get("details", {}),
                    "last_check": health_data.get("last_check")
                }
            else:
                return {
                    "component": component,
                    "status": "unknown",
                    "error": "Health monitor not available"
                }
    
    async def _get_alert_feed_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for alert feed widget"""
        severity = widget.config.get("severity")
        limit = widget.config.get("limit", 10)
        
        alerts = []
        
        # Get alerts from memory
        project_status = self.memory.get_project_status() or {}
        monitoring = project_status.get("monitoring", {})
        
        # Check correlation groups
        correlation_groups = monitoring.get("correlation_groups", [])
        for group in correlation_groups:
            primary_alert = group.get("primary_alert", {})
            
            # Filter by severity if specified
            if severity and primary_alert.get("severity") != severity:
                continue
            
            alerts.append({
                "id": group.get("id"),
                "type": "correlated",
                "severity": primary_alert.get("severity"),
                "component": primary_alert.get("component"),
                "message": primary_alert.get("message"),
                "timestamp": group.get("created_at"),
                "alert_count": group.get("alert_count", 1),
                "state": group.get("state")
            })
            
            if len(alerts) >= limit:
                break
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "severity": severity,
            "alerts": alerts[:limit],
            "total_count": len(alerts)
        }
    
    async def _get_incident_list_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for incident list widget"""
        state = widget.config.get("state", "active")
        limit = widget.config.get("limit", 10)
        time_range = widget.config.get("time_range")
        
        incidents = []
        
        if self.incident_response:
            if state == "active":
                incidents_data = await self.incident_response.get_active_incidents()
                incidents = incidents_data[:limit]
            else:
                # Get resolved incidents from memory
                project_status = self.memory.get_project_status() or {}
                monitoring = project_status.get("monitoring", {})
                
                incident_history = monitoring.get("incident_history", [])
                
                # Filter by time range if specified
                if time_range:
                    cutoff = datetime.now() - timedelta(
                        seconds=self._time_range_to_seconds(time_range)
                    )
                    incident_history = [
                        inc for inc in incident_history
                        if datetime.fromisoformat(inc.get("resolved_at", inc.get("created_at", ""))) >= cutoff
                    ]
                
                incidents = incident_history[:limit]
        else:
            # Fallback to memory
            project_status = self.memory.get_project_status() or {}
            monitoring = project_status.get("monitoring", {})
            
            if state == "active":
                incidents = monitoring.get("active_incidents", [])[:limit]
            else:
                incidents = monitoring.get("incident_history", [])[:limit]
        
        return {
            "state": state,
            "incidents": incidents,
            "count": len(incidents)
        }
    
    async def _get_remediation_status_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for remediation status widget"""
        # Get remediation data from memory
        project_status = self.memory.get_project_status() or {}
        monitoring = project_status.get("monitoring", {})
        
        active_remediations = monitoring.get("active_remediations", [])
        remediation_stats = monitoring.get("remediation_stats", {})
        
        return {
            "active_remediations": active_remediations[:10],  # Limit to 10
            "statistics": remediation_stats,
            "total_active": len(active_remediations)
        }
    
    async def _get_deployment_status_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for deployment status widget"""
        # Get deployment data from memory
        project_status = self.memory.get_project_status() or {}
        
        deployments = []
        
        # Check for recent deployments in project status
        if "last_deployment" in project_status:
            deployments.append(project_status["last_deployment"])
        
        # Check deployment history
        deployment_history = project_status.get("deployment_history", [])[:5]
        deployments.extend(deployment_history)
        
        return {
            "deployments": deployments,
            "count": len(deployments)
        }
    
    async def _get_stats_card_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for stats card widget"""
        stats_type = widget.config.get("type", "general")
        
        # Get various statistics
        project_status = self.memory.get_project_status() or {}
        monitoring = project_status.get("monitoring", {})
        
        if stats_type == "incident_stats":
            incident_stats = monitoring.get("incident_stats", {})
            
            return {
                "type": "incident_stats",
                "stats": {
                    "active_incidents": incident_stats.get("active_incidents", 0),
                    "resolved_today": 0,  # Would calculate from history
                    "avg_resolution_time": incident_stats.get("statistics", {}).get("avg_time_to_resolve", 0),
                    "mttr_minutes": math.floor(incident_stats.get("statistics", {}).get("avg_time_to_resolve", 0) / 60)
                }
            }
        
        elif stats_type == "system_stats":
            # System statistics
            metrics_summary = monitoring.get("metrics", {}).get("summary", {})
            
            return {
                "type": "system_stats",
                "stats": {
                    "health_score": monitoring.get("health_status", {}).get("score", 0),
                    "critical_alerts": metrics_summary.get("critical_alerts", 0),
                    "services_monitored": metrics_summary.get("total_metrics", 0),
                    "uptime_percentage": 99.9  # Would calculate from history
                }
            }
        
        else:
            # General statistics
            return {
                "type": "general",
                "stats": {
                    "total_alerts": 0,
                    "auto_remediations": 0,
                    "manual_interventions": 0,
                    "system_health": "good"
                }
            }
    
    async def _get_timeline_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Get data for timeline widget"""
        component = widget.config.get("component", "overall")
        time_range = widget.config.get("time_range", "24h")
        
        window_seconds = self._time_range_to_seconds(time_range)
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        
        events = []
        
        # Get events from various sources
        project_status = self.memory.get_project_status() or {}
        monitoring = project_status.get("monitoring", {})
        
        # Get incidents
        incidents = monitoring.get("incident_history", []) + monitoring.get("active_incidents", [])
        for incident in incidents:
            created_at = datetime.fromisoformat(incident.get("created_at", ""))
            if created_at >= cutoff:
                events.append({
                    "timestamp": incident.get("created_at"),
                    "type": "incident",
                    "title": f"Incident: {incident.get('title')}",
                    "severity": incident.get("severity"),
                    "details": {"incident_id": incident.get("id")}
                })
        
        # Get deployments
        if "last_deployment" in project_status:
            deployment = project_status["last_deployment"]
            deployed_at = datetime.fromisoformat(deployment.get("timestamp", ""))
            if deployed_at >= cutoff:
                events.append({
                    "timestamp": deployment.get("timestamp"),
                    "type": "deployment",
                    "title": f"Deployment: {deployment.get('platform')}",
                    "severity": "info",
                    "details": {"platform": deployment.get("platform"), "success": deployment.get("success")}
                })
        
        # Get major alerts
        correlation_groups = monitoring.get("correlation_groups", [])
        for group in correlation_groups:
            created_at = datetime.fromisoformat(group.get("created_at", ""))
            if created_at >= cutoff:
                primary_alert = group.get("primary_alert", {})
                if primary_alert.get("severity") in ["critical", "high"]:
                    events.append({
                        "timestamp": group.get("created_at"),
                        "type": "alert",
                        "title": f"Alert: {primary_alert.get('component')}",
                        "severity": primary_alert.get("severity"),
                        "details": {"correlation_group_id": group.get("id")}
                    })
        
        # Sort events by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "component": component,
            "time_range": time_range,
            "events": events[:50],  # Limit events
            "event_count": len(events)
        }
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get display unit for a metric"""
        units = {
            "cpu_percent": "%",
            "memory_percent": "%",
            "disk_usage_percent": "%",
            "network_bytes": "bytes",
            "http_request_duration_seconds": "seconds",
            "database_connections": "connections"
        }
        return units.get(metric_name, "")
    
    def _time_range_to_seconds(self, time_range: str) -> int:
        """Convert time range string to seconds"""
        if time_range.endswith("h"):
            return int(time_range[:-1]) * 3600
        elif time_range.endswith("d"):
            return int(time_range[:-1]) * 86400
        elif time_range.endswith("m"):
            return int(time_range[:-1]) * 60
        else:
            return 3600  # Default to 1 hour
    
    async def _report_scheduler(self):
        """Schedule and send dashboard reports"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.now()
                
                for report_id, report in list(self.reports.items()):
                    if not report.enabled:
                        continue
                    
                    # Check if report should be sent
                    should_send = False
                    
                    if report.schedule == "manual":
                        continue
                    
                    elif report.schedule == "hourly":
                        # Send at the top of each hour
                        if current_time.minute == 0:
                            should_send = True
                    
                    elif report.schedule == "daily":
                        # Send at 9 AM daily
                        if current_time.hour == 9 and current_time.minute == 0:
                            should_send = True
                    
                    elif report.schedule == "weekly":
                        # Send on Monday at 9 AM
                        if (current_time.weekday() == 0 and  # Monday
                            current_time.hour == 9 and current_time.minute == 0):
                            should_send = True
                    
                    # Custom cron expressions would be parsed here
                    
                    if should_send:
                        # Generate and send report
                        await self._generate_and_send_report(report)
                        report.last_sent = current_time
                        
                        # Calculate next send time
                        if report.schedule == "hourly":
                            report.next_send = current_time + timedelta(hours=1)
                        elif report.schedule == "daily":
                            report.next_send = current_time + timedelta(days=1)
                        elif report.schedule == "weekly":
                            report.next_send = current_time + timedelta(days=7)
                
            except Exception as e:
                print(f"[Dashboard] Error in report scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _generate_and_send_report(self, report: DashboardReport):
        """Generate and send a dashboard report"""
        print(f"[Dashboard] Generating report: {report.name}")
        
        try:
            # Generate report data
            report_data = await self._generate_report_data(report)
            
            # Format report based on format
            if report.format == "html":
                formatted_report = self._format_html_report(report, report_data)
            elif report.format == "json":
                formatted_report = json.dumps(report_data, indent=2)
            else:
                formatted_report = str(report_data)
            
            # Send report to recipients
            await self._send_report(report, formatted_report)
            
            self.stats["reports_generated"] += 1
            
            print(f"[Dashboard] Report {report.name} sent to {len(report.recipients)} recipients")
            
        except Exception as e:
            print(f"[Dashboard] Failed to generate report {report.name}: {e}")
    
    async def _generate_report_data(self, report: DashboardReport) -> Dict[str, Any]:
        """Generate data for a report"""
        # This would generate comprehensive report data
        # For now, return basic statistics
        
        project_status = self.memory.get_project_status() or {}
        monitoring = project_status.get("monitoring", {})
        
        return {
            "generated_at": datetime.now().isoformat(),
            "time_range": "24h",
            "summary": {
                "system_health": monitoring.get("health_status", {}).get("overall", "unknown"),
                "active_incidents": len(monitoring.get("active_incidents", [])),
                "critical_alerts": monitoring.get("metrics", {}).get("summary", {}).get("critical_alerts", 0),
                "remediations_executed": monitoring.get("remediation_stats", {}).get("remediations_completed", 0)
            },
            "incidents": monitoring.get("incident_history", [])[:10],
            "metrics": monitoring.get("metrics", {}).get("summary", {}),
            "remediations": monitoring.get("active_remediations", [])[:5]
        }
    
    def _format_html_report(self, report: DashboardReport, data: Dict[str, Any]) -> str:
        """Format report as HTML"""
        html =