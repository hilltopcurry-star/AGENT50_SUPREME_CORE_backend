"""
incident_response.py - Incident response coordination engine for Agent 50
Manages complex multi-step incident response with automated runbooks and communication
"""

import asyncio
import time
import json
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# Import existing MemoryManager
from agent50_core.memory.memory_manager import MemoryManager


class IncidentSeverity(Enum):
    """Incident severity levels"""
    SEV1 = "sev1"      # Critical - Service down, data loss, security breach
    SEV2 = "sev2"      # High - Major degradation, partial outage
    SEV3 = "sev3"      # Medium - Performance issues, minor degradation
    SEV4 = "sev4"      # Low - Minor issues, no user impact


class IncidentState(Enum):
    """Incident lifecycle states"""
    DETECTED = "detected"
    TRIAGING = "triaging"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    POST_MORTEM = "post_mortem"
    CLOSED = "closed"


class IncidentSource(Enum):
    """Sources of incidents"""
    ALERT_CORRELATION = "alert_correlation"
    MANUAL_REPORT = "manual_report"
    HEALTH_MONITOR = "health_monitor"
    METRICS_ANOMALY = "metrics_anomaly"
    USER_REPORT = "user_report"
    SECURITY_SCAN = "security_scan"


class CommunicationChannel(Enum):
    """Communication channels for incident updates"""
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    STATUS_PAGE = "status_page"


class ResponseActionType(Enum):
    """Types of response actions"""
    AUTO_REMEDIATE = "auto_remediate"
    MANUAL_INTERVENTION = "manual_intervention"
    ESCALATE_TEAM = "escalate_team"
    COMMUNICATE = "communicate"
    COLLECT_DATA = "collect_data"
    UPDATE_STATUS = "update_status"


@dataclass
class IncidentTimelineEntry:
    """Timeline entry for incident"""
    timestamp: datetime
    action: str
    actor: str  # "system", "user:username", "auto_remediation"
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "actor": self.actor,
            "details": self.details
        }


@dataclass
class ResponseAction:
    """Response action in runbook"""
    id: str
    type: ResponseActionType
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    timeout_minutes: int = 30
    retry_count: int = 1
    depends_on: List[str] = field(default_factory=list)  # Action IDs this depends on


@dataclass
class Runbook:
    """Incident response runbook"""
    id: str
    name: str
    description: str
    severity: IncidentSeverity
    trigger_conditions: List[Dict[str, Any]]
    actions: List[ResponseAction]
    pre_conditions: List[Dict[str, Any]] = field(default_factory=list)
    post_conditions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "actions_count": len(self.actions),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Incident:
    """Incident record"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    state: IncidentState
    source: IncidentSource
    created_at: datetime = field(default_factory=datetime.now)
    detected_at: Optional[datetime] = None
    triaged_at: Optional[datetime] = None
    mitigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Affected components
    affected_services: List[str] = field(default_factory=list)
    affected_users: int = 0
    business_impact: str = "low"
    
    # Related data
    correlation_group_id: Optional[str] = None
    alert_ids: List[str] = field(default_factory=list)
    runbook_id: Optional[str] = None
    
    # Response team
    commander: Optional[str] = None  # Incident commander username
    responders: List[str] = field(default_factory=list)
    
    # Tracking
    timeline: List[IncidentTimelineEntry] = field(default_factory=list)
    action_log: List[Dict[str, Any]] = field(default_factory=list)
    communications: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metrics
    time_to_triage: Optional[int] = None  # seconds
    time_to_mitigate: Optional[int] = None  # seconds
    time_to_resolve: Optional[int] = None  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "state": self.state.value,
            "source": self.source.value,
            "created_at": self.created_at.isoformat(),
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "triaged_at": self.triaged_at.isoformat() if self.triaged_at else None,
            "mitigated_at": self.mitigated_at.isoformat() if self.mitigated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "affected_services": self.affected_services,
            "affected_users": self.affected_users,
            "business_impact": self.business_impact,
            "correlation_group_id": self.correlation_group_id,
            "alert_count": len(self.alert_ids),
            "runbook_id": self.runbook_id,
            "commander": self.commander,
            "responder_count": len(self.responders),
            "timeline_entries": len(self.timeline),
            "action_count": len(self.action_log),
            "communication_count": len(self.communications),
            "time_to_triage": self.time_to_triage,
            "time_to_mitigate": self.time_to_mitigate,
            "time_to_resolve": self.time_to_resolve
        }
    
    def add_timeline_entry(self, action: str, actor: str, details: Dict[str, Any] = None):
        """Add entry to incident timeline"""
        entry = IncidentTimelineEntry(
            timestamp=datetime.now(),
            action=action,
            actor=actor,
            details=details or {}
        )
        self.timeline.append(entry)
        
        # Auto-update state based on certain actions
        if action == "incident_triaged":
            self.state = IncidentState.INVESTIGATING
            self.triaged_at = datetime.now()
            if self.detected_at:
                self.time_to_triage = int((self.triaged_at - self.detected_at).total_seconds())
        
        elif action == "mitigation_completed":
            self.state = IncidentState.RESOLVING
            self.mitigated_at = datetime.now()
            if self.detected_at:
                self.time_to_mitigate = int((self.mitigated_at - self.detected_at).total_seconds())
        
        elif action == "incident_resolved":
            self.state = IncidentState.RESOLVED
            self.resolved_at = datetime.now()
            if self.detected_at:
                self.time_to_resolve = int((self.resolved_at - self.detected_at).total_seconds())


class IncidentResponseCoordinator:
    """
    Incident response coordination engine
    Manages complex multi-step incident response with automated runbooks
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.active_incidents: Dict[str, Incident] = {}
        self.resolved_incidents: Dict[str, Incident] = {}
        self.runbooks: Dict[str, Runbook] = {}
        self.response_lock = threading.Lock()
        self.running = False
        
        # Communication configuration
        self.communication_config = {
            "slack_webhook": None,
            "email_smtp_server": None,
            "email_smtp_port": 587,
            "email_from": "incidents@agent50.local",
            "email_recipients": [],
            "status_page_url": None,
            "status_page_api_key": None,
            "pagerduty_api_key": None
        }
        
        # Response team configuration
        self.response_teams = {
            "platform": ["team-platform@example.com"],
            "database": ["team-database@example.com"],
            "security": ["team-security@example.com"],
            "oncall": ["oncall@example.com"]
        }
        
        # Statistics
        self.stats = {
            "incidents_created": 0,
            "incidents_resolved": 0,
            "incidents_escalated": 0,
            "runbooks_executed": 0,
            "auto_remediations_triggered": 0,
            "communications_sent": 0,
            "avg_time_to_triage": 0,
            "avg_time_to_resolve": 0
        }
        
        # Load runbooks and configuration
        self._load_configuration()
        self._load_default_runbooks()
        
        print(f"[IncidentResponse] Loaded {len(self.runbooks)} runbooks")
    
    def _load_configuration(self):
        """Load incident response configuration from memory"""
        try:
            project_status = self.memory.get_project_status() or {}
            monitoring_config = project_status.get("monitoring", {})
            
            # Load communication config
            if "incident_response_config" in monitoring_config:
                config = monitoring_config["incident_response_config"]
                self.communication_config.update(config.get("communication", {}))
                self.response_teams.update(config.get("response_teams", {}))
            
            # Load runbooks
            if "incident_runbooks" in monitoring_config:
                runbooks_data = monitoring_config["incident_runbooks"]
                for runbook_id, runbook_data in runbooks_data.items():
                    try:
                        runbook = self._create_runbook_from_dict(runbook_data)
                        self.runbooks[runbook_id] = runbook
                    except Exception as e:
                        print(f"[IncidentResponse] Failed to load runbook {runbook_id}: {e}")
            
            print(f"[IncidentResponse] Configuration loaded")
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to load configuration: {e}")
    
    def _load_default_runbooks(self):
        """Load default incident response runbooks"""
        if self.runbooks:
            return  # Already loaded runbooks
        
        default_runbooks = {
            "sev1_service_outage": Runbook(
                id="sev1_service_outage",
                name="SEV1 Service Outage",
                description="Response to critical service outage affecting all users",
                severity=IncidentSeverity.SEV1,
                trigger_conditions=[
                    {"type": "service_unavailable", "services": ">=2", "duration": ">2m"},
                    {"type": "error_rate", "rate": ">50%", "duration": ">1m"}
                ],
                actions=[
                    ResponseAction(
                        id="declare_incident",
                        type=ResponseActionType.COMMUNICATE,
                        name="Declare Incident",
                        description="Formally declare SEV1 incident and notify teams",
                        parameters={
                            "channels": ["slack", "email", "pagerduty"],
                            "message_template": "SEV1 Incident declared: {incident_title}",
                            "escalate_to": ["oncall", "platform", "management"]
                        }
                    ),
                    ResponseAction(
                        id="appoint_commander",
                        type=ResponseActionType.ESCALATE_TEAM,
                        name="Appoint Incident Commander",
                        description="Appoint incident commander and establish command structure",
                        parameters={
                            "team": "oncall",
                            "role": "incident_commander"
                        }
                    ),
                    ResponseAction(
                        id="collect_diagnostics",
                        type=ResponseActionType.COLLECT_DATA,
                        name="Collect Diagnostics",
                        description="Collect logs, metrics, and diagnostics for investigation",
                        parameters={
                            "data_sources": ["logs", "metrics", "tracing", "database"],
                            "time_range": "last_15_minutes"
                        },
                        depends_on=["declare_incident"]
                    ),
                    ResponseAction(
                        id="attempt_auto_remediation",
                        type=ResponseActionType.AUTO_REMEDIATE,
                        name="Attempt Auto-Remediation",
                        description="Trigger auto-remediation for known issues",
                        parameters={
                            "remediation_types": ["restart_service", "rollback_deployment", "scale_resources"],
                            "max_attempts": 2
                        },
                        depends_on=["collect_diagnostics"]
                    ),
                    ResponseAction(
                        id="update_status_page",
                        type=ResponseActionType.UPDATE_STATUS,
                        name="Update Status Page",
                        description="Update public status page with incident information",
                        parameters={
                            "status": "major_outage",
                            "message": "Investigating service outage"
                        },
                        depends_on=["declare_incident"]
                    )
                ]
            ),
            "sev2_performance_degradation": Runbook(
                id="sev2_performance_degradation",
                name="SEV2 Performance Degradation",
                description="Response to significant performance degradation",
                severity=IncidentSeverity.SEV2,
                trigger_conditions=[
                    {"type": "latency_increase", "percent": ">200%", "duration": ">5m"},
                    {"type": "error_rate", "rate": ">10%", "duration": ">5m"}
                ],
                actions=[
                    ResponseAction(
                        id="notify_team",
                        type=ResponseActionType.COMMUNICATE,
                        name="Notify Response Team",
                        description="Notify platform team of performance issues",
                        parameters={
                            "channels": ["slack"],
                            "message_template": "SEV2 Performance issue: {incident_title}",
                            "team": "platform"
                        }
                    ),
                    ResponseAction(
                        id="analyze_root_cause",
                        type=ResponseActionType.COLLECT_DATA,
                        name="Analyze Root Cause",
                        description="Collect performance metrics and identify bottlenecks",
                        parameters={
                            "metrics": ["cpu", "memory", "database", "cache", "network"],
                            "comparison_period": "last_hour"
                        }
                    ),
                    ResponseAction(
                        id="scale_resources",
                        type=ResponseActionType.AUTO_REMEDIATE,
                        name="Scale Resources",
                        description="Scale up resources to handle load",
                        parameters={
                            "scale_type": "vertical",
                            "cpu_increment": 0.5,
                            "memory_increment": "1Gi"
                        },
                        depends_on=["analyze_root_cause"]
                    ),
                    ResponseAction(
                        id="update_status",
                        type=ResponseActionType.UPDATE_STATUS,
                        name="Update Status",
                        description="Update status page with degradation notice",
                        parameters={
                            "status": "degraded_performance",
                            "message": "Investigating performance issues"
                        }
                    )
                ]
            ),
            "sev3_partial_outage": Runbook(
                id="sev3_partial_outage",
                name="SEV3 Partial Outage",
                description="Response to partial service outage affecting some users",
                severity=IncidentSeverity.SEV3,
                trigger_conditions=[
                    {"type": "service_unavailable", "services": "1", "duration": ">5m"},
                    {"type": "regional_outage", "region": "any", "duration": ">5m"}
                ],
                actions=[
                    ResponseAction(
                        id="notify_platform",
                        type=ResponseActionType.COMMUNICATE,
                        name="Notify Platform Team",
                        description="Notify platform team of partial outage",
                        parameters={
                            "channels": ["slack"],
                            "team": "platform"
                        }
                    ),
                    ResponseAction(
                        id="check_dependencies",
                        type=ResponseActionType.COLLECT_DATA,
                        name="Check Dependencies",
                        description="Check dependent services and external APIs",
                        parameters={
                            "dependencies": ["database", "cache", "external_apis"],
                            "timeout": 30
                        }
                    ),
                    ResponseAction(
                        id="failover_if_possible",
                        type=ResponseActionType.MANUAL_INTERVENTION,
                        name="Failover if Possible",
                        description="Failover to backup region or instance",
                        parameters={
                            "action": "failover",
                            "target": "affected_service"
                        },
                        depends_on=["check_dependencies"]
                    )
                ]
            ),
            "database_connection_issues": Runbook(
                id="database_connection_issues",
                name="Database Connection Issues",
                description="Response to database connectivity or performance issues",
                severity=IncidentSeverity.SEV2,
                trigger_conditions=[
                    {"type": "database_connections", "percent": ">90", "duration": ">2m"},
                    {"type": "database_latency", "latency": ">500ms", "duration": ">2m"}
                ],
                actions=[
                    ResponseAction(
                        id="notify_database_team",
                        type=ResponseActionType.ESCALATE_TEAM,
                        name="Notify Database Team",
                        description="Immediately notify database team",
                        parameters={
                            "team": "database",
                            "urgency": "high"
                        }
                    ),
                    ResponseAction(
                        id="kill_idle_connections",
                        type=ResponseActionType.AUTO_REMEDIATE,
                        name="Kill Idle Connections",
                        description="Kill idle database connections to free up pool",
                        parameters={
                            "action": "kill_idle_connections",
                            "idle_timeout": 300
                        }
                    ),
                    ResponseAction(
                        id="increase_connection_pool",
                        type=ResponseActionType.AUTO_REMEDIATE,
                        name="Increase Connection Pool",
                        description="Increase database connection pool size",
                        parameters={
                            "increment": 20,
                            "max_connections": 200
                        },
                        depends_on=["kill_idle_connections"]
                    ),
                    ResponseAction(
                        id="check_replica_health",
                        type=ResponseActionType.COLLECT_DATA,
                        name="Check Replica Health",
                        description="Check database replica health for possible failover",
                        parameters={
                            "replicas": "all",
                            "health_metrics": ["lag", "connections", "cpu"]
                        }
                    )
                ]
            )
        }
        
        for runbook_id, runbook in default_runbooks.items():
            self.runbooks[runbook_id] = runbook
    
    def _create_runbook_from_dict(self, data: Dict[str, Any]) -> Runbook:
        """Create Runbook object from dictionary"""
        actions = []
        for action_data in data.get("actions", []):
            action = ResponseAction(
                id=action_data["id"],
                type=ResponseActionType(action_data["type"]),
                name=action_data["name"],
                description=action_data["description"],
                parameters=action_data.get("parameters", {}),
                conditions=action_data.get("conditions", []),
                timeout_minutes=action_data.get("timeout_minutes", 30),
                retry_count=action_data.get("retry_count", 1),
                depends_on=action_data.get("depends_on", [])
            )
            actions.append(action)
        
        return Runbook(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            severity=IncidentSeverity(data["severity"]),
            trigger_conditions=data["trigger_conditions"],
            actions=actions,
            pre_conditions=data.get("pre_conditions", []),
            post_conditions=data.get("post_conditions", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )
    
    async def start(self):
        """Start the incident response coordinator"""
        if self.running:
            print("[IncidentResponse] Coordinator already running")
            return
        
        print("[IncidentResponse] Starting incident response coordinator...")
        self.running = True
        
        # Start monitoring for incidents
        asyncio.create_task(self._monitor_for_incidents())
        
        # Start periodic tasks
        asyncio.create_task(self._update_active_incidents())
        asyncio.create_task(self._cleanup_old_incidents())
        
        print("[IncidentResponse] Coordinator started")
    
    async def stop(self):
        """Stop the incident response coordinator"""
        if not self.running:
            return
        
        print("[IncidentResponse] Stopping incident response coordinator...")
        self.running = False
        
        # Wait for active incident handling to complete
        with self.response_lock:
            active_count = len(self.active_incidents)
            if active_count > 0:
                print(f"[IncidentResponse] {active_count} active incidents will continue running")
        
        print("[IncidentResponse] Coordinator stopped")
    
    async def _monitor_for_incidents(self):
        """Monitor for new incidents from various sources"""
        while self.running:
            try:
                await asyncio.sleep(15)  # Check every 15 seconds
                
                # Check for new incidents from correlation engine
                await self._check_correlation_incidents()
                
                # Check for manual incident reports
                await self._check_manual_incidents()
                
                # Check for health monitor incidents
                await self._check_health_incidents()
                
            except Exception as e:
                print(f"[IncidentResponse] Error monitoring for incidents: {e}")
                await asyncio.sleep(60)
    
    async def _check_correlation_incidents(self):
        """Check for incidents from alert correlation engine"""
        try:
            project_status = self.memory.get_project_status() or {}
            monitoring = project_status.get("monitoring", {})
            
            # Check for escalated alerts
            escalations = monitoring.get("escalations", [])
            for escalation in escalations:
                if escalation.get("status") == "open":
                    # Check if incident already exists for this correlation group
                    correlation_group_id = escalation.get("correlation_group_id")
                    if correlation_group_id:
                        incident_exists = any(
                            inc.correlation_group_id == correlation_group_id
                            for inc in self.active_incidents.values()
                        )
                        
                        if not incident_exists:
                            # Create incident from escalation
                            await self._create_incident_from_escalation(escalation)
            
            # Check for remediation requests that might indicate incidents
            remediation_requests = monitoring.get("remediation_requests", [])
            for request in remediation_requests:
                correlation_group_id = request.get("correlation_group_id")
                if correlation_group_id and correlation_group_id.startswith("corr_"):
                    # Check if this is a high-priority remediation that needs incident
                    priority_score = request.get("priority_score", 0)
                    if priority_score >= 7.0:  # High priority
                        incident_exists = any(
                            inc.correlation_group_id == correlation_group_id
                            for inc in self.active_incidents.values()
                        )
                        
                        if not incident_exists:
                            await self._create_incident_from_remediation(request)
        
        except Exception as e:
            print(f"[IncidentResponse] Error checking correlation incidents: {e}")
    
    async def _check_manual_incidents(self):
        """Check for manual incident reports"""
        try:
            project_status = self.memory.get_project_status() or {}
            monitoring = project_status.get("monitoring", {})
            
            # Check for manual incident reports
            if "manual_incident_reports" in monitoring:
                reports = monitoring["manual_incident_reports"]
                for report in reports:
                    if report.get("status") == "pending":
                        await self._create_incident_from_manual_report(report)
                        # Mark as processed
                        report["status"] = "processed"
                
                # Update memory
                self.memory.update_project_status(
                    platform=project_status.get("platform", "unknown"),
                    monitoring=monitoring
                )
        
        except Exception as e:
            print(f"[IncidentResponse] Error checking manual incidents: {e}")
    
    async def _check_health_incidents(self):
        """Check for incidents from health monitor"""
        try:
            project_status = self.memory.get_project_status() or {}
            monitoring = project_status.get("monitoring", {})
            
            # Check for critical health status
            health_status = monitoring.get("health_status", {})
            if health_status.get("overall") == "critical":
                # Check if we already have an active incident for this
                has_critical_incident = any(
                    inc.severity == IncidentSeverity.SEV1
                    for inc in self.active_incidents.values()
                )
                
                if not has_critical_incident:
                    await self._create_health_incident(health_status)
        
        except Exception as e:
            print(f"[IncidentResponse] Error checking health incidents: {e}")
    
    async def _create_incident_from_escalation(self, escalation: Dict[str, Any]):
        """Create incident from escalation"""
        try:
            correlation_group_id = escalation.get("correlation_group_id")
            severity_str = escalation.get("severity", "high")
            alerts = escalation.get("alerts", [])
            
            # Map severity
            severity_map = {
                "critical": IncidentSeverity.SEV1,
                "high": IncidentSeverity.SEV2,
                "medium": IncidentSeverity.SEV3,
                "low": IncidentSeverity.SEV4
            }
            severity = severity_map.get(severity_str, IncidentSeverity.SEV3)
            
            # Extract affected services from alerts
            affected_services = set()
            affected_users = 0
            for alert in alerts:
                component = alert.get("component", "")
                if ":" in component:
                    service = component.split(":")[0]
                    affected_services.add(service)
                
                affected_users = max(affected_users, alert.get("affected_users", 0))
            
            # Create incident
            incident_id = f"inc_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            incident = Incident(
                id=incident_id,
                title=escalation.get("title", "Unnamed Incident"),
                description=escalation.get("description", ""),
                severity=severity,
                state=IncidentState.DETECTED,
                source=IncidentSource.ALERT_CORRELATION,
                detected_at=datetime.now(),
                affected_services=list(affected_services),
                affected_users=affected_users,
                correlation_group_id=correlation_group_id,
                alert_ids=[alert.get("id") for alert in alerts if alert.get("id")]
            )
            
            # Add to timeline
            incident.add_timeline_entry(
                action="incident_detected",
                actor="alert_correlation",
                details={"escalation_id": escalation.get("id")}
            )
            
            # Store incident
            with self.response_lock:
                self.active_incidents[incident_id] = incident
            
            self.stats["incidents_created"] += 1
            
            # Find and execute appropriate runbook
            runbook = self._select_runbook_for_incident(incident)
            if runbook:
                incident.runbook_id = runbook.id
                incident.add_timeline_entry(
                    action="runbook_selected",
                    actor="system",
                    details={"runbook_id": runbook.id, "runbook_name": runbook.name}
                )
                
                # Execute runbook
                asyncio.create_task(self._execute_runbook(incident, runbook))
            
            # Send initial communications
            asyncio.create_task(self._send_incident_communications(incident, "detected"))
            
            # Update memory
            await self._update_incident_in_memory(incident)
            
            print(f"[IncidentResponse] Created incident {incident_id} from escalation")
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to create incident from escalation: {e}")
    
    async def _create_incident_from_remediation(self, remediation: Dict[str, Any]):
        """Create incident from high-priority remediation request"""
        try:
            correlation_group_id = remediation.get("correlation_group_id")
            alerts = remediation.get("alerts", [])
            priority_score = remediation.get("priority_score", 0)
            
            # Determine severity from priority score
            if priority_score >= 9.0:
                severity = IncidentSeverity.SEV1
            elif priority_score >= 7.0:
                severity = IncidentSeverity.SEV2
            elif priority_score >= 5.0:
                severity = IncidentSeverity.SEV3
            else:
                severity = IncidentSeverity.SEV4
            
            # Create incident
            incident_id = f"inc_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            incident = Incident(
                id=incident_id,
                title=f"Auto-Remediation Triggered: {remediation.get('root_cause', 'Unknown')}",
                description=f"High-priority auto-remediation triggered. Suggested action: {remediation.get('suggested_action', 'None')}",
                severity=severity,
                state=IncidentState.DETECTED,
                source=IncidentSource.ALERT_CORRELATION,
                detected_at=datetime.now(),
                correlation_group_id=correlation_group_id
            )
            
            incident.add_timeline_entry(
                action="incident_detected",
                actor="auto_remediation",
                details={"priority_score": priority_score}
            )
            
            # Store incident
            with self.response_lock:
                self.active_incidents[incident_id] = incident
            
            self.stats["incidents_created"] += 1
            
            # Update memory
            await self._update_incident_in_memory(incident)
            
            print(f"[IncidentResponse] Created incident {incident_id} from remediation request")
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to create incident from remediation: {e}")
    
    async def _create_incident_from_manual_report(self, report: Dict[str, Any]):
        """Create incident from manual report"""
        try:
            incident_id = f"inc_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Determine severity from report
            severity_str = report.get("severity", "medium").lower()
            severity_map = {
                "critical": IncidentSeverity.SEV1,
                "high": IncidentSeverity.SEV2,
                "medium": IncidentSeverity.SEV3,
                "low": IncidentSeverity.SEV4
            }
            severity = severity_map.get(severity_str, IncidentSeverity.SEV3)
            
            incident = Incident(
                id=incident_id,
                title=report.get("title", "Manual Incident Report"),
                description=report.get("description", ""),
                severity=severity,
                state=IncidentState.DETECTED,
                source=IncidentSource.MANUAL_REPORT,
                detected_at=datetime.now(),
                affected_users=report.get("affected_users", 0),
                business_impact=report.get("business_impact", "low"),
                commander=report.get("reporter")
            )
            
            incident.add_timeline_entry(
                action="incident_reported",
                actor=f"user:{report.get('reporter', 'unknown')}",
                details={"report_id": report.get("id")}
            )
            
            # Store incident
            with self.response_lock:
                self.active_incidents[incident_id] = incident
            
            self.stats["incidents_created"] += 1
            
            # Find and execute appropriate runbook
            runbook = self._select_runbook_for_incident(incident)
            if runbook:
                incident.runbook_id = runbook.id
                asyncio.create_task(self._execute_runbook(incident, runbook))
            
            # Send initial communications
            asyncio.create_task(self._send_incident_communications(incident, "detected"))
            
            # Update memory
            await self._update_incident_in_memory(incident)
            
            print(f"[IncidentResponse] Created incident {incident_id} from manual report")
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to create incident from manual report: {e}")
    
    async def _create_health_incident(self, health_status: Dict[str, Any]):
        """Create incident from critical health status"""
        try:
            incident_id = f"inc_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            incident = Incident(
                id=incident_id,
                title="Critical Health Status Detected",
                description="System health monitoring detected critical status requiring immediate attention",
                severity=IncidentSeverity.SEV1,
                state=IncidentState.DETECTED,
                source=IncidentSource.HEALTH_MONITOR,
                detected_at=datetime.now()
            )
            
            incident.add_timeline_entry(
                action="critical_health_detected",
                actor="health_monitor",
                details={"health_status": health_status}
            )
            
            # Store incident
            with self.response_lock:
                self.active_incidents[incident_id] = incident
            
            self.stats["incidents_created"] += 1
            
            # Execute SEV1 runbook
            runbook = self.runbooks.get("sev1_service_outage")
            if runbook:
                incident.runbook_id = runbook.id
                asyncio.create_task(self._execute_runbook(incident, runbook))
            
            # Send initial communications
            asyncio.create_task(self._send_incident_communications(incident, "detected"))
            
            # Update memory
            await self._update_incident_in_memory(incident)
            
            print(f"[IncidentResponse] Created incident {incident_id} from critical health status")
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to create health incident: {e}")
    
    def _select_runbook_for_incident(self, incident: Incident) -> Optional[Runbook]:
        """Select appropriate runbook for incident"""
        # First, try to match by severity and affected services
        for runbook in self.runbooks.values():
            if runbook.severity == incident.severity:
                # Check if runbook conditions match incident
                if self._runbook_matches_incident(runbook, incident):
                    return runbook
        
        # Fallback: return default runbook for severity
        severity_map = {
            IncidentSeverity.SEV1: "sev1_service_outage",
            IncidentSeverity.SEV2: "sev2_performance_degradation",
            IncidentSeverity.SEV3: "sev3_partial_outage",
            IncidentSeverity.SEV4: None  # No default for SEV4
        }
        
        runbook_id = severity_map.get(incident.severity)
        return self.runbooks.get(runbook_id) if runbook_id else None
    
    def _runbook_matches_incident(self, runbook: Runbook, incident: Incident) -> bool:
        """Check if runbook matches incident conditions"""
        if not runbook.trigger_conditions:
            return True
        
        # For now, simple matching based on severity
        # In production, would evaluate all trigger conditions
        return True
    
    async def _execute_runbook(self, incident: Incident, runbook: Runbook):
        """Execute runbook for incident"""
        print(f"[IncidentResponse] Executing runbook {runbook.id} for incident {incident.id}")
        
        incident.add_timeline_entry(
            action="runbook_execution_started",
            actor="system",
            details={"runbook_id": runbook.id, "action_count": len(runbook.actions)}
        )
        
        self.stats["runbooks_executed"] += 1
        
        # Execute actions in order, respecting dependencies
        executed_actions = set()
        
        while len(executed_actions) < len(runbook.actions):
            action_executed = False
            
            for action in runbook.actions:
                if action.id in executed_actions:
                    continue
                
                # Check if all dependencies are satisfied
                dependencies_satisfied = all(
                    dep in executed_actions for dep in action.depends_on
                )
                
                if dependencies_satisfied:
                    # Execute action
                    action_result = await self._execute_response_action(incident, action)
                    
                    # Log action execution
                    incident.action_log.append({
                        "action_id": action.id,
                        "action_name": action.name,
                        "type": action.type.value,
                        "result": action_result,
                        "executed_at": datetime.now().isoformat()
                    })
                    
                    executed_actions.add(action.id)
                    action_executed = True
                    
                    # Add to timeline
                    incident.add_timeline_entry(
                        action=f"runbook_action_executed",
                        actor="system",
                        details={
                            "action_id": action.id,
                            "action_name": action.name,
                            "result": "success" if action_result.get("success") else "failed"
                        }
                    )
                    
                    # Update incident in memory
                    await self._update_incident_in_memory(incident)
                    
                    # If action failed, handle accordingly
                    if not action_result.get("success", False) and action.retry_count > 0:
                        await self._retry_action(incident, action, action_result)
            
            if not action_executed:
                # Circular dependency or no actions can be executed
                print(f"[IncidentResponse] No actions can be executed for incident {incident.id}")
                break
        
        incident.add_timeline_entry(
            action="runbook_execution_completed",
            actor="system",
            details={"actions_executed": len(executed_actions)}
        )
        
        print(f"[IncidentResponse] Runbook execution completed for incident {incident.id}")
    
    async def _execute_response_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute a response action"""
        print(f"[IncidentResponse] Executing action {action.id}: {action.name}")
        
        result = {
            "action_id": action.id,
            "action_name": action.name,
            "type": action.type.value,
            "started_at": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            if action.type == ResponseActionType.AUTO_REMEDIATE:
                result.update(await self._execute_auto_remediate_action(incident, action))
            
            elif action.type == ResponseActionType.MANUAL_INTERVENTION:
                result.update(await self._execute_manual_intervention_action(incident, action))
            
            elif action.type == ResponseActionType.ESCALATE_TEAM:
                result.update(await self._execute_escalate_action(incident, action))
            
            elif action.type == ResponseActionType.COMMUNICATE:
                result.update(await self._execute_communication_action(incident, action))
            
            elif action.type == ResponseActionType.COLLECT_DATA:
                result.update(await self._execute_collect_data_action(incident, action))
            
            elif action.type == ResponseActionType.UPDATE_STATUS:
                result.update(await self._execute_update_status_action(incident, action))
            
            else:
                result["error"] = f"Unknown action type: {action.type}"
        
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
        
        result["completed_at"] = datetime.now().isoformat()
        return result
    
    async def _execute_auto_remediate_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute auto-remediation action"""
        remediation_types = action.parameters.get("remediation_types", [])
        max_attempts = action.parameters.get("max_attempts", 2)
        
        # This would trigger the auto-remediation engine
        # For now, simulate success
        self.stats["auto_remediations_triggered"] += 1
        
        return {
            "success": True,
            "message": f"Triggered auto-remediation for {', '.join(remediation_types)}",
            "details": {"attempts": 1, "max_attempts": max_attempts}
        }
    
    async def _execute_manual_intervention_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute manual intervention action"""
        intervention_type = action.parameters.get("action")
        target = action.parameters.get("target")
        
        # Notify human responders
        await self._send_manual_intervention_notification(incident, action)
        
        return {
            "success": True,
            "message": f"Manual intervention required: {intervention_type} on {target}",
            "details": {"notified": True, "intervention_type": intervention_type}
        }
    
    async def _execute_escalate_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute team escalation action"""
        team = action.parameters.get("team")
        urgency = action.parameters.get("urgency", "medium")
        
        # Get team contact information
        team_contacts = self.response_teams.get(team, [])
        
        if team_contacts:
            # Send escalation notification
            await self._send_escalation_notification(incident, team, team_contacts, urgency)
            
            # Update incident responders
            incident.responders.extend(team_contacts)
            
            # If this is the first escalation, appoint commander
            if action.parameters.get("role") == "incident_commander" and not incident.commander:
                # For now, assign first contact as commander
                incident.commander = team_contacts[0] if team_contacts else None
            
            return {
                "success": True,
                "message": f"Escalated to {team} team ({len(team_contacts)} contacts)",
                "details": {"team": team, "urgency": urgency, "contacts": team_contacts}
            }
        else:
            return {
                "success": False,
                "error": f"Team {team} not found in response teams configuration"
            }
    
    async def _execute_communication_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute communication action"""
        channels = action.parameters.get("channels", [])
        message_template = action.parameters.get("message_template", "{incident_title}")
        escalate_to = action.parameters.get("escalate_to", [])
        
        # Format message
        message = message_template.format(
            incident_title=incident.title,
            incident_id=incident.id,
            severity=incident.severity.value,
            affected_services=", ".join(incident.affected_services)
        )
        
        # Send communications
        sent_channels = []
        for channel in channels:
            try:
                if channel == "slack" and self.communication_config.get("slack_webhook"):
                    await self._send_slack_notification(incident, message)
                    sent_channels.append("slack")
                
                elif channel == "email":
                    recipients = []
                    for team_name in escalate_to:
                        team_contacts = self.response_teams.get(team_name, [])
                        recipients.extend(team_contacts)
                    
                    if recipients:
                        await self._send_email_notification(incident, message, recipients)
                        sent_channels.append("email")
                
                elif channel == "pagerduty" and self.communication_config.get("pagerduty_api_key"):
                    await self._send_pagerduty_notification(incident, message)
                    sent_channels.append("pagerduty")
                
            except Exception as e:
                print(f"[IncidentResponse] Failed to send {channel} notification: {e}")
        
        self.stats["communications_sent"] += len(sent_channels)
        
        return {
            "success": len(sent_channels) > 0,
            "message": f"Sent communications via {', '.join(sent_channels) if sent_channels else 'no channels'}",
            "details": {"channels_attempted": channels, "channels_sent": sent_channels}
        }
    
    async def _execute_collect_data_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute data collection action"""
        data_sources = action.parameters.get("data_sources", [])
        time_range = action.parameters.get("time_range", "last_15_minutes")
        
        # This would collect data from various sources
        # For now, simulate data collection
        collected_data = {}
        
        if "logs" in data_sources:
            collected_data["logs"] = {"status": "collected", "entries": 1000}
        
        if "metrics" in data_sources:
            collected_data["metrics"] = {"status": "collected", "data_points": 500}
        
        if "database" in data_sources:
            collected_data["database"] = {"status": "collected", "queries": 50}
        
        return {
            "success": True,
            "message": f"Collected data from {len(data_sources)} sources",
            "details": {"collected_data": collected_data, "time_range": time_range}
        }
    
    async def _execute_update_status_action(self, incident: Incident, action: ResponseAction) -> Dict[str, Any]:
        """Execute status update action"""
        status = action.parameters.get("status", "investigating")
        message = action.parameters.get("message", "")
        
        # Update status page if configured
        if self.communication_config.get("status_page_url") and self.communication_config.get("status_page_api_key"):
            try:
                await self._update_status_page(incident, status, message)
                
                # Record communication
                incident.communications.append({
                    "channel": CommunicationChannel.STATUS_PAGE.value,
                    "status": status,
                    "message": message,
                    "sent_at": datetime.now().isoformat()
                })
                
                return {
                    "success": True,
                    "message": f"Updated status page to '{status}'",
                    "details": {"status": status, "message": message}
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to update status page: {str(e)}",
                    "details": {"status": status}
                }
        else:
            return {
                "success": True,
                "message": "Status page update simulated (no configuration)",
                "details": {"status": status, "message": message}
            }
    
    async def _retry_action(self, incident: Incident, action: ResponseAction, previous_result: Dict[str, Any]):
        """Retry a failed action"""
        print(f"[IncidentResponse] Retrying action {action.id} for incident {incident.id}")
        
        # In production, would implement retry logic with backoff
        # For now, just log the retry attempt
        incident.add_timeline_entry(
            action="action_retry_attempted",
            actor="system",
            details={
                "action_id": action.id,
                "action_name": action.name,
                "previous_error": previous_result.get("error"),
                "retry_count": 1
            }
        )
    
    async def _send_incident_communications(self, incident: Incident, stage: str):
        """Send incident communications based on stage"""
        if stage == "detected":
            # Initial detection notifications
            message = f"🚨 Incident {incident.id} detected: {incident.title}\n"
            message += f"Severity: {incident.severity.value.upper()}\n"
            message += f"Affected services: {', '.join(incident.affected_services) if incident.affected_services else 'Unknown'}"
            
            # Send to appropriate channels based on severity
            if incident.severity in [IncidentSeverity.SEV1, IncidentSeverity.SEV2]:
                channels = ["slack", "email"]
                teams = ["oncall", "platform"]
            else:
                channels = ["slack"]
                teams = ["platform"]
            
            # Send notifications
            for channel in channels:
                try:
                    if channel == "slack" and self.communication_config.get("slack_webhook"):
                        await self._send_slack_notification(incident, message)
                    
                    elif channel == "email":
                        recipients = []
                        for team_name in teams:
                            team_contacts = self.response_teams.get(team_name, [])
                            recipients.extend(team_contacts)
                        
                        if recipients:
                            await self._send_email_notification(incident, message, recipients)
                
                except Exception as e:
                    print(f"[IncidentResponse] Failed to send {channel} notification: {e}")
        
        # Record communications
        incident.communications.append({
            "stage": stage,
            "sent_at": datetime.now().isoformat(),
            "channels_attempted": ["slack", "email"] if incident.severity.value in ["sev1", "sev2"] else ["slack"]
        })
    
    async def _send_slack_notification(self, incident: Incident, message: str):
        """Send Slack notification"""
        webhook_url = self.communication_config.get("slack_webhook")
        if not webhook_url:
            return
        
        payload = {
            "text": message,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Incident ID:*\n{incident.id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{incident.severity.value.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*State:*\n{incident.state.value}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Detected:*\n{incident.detected_at.strftime('%H:%M:%S') if incident.detected_at else 'Unknown'}"
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"[IncidentResponse] Slack webhook returned {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[IncidentResponse] Failed to send Slack notification: {e}")
    
    async def _send_email_notification(self, incident: Incident, message: str, recipients: List[str]):
        """Send email notification"""
        smtp_server = self.communication_config.get("email_smtp_server")
        smtp_port = self.communication_config.get("email_smtp_port", 587)
        from_email = self.communication_config.get("email_from", "incidents@agent50.local")
        
        if not smtp_server or not recipients:
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[{incident.severity.value.upper()}] Incident {incident.id}: {incident.title}"
            
            # Create email body
            body = f"""
            Incident Notification
            =====================
            
            {message}
            
            Incident Details:
            - ID: {incident.id}
            - Title: {incident.title}
            - Severity: {incident.severity.value.upper()}
            - State: {incident.state.value}
            - Detected: {incident.detected_at.strftime('%Y-%m-%d %H:%M:%S') if incident.detected_at else 'Unknown'}
            - Affected Services: {', '.join(incident.affected_services) if incident.affected_services else 'Unknown'}
            - Affected Users: {incident.affected_users}
            
            Timeline:
            {chr(10).join(f"  - {entry.timestamp.strftime('%H:%M:%S')}: {entry.action}" for entry in incident.timeline[-5:])}
            
            This is an automated notification from Agent 50 Incident Response System.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (in production, would use async SMTP)
            # For now, simulate sending
            print(f"[IncidentResponse] Would send email to {len(recipients)} recipients")
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to prepare email notification: {e}")
    
    async def _send_pagerduty_notification(self, incident: Incident, message: str):
        """Send PagerDuty notification"""
        api_key = self.communication_config.get("pagerduty_api_key")
        if not api_key:
            return
        
        # PagerDuty API integration would go here
        # For now, simulate
        print(f"[IncidentResponse] Would send PagerDuty notification for incident {incident.id}")
    
    async def _send_manual_intervention_notification(self, incident: Incident, action: ResponseAction):
        """Send manual intervention notification"""
        message = f"🛠️ Manual intervention required for incident {incident.id}\n"
        message += f"Action: {action.name}\n"
        message += f"Description: {action.description}\n"
        
        if incident.commander:
            message += f"Incident Commander: {incident.commander}"
        
        # Send to incident commander and responders
        recipients = []
        if incident.commander:
            recipients.append(incident.commander)
        recipients.extend(incident.responders)
        
        if recipients:
            await self._send_email_notification(incident, message, recipients)
    
    async def _send_escalation_notification(self, incident: Incident, team: str, contacts: List[str], urgency: str):
        """Send escalation notification"""
        message = f"📢 Escalation to {team} team for incident {incident.id}\n"
        message += f"Urgency: {urgency.upper()}\n"
        message += f"Title: {incident.title}\n"
        message += f"Severity: {incident.severity.value.upper()}"
        
        await self._send_email_notification(incident, message, contacts)
    
    async def _update_status_page(self, incident: Incident, status: str, message: str):
        """Update status page"""
        url = self.communication_config.get("status_page_url")
        api_key = self.communication_config.get("status_page_api_key")
        
        if not url or not api_key:
            return
        
        # Status page API integration would go here
        # For now, simulate
        print(f"[IncidentResponse] Would update status page for incident {incident.id}")
    
    async def _update_incident_in_memory(self, incident: Incident):
        """Update incident in memory"""
        try:
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            # Update active incidents
            if "active_incidents" not in project_status["monitoring"]:
                project_status["monitoring"]["active_incidents"] = []
            
            active_incidents = project_status["monitoring"]["active_incidents"]
            
            # Find and update or add incident
            incident_index = None
            for i, inc in enumerate(active_incidents):
                if inc.get("id") == incident.id:
                    incident_index = i
                    break
            
            incident_dict = incident.to_dict()
            if incident_index is not None:
                active_incidents[incident_index] = incident_dict
            else:
                active_incidents.append(incident_dict)
            
            # Keep only last 20 active incidents
            if len(active_incidents) > 20:
                project_status["monitoring"]["active_incidents"] = active_incidents[-20:]
            
            # Add to incident history if resolved or closed
            if incident.state in [IncidentState.RESOLVED, IncidentState.CLOSED, IncidentState.POST_MORTEM]:
                if "incident_history" not in project_status["monitoring"]:
                    project_status["monitoring"]["incident_history"] = []
                
                project_status["monitoring"]["incident_history"].append(incident_dict)
                
                # Keep only last 100 history entries
                if len(project_status["monitoring"]["incident_history"]) > 100:
                    project_status["monitoring"]["incident_history"] = \
                        project_status["monitoring"]["incident_history"][-100:]
                
                # Remove from active incidents
                project_status["monitoring"]["active_incidents"] = [
                    inc for inc in project_status["monitoring"]["active_incidents"]
                    if inc.get("id") != incident.id
                ]
                
                # Update statistics
                self.stats["incidents_resolved"] += 1
                
                # Update average resolution time
                if incident.time_to_resolve:
                    resolved_count = self.stats["incidents_resolved"]
                    old_avg = self.stats["avg_time_to_resolve"]
                    self.stats["avg_time_to_resolve"] = (
                        (old_avg * (resolved_count - 1) + incident.time_to_resolve) / resolved_count
                    ) if resolved_count > 1 else incident.time_to_resolve
            
            # Update statistics
            project_status["monitoring"]["incident_stats"] = self.stats
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
        except Exception as e:
            print(f"[IncidentResponse] Failed to update incident in memory: {e}")
    
    async def _update_active_incidents(self):
        """Periodically update active incidents"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                with self.response_lock:
                    for incident in list(self.active_incidents.values()):
                        # Update incident state if needed
                        if incident.state == IncidentState.DETECTED and not incident.triaged_at:
                            # Check if auto-triaging should happen
                            detect_time = incident.detected_at or incident.created_at
                            time_since_detection = (datetime.now() - detect_time).total_seconds()
                            
                            if time_since_detection > 300:  # 5 minutes
                                # Auto-triage
                                incident.add_timeline_entry(
                                    action="auto_triaged",
                                    actor="system",
                                    details={"reason": "No manual triage within 5 minutes"}
                                )
                        
                        # Update in memory
                        await self._update_incident_in_memory(incident)
                
            except Exception as e:
                print(f"[IncidentResponse] Error updating active incidents: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_old_incidents(self):
        """Clean up old incidents from memory"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff = datetime.now() - timedelta(days=30)  # 30 days
                
                with self.response_lock:
                    # Clean up resolved incidents older than cutoff
                    incidents_to_remove = []
                    for incident_id, incident in self.resolved_incidents.items():
                        if incident.resolved_at and incident.resolved_at < cutoff:
                            incidents_to_remove.append(incident_id)
                    
                    for incident_id in incidents_to_remove:
                        del self.resolved_incidents[incident_id]
                    
                    if incidents_to_remove:
                        print(f"[IncidentResponse] Cleaned up {len(incidents_to_remove)} old incidents")
                
            except Exception as e:
                print(f"[IncidentResponse] Error in cleanup: {e}")
    
    async def create_manual_incident(self, title: str, description: str, severity: str,
                                   affected_services: List[str] = None,
                                   reporter: str = None) -> Dict[str, Any]:
        """Create a manual incident"""
        try:
            # Create incident
            incident_id = f"inc_manual_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            severity_map = {
                "sev1": IncidentSeverity.SEV1,
                "sev2": IncidentSeverity.SEV2,
                "sev3": IncidentSeverity.SEV3,
                "sev4": IncidentSeverity.SEV4
            }
            incident_severity = severity_map.get(severity.lower(), IncidentSeverity.SEV3)
            
            incident = Incident(
                id=incident_id,
                title=title,
                description=description,
                severity=incident_severity,
                state=IncidentState.DETECTED,
                source=IncidentSource.MANUAL_REPORT,
                detected_at=datetime.now(),
                affected_services=affected_services or [],
                commander=reporter
            )
            
            incident.add_timeline_entry(
                action="incident_created_manually",
                actor=f"user:{reporter or 'unknown'}",
                details={"title": title, "severity": severity}
            )
            
            # Store incident
            with self.response_lock:
                self.active_incidents[incident_id] = incident
            
            self.stats["incidents_created"] += 1
            
            # Find and execute appropriate runbook
            runbook = self._select_runbook_for_incident(incident)
            if runbook:
                incident.runbook_id = runbook.id
                asyncio.create_task(self._execute_runbook(incident, runbook))
            
            # Send initial communications
            asyncio.create_task(self._send_incident_communications(incident, "detected"))
            
            # Update memory
            await self._update_incident_in_memory(incident)
            
            return {
                "success": True,
                "incident_id": incident_id,
                "message": f"Incident {incident_id} created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_incident_state(self, incident_id: str, new_state: str,
                                  actor: str, notes: str = None) -> Dict[str, Any]:
        """Update incident state"""
        with self.response_lock:
            incident = self.active_incidents.get(incident_id)
            if not incident:
                # Check resolved incidents
                incident = self.resolved_incidents.get(incident_id)
            
            if not incident:
                return {
                    "success": False,
                    "error": f"Incident {incident_id} not found"
                }
            
            # Update state
            try:
                new_state_enum = IncidentState(new_state)
                
                # Add timeline entry
                details = {"old_state": incident.state.value, "new_state": new_state}
                if notes:
                    details["notes"] = notes
                
                incident.add_timeline_entry(
                    action=f"state_changed_to_{new_state}",
                    actor=f"user:{actor}",
                    details=details
                )
                
                # Update incident state
                incident.state = new_state_enum
                
                # Set timestamps based on state
                if new_state == "triaging" and not incident.triaged_at:
                    incident.triaged_at = datetime.now()
                    if incident.detected_at:
                        incident.time_to_triage = int((incident.triaged_at - incident.detected_at).total_seconds())
                
                elif new_state == "resolved" and not incident.resolved_at:
                    incident.resolved_at = datetime.now()
                    if incident.detected_at:
                        incident.time_to_resolve = int((incident.resolved_at - incident.detected_at).total_seconds())
                    
                    # Send resolution notifications
                    asyncio.create_task(self._send_incident_communications(incident, "resolved"))
                
                elif new_state == "closed" and not incident.closed_at:
                    incident.closed_at = datetime.now()
                
                # Update in memory
                await self._update_incident_in_memory(incident)
                
                return {
                    "success": True,
                    "incident_id": incident_id,
                    "new_state": new_state,
                    "message": f"Incident {incident_id} state updated to {new_state}"
                }
                
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid state: {new_state}"
                }
    
    async def add_incident_comment(self, incident_id: str, comment: str,
                                 author: str) -> Dict[str, Any]:
        """Add comment to incident"""
        with self.response_lock:
            incident = self.active_incidents.get(incident_id)
            if not incident:
                incident = self.resolved_incidents.get(incident_id)
            
            if not incident:
                return {
                    "success": False,
                    "error": f"Incident {incident_id} not found"
                }
            
            # Add timeline entry
            incident.add_timeline_entry(
                action="comment_added",
                actor=f"user:{author}",
                details={"comment": comment[:500]}  # Limit comment length
            )
            
            # Update in memory
            await self._update_incident_in_memory(incident)
            
            return {
                "success": True,
                "incident_id": incident_id,
                "message": "Comment added to incident"
            }
    
    async def get_active_incidents(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active incidents, optionally filtered by severity"""
        with self.response_lock:
            incidents = list(self.active_incidents.values())
            
            if severity:
                try:
                    severity_enum = IncidentSeverity(severity)
                    incidents = [inc for inc in incidents if inc.severity == severity_enum]
                except ValueError:
                    pass
            
            return [incident.to_dict() for incident in incidents]
    
    async def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an incident"""
        with self.response_lock:
            incident = self.active_incidents.get(incident_id)
            if not incident:
                incident = self.resolved_incidents.get(incident_id)
            
            if not incident:
                return None
            
            result = incident.to_dict()
            
            # Add detailed timeline
            result["detailed_timeline"] = [
                entry.to_dict() for entry in incident.timeline
            ]
            
            # Add action log
            result["action_log"] = incident.action_log
            
            # Add communications
            result["communications"] = incident.communications
            
            return result
    
    async def get_incident_stats(self) -> Dict[str, Any]:
        """Get incident statistics"""
        with self.response_lock:
            active_by_severity = defaultdict(int)
            for incident in self.active_incidents.values():
                active_by_severity[incident.severity.value] += 1
            
            return {
                "timestamp": datetime.now().isoformat(),
                "active_incidents": len(self.active_incidents),
                "active_by_severity": dict(active_by_severity),
                "resolved_incidents": len(self.resolved_incidents),
                "statistics": self.stats,
                "runbooks_loaded": len(self.runbooks)
            }
    
    async def generate_post_mortem(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Generate post-mortem report for incident"""
        with self.response_lock:
            incident = self.resolved_incidents.get(incident_id)
            if not incident:
                # Check active incidents
                incident = self.active_incidents.get(incident_id)
            
            if not incident or incident.state != IncidentState.RESOLVED:
                return None
            
            # Generate post-mortem report
            post_mortem = {
                "incident_id": incident.id,
                "title": incident.title,
                "severity": incident.severity.value,
                "timeline": [
                    {
                        "time": entry.timestamp.isoformat(),
                        "action": entry.action,
                        "actor": entry.actor,
                        "details": entry.details
                    }
                    for entry in incident.timeline
                ],
                "root_cause": "To be determined",  # Would be analyzed from timeline
                "impact": {
                    "affected_services": incident.affected_services,
                    "affected_users": incident.affected_users,
                    "business_impact": incident.business_impact,
                    "duration_minutes": incident.time_to_resolve // 60 if incident.time_to_resolve else None
                },
                "actions_taken": incident.action_log,
                "what_went_well": [],
                "what_went_wrong": [],
                "action_items": [],
                "generated_at": datetime.now().isoformat()
            }
            
            # Update incident state
            incident.state = IncidentState.POST_MORTEM
            
            # Add timeline entry
            incident.add_timeline_entry(
                action="post_mortem_generated",
                actor="system",
                details={"report_generated": True}
            )
            
            # Update in memory
            await self._update_incident_in_memory(incident)
            
            return post_mortem


# Example usage
async def example_usage():
    """Example of how to use the incident response coordinator"""
    from agent50_core.memory.memory_manager import MemoryManager
    
    memory = MemoryManager()
    coordinator = IncidentResponseCoordinator(memory)
    
    # Start the coordinator
    await coordinator.start()
    
    # Create a manual incident
    result = await coordinator.create_manual_incident(
        title="Database Performance Issues",
        description="Users reporting slow database queries",
        severity="sev2",
        affected_services=["database", "api_gateway"],
        reporter="admin@example.com"
    )
    
    print(f"Created incident: {result}")
    
    # Wait a bit
    await asyncio.sleep(5)
    
    # Get active incidents
    active_incidents = await coordinator.get_active_incidents()
    print(f"Active incidents: {len(active_incidents)}")
    
    # Get statistics
    stats = await coordinator.get_incident_stats()
    print(f"Incident stats: {stats}")
    
    # Stop the coordinator
    await coordinator.stop()


if __name__ == "__main__":
    asyncio.run(example_usage())