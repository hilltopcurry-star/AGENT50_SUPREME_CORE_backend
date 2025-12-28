"""
alert_correlator.py - Intelligent alert correlation and routing engine for Agent 50
Reduces alert fatigue through temporal, causal, and similarity-based correlation
Routes alerts to appropriate remediation or human escalation
"""

import asyncio
import time
import json
import hashlib
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import heapq
from collections import defaultdict, deque
import networkx as nx
from memory.memory_manager import MemoryManager

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(Enum):
    """Types of alerts"""
    THRESHOLD = "threshold_exceeded"
    ANOMALY = "statistical_anomaly"
    FAILURE = "component_failure"
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"

class AlertState(Enum):
    """Alert lifecycle states"""
    NEW = "new"
    CORRELATED = "correlated"
    ACKNOWLEDGED = "acknowledged"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class RoutingDestination(Enum):
    """Where to route correlated alerts"""
    AUTO_REMEDIATION = "auto_remediation"
    DEPLOYMENT_ROLLBACK = "deployment_rollback"
    MANUAL_INTERVENTION = "manual_intervention"
    MONITOR_ONLY = "monitor_only"
    ESCALATE_HUMAN = "escalate_human"

@dataclass
class Alert:
    """Single alert instance"""
    id: str
    source: str  # metrics, health_monitor, deployment, etc.
    type: AlertType
    severity: AlertSeverity
    component: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: AlertState = AlertState.NEW
    correlation_id: Optional[str] = None
    fingerprint: Optional[str] = None
    affected_users: int = 0
    business_impact: str = "low"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "source": self.source,
            "type": self.type.value,
            "severity": self.severity.value,
            "component": self.component,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "state": self.state.value,
            "correlation_id": self.correlation_id,
            "fingerprint": self.fingerprint,
            "affected_users": self.affected_users,
            "business_impact": self.business_impact
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create alert from dictionary"""
        return cls(
            id=data["id"],
            source=data["source"],
            type=AlertType(data["type"]),
            severity=AlertSeverity(data["severity"]),
            component=data["component"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            state=AlertState(data.get("state", "new")),
            correlation_id=data.get("correlation_id"),
            fingerprint=data.get("fingerprint"),
            affected_users=data.get("affected_users", 0),
            business_impact=data.get("business_impact", "low")
        )

@dataclass
class CorrelatedAlertGroup:
    """Group of correlated alerts"""
    id: str
    primary_alert: Alert
    correlated_alerts: List[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    state: AlertState = AlertState.NEW
    root_cause: Optional[str] = None
    suggested_action: Optional[str] = None
    routing_destination: Optional[RoutingDestination] = None
    priority_score: float = 0.0
    
    def add_alert(self, alert: Alert):
        """Add alert to correlation group"""
        self.correlated_alerts.append(alert)
        self.updated_at = datetime.now()
        
        # Update priority score
        self._calculate_priority_score()
    
    def _calculate_priority_score(self):
        """Calculate priority score for the group"""
        # Base score from severity
        severity_weights = {
            AlertSeverity.CRITICAL: 10.0,
            AlertSeverity.HIGH: 7.0,
            AlertSeverity.MEDIUM: 4.0,
            AlertSeverity.LOW: 2.0,
            AlertSeverity.INFO: 0.5
        }
        
        # Age penalty (older alerts get lower priority after initial burst)
        age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        age_penalty = min(age_hours * 0.1, 3.0)  # Max 3.0 penalty
        
        # Component criticality
        component_criticality = {
            "database": 3.0,
            "api_gateway": 2.5,
            "authentication": 3.0,
            "payment": 4.0,
            "cache": 1.5,
            "queue": 2.0
        }
        
        # Calculate score
        severity_score = max(severity_weights.get(a.severity, 1.0) for a in [self.primary_alert] + self.correlated_alerts)
        component_score = component_criticality.get(self.primary_alert.component.split(":")[0], 1.0)
        affected_users_score = min(self.primary_alert.affected_users / 1000, 5.0)  # Max 5.0
        
        self.priority_score = (severity_score + component_score + affected_users_score) - age_penalty
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert group to dictionary"""
        return {
            "id": self.id,
            "primary_alert": self.primary_alert.to_dict(),
            "correlated_alerts": [a.to_dict() for a in self.correlated_alerts],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "state": self.state.value,
            "root_cause": self.root_cause,
            "suggested_action": self.suggested_action,
            "routing_destination": self.routing_destination.value if self.routing_destination else None,
            "priority_score": self.priority_score,
            "alert_count": len(self.correlated_alerts) + 1
        }

class AlertCorrelationEngine:
    """
    Intelligent alert correlation engine
    Reduces alert fatigue through temporal, causal, and similarity-based correlation
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.alerts: Dict[str, Alert] = {}  # All alerts by ID
        self.correlation_groups: Dict[str, CorrelatedAlertGroup] = {}
        self.suppression_rules: List[Dict[str, Any]] = []
        self.routing_rules: List[Dict[str, Any]] = []
        
        # Temporal correlation window (seconds)
        self.temporal_window = 300  # 5 minutes
        
        # Causal dependency graph
        self.dependency_graph = nx.DiGraph()
        
        # Alert fingerprint cache for deduplication
        self.fingerprint_cache = {}
        
        # Priority queue for alert processing
        self.priority_queue = []
        
        # Load historical patterns and configuration
        self._load_configuration()
        self._build_dependency_graph()
        
        # Statistics
        self.stats = {
            "alerts_received": 0,
            "alerts_correlated": 0,
            "alerts_suppressed": 0,
            "groups_created": 0,
            "auto_remediated": 0,
            "human_escalations": 0
        }
    
    def _load_configuration(self):
        """Load correlation rules from memory"""
        try:
            # Load from project_status or dedicated correlation_rules.json
            project_status = self.memory.get_project_status() or {}
            
            # Load suppression rules
            suppression_rules = project_status.get("monitoring", {}).get("suppression_rules", [])
            if suppression_rules:
                self.suppression_rules = suppression_rules
            else:
                # Default suppression rules
                self.suppression_rules = self._get_default_suppression_rules()
            
            # Load routing rules
            routing_rules = project_status.get("monitoring", {}).get("routing_rules", [])
            if routing_rules:
                self.routing_rules = routing_rules
            else:
                # Default routing rules
                self.routing_rules = self._get_default_routing_rules()
            
            # Load service dependencies from architecture patterns
            arch_patterns = self.memory.get_architecture_patterns()
            if arch_patterns:
                self._load_service_dependencies(arch_patterns)
            
            print(f"[AlertCorrelator] Loaded {len(self.suppression_rules)} suppression rules "
                  f"and {len(self.routing_rules)} routing rules")
            
        except Exception as e:
            print(f"[AlertCorrelator] Failed to load configuration: {e}")
            # Load defaults
            self.suppression_rules = self._get_default_suppression_rules()
            self.routing_rules = self._get_default_routing_rules()
    
    def _get_default_suppression_rules(self) -> List[Dict[str, Any]]:
        """Get default suppression rules"""
        return [
            {
                "id": "suppress_frequent_healthchecks",
                "condition": {
                    "component": "health_check",
                    "type": "availability",
                    "severity": "low",
                    "frequency": ">10 in 60s"
                },
                "action": "suppress",
                "window_seconds": 300
            },
            {
                "id": "suppress_expected_deployment_errors",
                "condition": {
                    "source": "deployment",
                    "type": "deployment",
                    "during_maintenance": True
                },
                "action": "suppress",
                "window_seconds": 1800
            },
            {
                "id": "suppress_transient_network_errors",
                "condition": {
                    "component_regex": ".*network.*",
                    "type": "availability",
                    "severity": "medium",
                    "auto_resolved": True,
                    "duration": "<30s"
                },
                "action": "suppress",
                "window_seconds": 600
            }
        ]
    
    def _get_default_routing_rules(self) -> List[Dict[str, Any]]:
        """Get default routing rules"""
        return [
            {
                "id": "route_critical_db_to_auto_remediate",
                "condition": {
                    "component": "database",
                    "severity": "critical",
                    "type": ["performance", "availability"]
                },
                "action": "route",
                "destination": "auto_remediation",
                "priority": 1
            },
            {
                "id": "route_deployment_failures_to_rollback",
                "condition": {
                    "source": "deployment",
                    "type": "deployment",
                    "severity": ["critical", "high"]
                },
                "action": "route",
                "destination": "deployment_rollback",
                "priority": 1
            },
            {
                "id": "route_security_to_human",
                "condition": {
                    "type": "security",
                    "severity": ["critical", "high", "medium"]
                },
                "action": "route",
                "destination": "escalate_human",
                "priority": 1
            },
            {
                "id": "route_multi_component_to_human",
                "condition": {
                    "correlated_count": ">=3",
                    "affected_components": ">=2"
                },
                "action": "route",
                "destination": "escalate_human",
                "priority": 2
            },
            {
                "id": "route_high_business_impact",
                "condition": {
                    "business_impact": "high",
                    "affected_users": ">1000"
                },
                "action": "route",
                "destination": "escalate_human",
                "priority": 1
            }
        ]
    
    def _load_service_dependencies(self, arch_patterns: Dict[str, Any]):
        """Load service dependencies from architecture patterns"""
        try:
            # Extract service dependencies
            services = arch_patterns.get("services", {})
            
            for service_name, service_info in services.items():
                self.dependency_graph.add_node(service_name, **service_info)
                
                # Add dependencies
                dependencies = service_info.get("dependencies", [])
                for dep in dependencies:
                    self.dependency_graph.add_edge(service_name, dep)
            
            print(f"[AlertCorrelator] Built dependency graph with {self.dependency_graph.number_of_nodes()} "
                  f"nodes and {self.dependency_graph.number_of_edges()} edges")
            
        except Exception as e:
            print(f"[AlertCorrelator] Failed to build dependency graph: {e}")
    
    def _build_dependency_graph(self):
        """Build default dependency graph if none loaded"""
        if self.dependency_graph.number_of_nodes() == 0:
            # Default service dependencies
            default_services = {
                "web_server": {
                    "type": "web",
                    "criticality": "high",
                    "dependencies": ["api_gateway", "authentication"]
                },
                "api_gateway": {
                    "type": "api",
                    "criticality": "high",
                    "dependencies": ["user_service", "product_service", "order_service"]
                },
                "authentication": {
                    "type": "auth",
                    "criticality": "high",
                    "dependencies": ["database"]
                },
                "user_service": {
                    "type": "service",
                    "criticality": "medium",
                    "dependencies": ["database"]
                },
                "product_service": {
                    "type": "service",
                    "criticality": "medium",
                    "dependencies": ["database", "cache"]
                },
                "order_service": {
                    "type": "service",
                    "criticality": "high",
                    "dependencies": ["database", "payment_service", "inventory_service"]
                },
                "payment_service": {
                    "type": "service",
                    "criticality": "critical",
                    "dependencies": ["database", "external_payment_gateway"]
                },
                "database": {
                    "type": "database",
                    "criticality": "critical",
                    "dependencies": []
                },
                "cache": {
                    "type": "cache",
                    "criticality": "medium",
                    "dependencies": []
                }
            }
            
            for service_name, service_info in default_services.items():
                self.dependency_graph.add_node(service_name, **service_info)
                for dep in service_info.get("dependencies", []):
                    self.dependency_graph.add_edge(service_name, dep)
    
    async def process_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new alert through the correlation engine
        Returns: Processing result with correlation info
        """
        self.stats["alerts_received"] += 1
        
        try:
            # Create Alert object
            alert = self._create_alert_from_data(alert_data)
            
            # Step 1: Check for suppression
            if await self._should_suppress_alert(alert):
                self.stats["alerts_suppressed"] += 1
                alert.state = AlertState.SUPPRESSED
                self._store_alert(alert)
                
                return {
                    "processed": True,
                    "action": "suppressed",
                    "alert_id": alert.id,
                    "reason": "Matches suppression rule",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 2: Generate fingerprint for deduplication
            alert.fingerprint = self._generate_alert_fingerprint(alert)
            
            # Step 3: Check for duplicate alerts
            duplicate_group = await self._check_duplicate_alerts(alert)
            if duplicate_group:
                # Add to existing correlation group
                duplicate_group.add_alert(alert)
                alert.correlation_id = duplicate_group.id
                alert.state = AlertState.CORRELATED
                self._store_alert(alert)
                
                self.stats["alerts_correlated"] += 1
                
                return {
                    "processed": True,
                    "action": "correlated",
                    "alert_id": alert.id,
                    "correlation_group_id": duplicate_group.id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 4: Check for temporal correlation
            temporal_group = await self._check_temporal_correlation(alert)
            if temporal_group:
                # Add to temporal correlation group
                temporal_group.add_alert(alert)
                alert.correlation_id = temporal_group.id
                alert.state = AlertState.CORRELATED
                self._store_alert(alert)
                
                self.stats["alerts_correlated"] += 1
                
                return {
                    "processed": True,
                    "action": "temporally_correlated",
                    "alert_id": alert.id,
                    "correlation_group_id": temporal_group.id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 5: Check for causal correlation
            causal_group = await self._check_causal_correlation(alert)
            if causal_group:
                # Add to causal correlation group
                causal_group.add_alert(alert)
                alert.correlation_id = causal_group.id
                alert.state = AlertState.CORRELATED
                self._store_alert(alert)
                
                self.stats["alerts_correlated"] += 1
                
                return {
                    "processed": True,
                    "action": "causally_correlated",
                    "alert_id": alert.id,
                    "correlation_group_id": causal_group.id,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 6: Create new correlation group
            new_group = self._create_correlation_group(alert)
            alert.correlation_id = new_group.id
            alert.state = AlertState.CORRELATED
            self._store_alert(alert)
            
            self.stats["groups_created"] += 1
            
            # Step 7: Determine routing
            routing_result = await self._determine_routing(new_group)
            new_group.routing_destination = routing_result["destination"]
            new_group.suggested_action = routing_result.get("suggested_action")
            new_group.root_cause = routing_result.get("root_cause")
            
            # Update group
            self.correlation_groups[new_group.id] = new_group
            
            # Step 8: Route to appropriate destination
            await self._route_correlated_group(new_group)
            
            # Step 9: Update memory with correlation results
            await self._update_memory_with_correlation(new_group)
            
            return {
                "processed": True,
                "action": "new_group_created",
                "alert_id": alert.id,
                "correlation_group_id": new_group.id,
                "routing_destination": new_group.routing_destination.value,
                "priority_score": new_group.priority_score,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[AlertCorrelator] Error processing alert: {e}")
            return {
                "processed": False,
                "error": str(e),
                "alert_data": alert_data,
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_alert_from_data(self, alert_data: Dict[str, Any]) -> Alert:
        """Create Alert object from raw alert data"""
        # Generate alert ID if not provided
        alert_id = alert_data.get("id", f"alert_{int(time.time())}_{hash(str(alert_data))[:8]}")
        
        # Parse severity
        severity_str = alert_data.get("severity", "medium").lower()
        severity_map = {
            "critical": AlertSeverity.CRITICAL,
            "high": AlertSeverity.HIGH,
            "medium": AlertSeverity.MEDIUM,
            "low": AlertSeverity.LOW,
            "info": AlertSeverity.INFO
        }
        severity = severity_map.get(severity_str, AlertSeverity.MEDIUM)
        
        # Parse alert type
        type_str = alert_data.get("type", "threshold_exceeded")
        type_map = {
            "threshold_exceeded": AlertType.THRESHOLD,
            "statistical_anomaly": AlertType.ANOMALY,
            "component_failure": AlertType.FAILURE,
            "availability": AlertType.AVAILABILITY,
            "performance": AlertType.PERFORMANCE,
            "security": AlertType.SECURITY,
            "configuration": AlertType.CONFIGURATION,
            "deployment": AlertType.DEPLOYMENT
        }
        alert_type = type_map.get(type_str, AlertType.THRESHOLD)
        
        # Parse timestamp
        timestamp_str = alert_data.get("timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now()
        
        # Extract component from metadata if not directly provided
        component = alert_data.get("component", "unknown")
        if component == "unknown" and "metadata" in alert_data:
            metadata = alert_data["metadata"]
            component = metadata.get("component", metadata.get("metric", "unknown"))
        
        return Alert(
            id=alert_id,
            source=alert_data.get("source", "unknown"),
            type=alert_type,
            severity=severity,
            component=component,
            message=alert_data.get("message", "No message provided"),
            timestamp=timestamp,
            metadata=alert_data.get("metadata", {}),
            affected_users=alert_data.get("affected_users", 0),
            business_impact=alert_data.get("business_impact", "low")
        )
    
    async def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed based on rules"""
        current_time = datetime.now()
        
        for rule in self.suppression_rules:
            try:
                condition = rule["condition"]
                
                # Check if alert matches all conditions
                matches = True
                
                for key, value in condition.items():
                    if key == "component":
                        if alert.component != value:
                            matches = False
                            break
                    
                    elif key == "component_regex":
                        if not re.match(value, alert.component):
                            matches = False
                            break
                    
                    elif key == "type":
                        expected_types = value if isinstance(value, list) else [value]
                        if alert.type.value not in expected_types:
                            matches = False
                            break
                    
                    elif key == "severity":
                        expected_severities = value if isinstance(value, list) else [value]
                        if alert.severity.value not in expected_severities:
                            matches = False
                            break
                    
                    elif key == "source":
                        if alert.source != value:
                            matches = False
                            break
                    
                    elif key == "frequency":
                        # Check alert frequency in time window
                        # Format: ">10 in 60s" or "<5 in 300s"
                        match = re.match(r'([<>]=?)(\d+)\s+in\s+(\d+)s', value)
                        if match:
                            operator, count_str, window_str = match.groups()
                            count = int(count_str)
                            window = int(window_str)
                            
                            # Count similar alerts in time window
                            similar_count = self._count_similar_alerts(alert, window)
                            
                            if operator == ">" and similar_count <= count:
                                matches = False
                                break
                            elif operator == "<" and similar_count >= count:
                                matches = False
                                break
                    
                    elif key == "during_maintenance":
                        # Check if in maintenance window
                        # This would check against a maintenance schedule
                        if value and not self._is_in_maintenance_window():
                            matches = False
                            break
                    
                    elif key == "auto_resolved":
                        # Check if alert auto-resolved quickly
                        if value and not alert.metadata.get("auto_resolved", False):
                            matches = False
                            break
                    
                    elif key == "duration":
                        # Check alert duration
                        # Format: "<30s" or ">5m"
                        match = re.match(r'([<>]=?)(\d+)([smh])', value)
                        if match:
                            operator, duration_str, unit = match.groups()
                            duration = int(duration_str)
                            
                            # Convert to seconds
                            if unit == "m":
                                duration *= 60
                            elif unit == "h":
                                duration *= 3600
                            
                            # This would check actual alert duration
                            # For now, we'll skip this check
                            pass
                
                if matches:
                    print(f"[AlertCorrelator] Suppressing alert {alert.id} due to rule: {rule['id']}")
                    return True
                    
            except Exception as e:
                print(f"[AlertCorrelator] Error evaluating suppression rule {rule.get('id')}: {e}")
                continue
        
        return False
    
    def _count_similar_alerts(self, alert: Alert, window_seconds: int) -> int:
        """Count similar alerts in time window"""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        count = 0
        
        for stored_alert in self.alerts.values():
            if stored_alert.timestamp < cutoff:
                continue
            
            # Check similarity
            if (stored_alert.component == alert.component and
                stored_alert.type == alert.type and
                stored_alert.source == alert.source):
                count += 1
        
        return count
    
    def _is_in_maintenance_window(self) -> bool:
        """Check if current time is in maintenance window"""
        # This would check against a maintenance schedule
        # For now, return False (no maintenance)
        return False
    
    def _generate_alert_fingerprint(self, alert: Alert) -> str:
        """Generate fingerprint for alert deduplication"""
        # Create fingerprint based on key attributes
        fingerprint_data = {
            "source": alert.source,
            "type": alert.type.value,
            "component": alert.component,
            "message_hash": hashlib.md5(alert.message.encode()).hexdigest()[:8]
        }
        
        # Add metadata if it contains specific error codes or patterns
        if "error_code" in alert.metadata:
            fingerprint_data["error_code"] = alert.metadata["error_code"]
        if "metric" in alert.metadata:
            fingerprint_data["metric"] = alert.metadata["metric"]
        
        # Create fingerprint string
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    async def _check_duplicate_alerts(self, alert: Alert) -> Optional[CorrelatedAlertGroup]:
        """Check for duplicate alerts based on fingerprint"""
        if not alert.fingerprint:
            return None
        
        # Check fingerprint cache
        if alert.fingerprint in self.fingerprint_cache:
            group_id = self.fingerprint_cache[alert.fingerprint]
            if group_id in self.correlation_groups:
                group = self.correlation_groups[group_id]
                
                # Check if last duplicate was recent (within 10 minutes)
                if group.correlated_alerts:
                    last_alert = group.correlated_alerts[-1]
                    time_diff = (alert.timestamp - last_alert.timestamp).total_seconds()
                    if time_diff < 600:  # 10 minutes
                        return group
        
        return None
    
    async def _check_temporal_correlation(self, alert: Alert) -> Optional[CorrelatedAlertGroup]:
        """Check for temporal correlation (alerts within time window)"""
        cutoff = alert.timestamp - timedelta(seconds=self.temporal_window)
        
        # Find recent alerts that might be related
        recent_alerts = []
        for stored_alert in self.alerts.values():
            if stored_alert.timestamp < cutoff:
                continue
            
            # Skip if already correlated or suppressed
            if stored_alert.state in [AlertState.SUPPRESSED, AlertState.RESOLVED]:
                continue
            
            # Check if alert is related (similar component, source, or type)
            is_related = (
                stored_alert.component == alert.component or
                stored_alert.source == alert.source or
                stored_alert.type == alert.type or
                self._are_components_related(stored_alert.component, alert.component)
            )
            
            if is_related:
                recent_alerts.append(stored_alert)
        
        # If we have recent related alerts, check existing correlation groups
        if recent_alerts:
            # Find groups containing recent alerts
            candidate_groups = set()
            for recent_alert in recent_alerts:
                if recent_alert.correlation_id and recent_alert.correlation_id in self.correlation_groups:
                    candidate_groups.add(recent_alert.correlation_id)
            
            # Return the group with highest priority if found
            if candidate_groups:
                # Get the most recent group
                groups = [self.correlation_groups[gid] for gid in candidate_groups]
                groups.sort(key=lambda g: g.updated_at, reverse=True)
                return groups[0]
        
        return None
    
    async def _check_causal_correlation(self, alert: Alert) -> Optional[CorrelatedAlertGroup]:
        """Check for causal correlation based on dependency graph"""
        # Extract service name from component
        service_name = self._extract_service_from_component(alert.component)
        if not service_name or service_name not in self.dependency_graph:
            return None
        
        # Find alerts for dependent services (services that depend on this one)
        dependent_services = list(self.dependency_graph.predecessors(service_name))
        
        # Also find alerts for this service's dependencies (services this depends on)
        dependency_services = list(self.dependency_graph.successors(service_name))
        
        # Check for recent alerts in dependent or dependency services
        related_services = dependent_services + dependency_services + [service_name]
        
        # Look for existing correlation groups with alerts from related services
        for group_id, group in self.correlation_groups.items():
            # Skip if group is resolved or old
            if group.state in [AlertState.RESOLVED, AlertState.SUPPRESSED]:
                continue
            
            # Check if group contains alerts from related services
            group_services = set()
            group_services.add(self._extract_service_from_component(group.primary_alert.component))
            for correlated_alert in group.correlated_alerts:
                group_services.add(self._extract_service_from_component(correlated_alert.component))
            
            # Remove None values
            group_services.discard(None)
            
            # Check for overlap
            if group_services.intersection(set(related_services)):
                # Check if alert is temporally close to group
                time_diff = abs((alert.timestamp - group.updated_at).total_seconds())
                if time_diff < self.temporal_window * 2:  # Double window for causal
                    return group
        
        return None
    
    def _extract_service_from_component(self, component: str) -> Optional[str]:
        """Extract service name from component string"""
        # Component format examples:
        # "database:connection_pool"
        # "web_server:request_latency"
        # "payment_service"
        
        if ":" in component:
            return component.split(":")[0]
        else:
            # Try to match against known services
            for service in self.dependency_graph.nodes():
                if service in component:
                    return service
        
        return None
    
    def _are_components_related(self, component1: str, component2: str) -> bool:
        """Check if two components are related"""
        # Same service
        service1 = self._extract_service_from_component(component1)
        service2 = self._extract_service_from_component(component2)
        
        if service1 and service2:
            # Same service
            if service1 == service2:
                return True
            
            # Check dependency relationship
            if (self.dependency_graph.has_edge(service1, service2) or
                self.dependency_graph.has_edge(service2, service1)):
                return True
        
        return False
    
    def _create_correlation_group(self, alert: Alert) -> CorrelatedAlertGroup:
        """Create new correlation group"""
        group_id = f"corr_{int(time.time())}_{hashlib.md5(alert.id.encode()).hexdigest()[:8]}"
        
        group = CorrelatedAlertGroup(
            id=group_id,
            primary_alert=alert
        )
        
        # Store fingerprint for deduplication
        if alert.fingerprint:
            self.fingerprint_cache[alert.fingerprint] = group_id
        
        return group
    
    async def _determine_routing(self, group: CorrelatedAlertGroup) -> Dict[str, Any]:
        """Determine where to route correlated alert group"""
        # Evaluate routing rules in priority order
        sorted_rules = sorted(self.routing_rules, key=lambda r: r.get("priority", 999))
        
        for rule in sorted_rules:
            try:
                if await self._evaluate_routing_rule(rule, group):
                    destination_str = rule["destination"]
                    destination_map = {
                        "auto_remediation": RoutingDestination.AUTO_REMEDIATION,
                        "deployment_rollback": RoutingDestination.DEPLOYMENT_ROLLBACK,
                        "manual_intervention": RoutingDestination.MANUAL_INTERVENTION,
                        "monitor_only": RoutingDestination.MONITOR_ONLY,
                        "escalate_human": RoutingDestination.ESCALATE_HUMAN
                    }
                    
                    destination = destination_map.get(destination_str, RoutingDestination.MONITOR_ONLY)
                    
                    # Determine suggested action based on alert types
                    suggested_action = self._suggest_action_for_group(group)
                    
                    # Determine root cause if possible
                    root_cause = self._determine_root_cause(group)
                    
                    return {
                        "destination": destination,
                        "suggested_action": suggested_action,
                        "root_cause": root_cause,
                        "rule_applied": rule["id"]
                    }
                    
            except Exception as e:
                print(f"[AlertCorrelator] Error evaluating routing rule {rule.get('id')}: {e}")
                continue
        
        # Default routing
        if group.primary_alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return {
                "destination": RoutingDestination.ESCALATE_HUMAN,
                "suggested_action": "Manual investigation required",
                "root_cause": "Unknown - requires investigation",
                "rule_applied": "default_critical"
            }
        else:
            return {
                "destination": RoutingDestination.MONITOR_ONLY,
                "suggested_action": "Monitor for escalation",
                "root_cause": None,
                "rule_applied": "default_monitor"
            }
    
    async def _evaluate_routing_rule(self, rule: Dict[str, Any], group: CorrelatedAlertGroup) -> bool:
        """Evaluate if routing rule matches alert group"""
        condition = rule["condition"]
        
        # Get all alerts in group
        all_alerts = [group.primary_alert] + group.correlated_alerts
        
        for key, value in condition.items():
            if key == "component":
                expected_components = value if isinstance(value, list) else [value]
                if not any(alert.component in expected_components for alert in all_alerts):
                    return False
            
            elif key == "severity":
                expected_severities = value if isinstance(value, list) else [value]
                if not any(alert.severity.value in expected_severities for alert in all_alerts):
                    return False
            
            elif key == "type":
                expected_types = value if isinstance(value, list) else [value]
                if not any(alert.type.value in expected_types for alert in all_alerts):
                    return False
            
            elif key == "source":
                expected_sources = value if isinstance(value, list) else [value]
                if not any(alert.source in expected_sources for alert in all_alerts):
                    return False
            
            elif key == "correlated_count":
                # Format: ">=3" or "=5" or "<10"
                match = re.match(r'([<>]=?|=)(\d+)', str(value))
                if match:
                    operator, count_str = match.groups()
                    count = int(count_str)
                    actual_count = len(all_alerts)
                    
                    if operator == ">=" and actual_count < count:
                        return False
                    elif operator == "<=" and actual_count > count:
                        return False
                    elif operator == ">" and actual_count <= count:
                        return False
                    elif operator == "<" and actual_count >= count:
                        return False
                    elif operator == "=" and actual_count != count:
                        return False
            
            elif key == "affected_components":
                # Count unique components
                unique_components = len(set(alert.component for alert in all_alerts))
                match = re.match(r'([<>]=?|=)(\d+)', str(value))
                if match:
                    operator, count_str = match.groups()
                    count = int(count_str)
                    
                    if operator == ">=" and unique_components < count:
                        return False
                    elif operator == "<=" and unique_components > count:
                        return False
                    elif operator == ">" and unique_components <= count:
                        return False
                    elif operator == "<" and unique_components >= count:
                        return False
                    elif operator == "=" and unique_components != count:
                        return False
            
            elif key == "business_impact":
                if group.primary_alert.business_impact != value:
                    return False
            
            elif key == "affected_users":
                match = re.match(r'([<>]=?|=)(\d+)', str(value))
                if match:
                    operator, count_str = match.groups()
                    count = int(count_str)
                    affected_users = group.primary_alert.affected_users
                    
                    if operator == ">=" and affected_users < count:
                        return False
                    elif operator == "<=" and affected_users > count:
                        return False
                    elif operator == ">" and affected_users <= count:
                        return False
                    elif operator == "<" and affected_users >= count:
                        return False
                    elif operator == "=" and affected_users != count:
                        return False
        
        return True
    
    def _suggest_action_for_group(self, group: CorrelatedAlertGroup) -> str:
        """Suggest action based on alert types and patterns"""
        all_alerts = [group.primary_alert] + group.correlated_alerts
        
        # Check for deployment-related alerts
        if any(alert.type == AlertType.DEPLOYMENT for alert in all_alerts):
            return "Rollback deployment and investigate deployment pipeline"
        
        # Check for database-related alerts
        db_alerts = [a for a in all_alerts if "database" in a.component.lower()]
        if db_alerts:
            if any(a.type == AlertType.PERFORMANCE for a in db_alerts):
                return "Check database queries, add indexes, or scale database resources"
            elif any(a.type == AlertType.AVAILABILITY for a in db_alerts):
                return "Check database connectivity, restart service, or failover to replica"
        
        # Check for memory/cpu alerts
        resource_alerts = [a for a in all_alerts if any(
            term in a.component.lower() for term in ["memory", "cpu", "disk"]
        )]
        if resource_alerts:
            return "Scale resources, optimize application, or restart affected services"
        
        # Check for cascading failures
        if len(set(a.component for a in all_alerts)) >= 3:
            return "Investigate root cause - likely cascading failure from core service"
        
        # Default suggestion
        return "Investigate logs and metrics for root cause"
    
    def _determine_root_cause(self, group: CorrelatedAlertGroup) -> Optional[str]:
        """Attempt to determine root cause from correlated alerts"""
        all_alerts = [group.primary_alert] + group.correlated_alerts
        
        # Look for the earliest alert in the dependency chain
        if len(all_alerts) >= 2:
            # Sort by timestamp
            sorted_alerts = sorted(all_alerts, key=lambda a: a.timestamp)
            
            # Check if there's a pattern of dependent services failing
            services = [self._extract_service_from_component(a.component) for a in sorted_alerts]
            services = [s for s in services if s]
            
            if len(services) >= 2:
                # Check dependency relationships
                for i in range(len(services) - 1):
                    if self.dependency_graph.has_edge(services[i + 1], services[i]):
                        # services[i] depends on services[i+1], so services[i+1] might be root cause
                        return f"Service '{services[i + 1]}' failure causing cascade"
        
        # Check for common patterns
        alert_types = set(a.type for a in all_alerts)
        
        if AlertType.DEPLOYMENT in alert_types:
            return "Recent deployment introduced issues"
        
        if AlertType.DATABASE in alert_types:
            return "Database performance or connectivity issues"
        
        # Look at most severe alert
        severity_order = [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM]
        for severity in severity_order:
            severe_alerts = [a for a in all_alerts if a.severity == severity]
            if severe_alerts:
                return f"Root cause in {severe_alerts[0].component}"
        
        return None
    
    async def _route_correlated_group(self, group: CorrelatedAlertGroup):
        """Route correlated group to appropriate destination"""
        print(f"[AlertCorrelator] Routing group {group.id} to {group.routing_destination.value}")
        
        if group.routing_destination == RoutingDestination.AUTO_REMEDIATION:
            await self._route_to_auto_remediation(group)
            self.stats["auto_remediated"] += 1
            
        elif group.routing_destination == RoutingDestination.DEPLOYMENT_ROLLBACK:
            await self._route_to_deployment_rollback(group)
            
        elif group.routing_destination == RoutingDestination.ESCALATE_HUMAN:
            await self._escalate_to_human(group)
            self.stats["human_escalations"] += 1
            
        elif group.routing_destination == RoutingDestination.MANUAL_INTERVENTION:
            await self._request_manual_intervention(group)
            
        else:  # MONITOR_ONLY
            group.state = AlertState.ACKNOWLEDGED
            print(f"[AlertCorrelator] Group {group.id} set to monitor only")
    
    async def _route_to_auto_remediation(self, group: CorrelatedAlertGroup):
        """Route to auto-remediation engine"""
        print(f"[AlertCorrelator] Routing to auto-remediation: {group.id}")
        
        # Prepare remediation request
        remediation_request = {
            "correlation_group_id": group.id,
            "alerts": [a.to_dict() for a in [group.primary_alert] + group.correlated_alerts],
            "suggested_action": group.suggested_action,
            "root_cause": group.root_cause,
            "priority_score": group.priority_score,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory for auto-remediation engine to pick up
        project_status = self.memory.get_project_status() or {}
        
        if "monitoring" not in project_status:
            project_status["monitoring"] = {}
        
        if "remediation_requests" not in project_status["monitoring"]:
            project_status["monitoring"]["remediation_requests"] = []
        
        project_status["monitoring"]["remediation_requests"].append(remediation_request)
        
        # Keep only last 20 requests
        if len(project_status["monitoring"]["remediation_requests"]) > 20:
            project_status["monitoring"]["remediation_requests"] = \
                project_status["monitoring"]["remediation_requests"][-20:]
        
        self.memory.update_project_status(
            platform=project_status.get("platform", "unknown"),
            monitoring=project_status["monitoring"]
        )
        
        group.state = AlertState.RESOLVING
        print(f"[AlertCorrelator] Auto-remediation requested for group {group.id}")
    
    async def _route_to_deployment_rollback(self, group: CorrelatedAlertGroup):
        """Route to deployment rollback"""
        print(f"[AlertCorrelator] Routing to deployment rollback: {group.id}")
        
        # Find deployment-related alerts
        deployment_alerts = [
            a for a in [group.primary_alert] + group.correlated_alerts
            if a.type == AlertType.DEPLOYMENT
        ]
        
        if deployment_alerts:
            # Extract deployment info
            deployment_info = deployment_alerts[0].metadata.get("deployment_info", {})
            
            # Store rollback request
            rollback_request = {
                "correlation_group_id": group.id,
                "deployment_id": deployment_info.get("deployment_id"),
                "platform": deployment_info.get("platform"),
                "reason": f"Alert correlation: {group.root_cause or 'Deployment issues detected'}",
                "alerts": [a.to_dict() for a in deployment_alerts],
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in memory for deploy orchestrator
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            project_status["monitoring"]["rollback_requests"] = rollback_request
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
            group.state = AlertState.RESOLVING
            print(f"[AlertCorrelator] Deployment rollback requested for group {group.id}")
    
    async def _escalate_to_human(self, group: CorrelatedAlertGroup):
        """Escalate to human operator"""
        print(f"[AlertCorrelator] Escalating to human: {group.id}")
        
        # Create escalation ticket
        escalation_data = {
            "id": f"escalation_{group.id}",
            "correlation_group_id": group.id,
            "severity": group.primary_alert.severity.value,
            "title": f"Correlated Alert Group: {group.root_cause or 'Multiple issues detected'}",
            "description": f"{len(group.correlated_alerts) + 1} correlated alerts detected",
            "alerts": [a.to_dict() for a in [group.primary_alert] + group.correlated_alerts],
            "suggested_action": group.suggested_action,
            "priority_score": group.priority_score,
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "assigned_to": None
        }
        
        # Store in memory
        project_status = self.memory.get_project_status() or {}
        
        if "monitoring" not in project_status:
            project_status["monitoring"] = {}
        
        if "escalations" not in project_status["monitoring"]:
            project_status["monitoring"]["escalations"] = []
        
        project_status["monitoring"]["escalations"].append(escalation_data)
        
        # Keep only last 50 escalations
        if len(project_status["monitoring"]["escalations"]) > 50:
            project_status["monitoring"]["escalations"] = \
                project_status["monitoring"]["escalations"][-50:]
        
        self.memory.update_project_status(
            platform=project_status.get("platform", "unknown"),
            monitoring=project_status["monitoring"]
        )
        
        group.state = AlertState.ACKNOWLEDGED
        print(f"[AlertCorrelator] Human escalation created for group {group.id}")
    
    async def _request_manual_intervention(self, group: CorrelatedAlertGroup):
        """Request manual intervention"""
        print(f"[AlertCorrelator] Requesting manual intervention: {group.id}")
        
        # Similar to escalation but with different category
        intervention_data = {
            "id": f"intervention_{group.id}",
            "correlation_group_id": group.id,
            "type": "manual_intervention",
            "reason": group.suggested_action or "Manual investigation required",
            "alerts": [a.to_dict() for a in [group.primary_alert] + group.correlated_alerts],
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # Store in memory
        project_status = self.memory.get_project_status() or {}
        
        if "monitoring" not in project_status:
            project_status["monitoring"] = {}
        
        if "interventions" not in project_status["monitoring"]:
            project_status["monitoring"]["interventions"] = []
        
        project_status["monitoring"]["interventions"].append(intervention_data)
        
        self.memory.update_project_status(
            platform=project_status.get("platform", "unknown"),
            monitoring=project_status["monitoring"]
        )
        
        group.state = AlertState.RESOLVING
    
    def _store_alert(self, alert: Alert):
        """Store alert in memory"""
        self.alerts[alert.id] = alert
        
        # Add to priority queue
        priority_score = self._calculate_alert_priority(alert)
        heapq.heappush(self.priority_queue, (-priority_score, alert.timestamp, alert.id))
        
        # Clean up old alerts (keep last 1000)
        if len(self.alerts) > 1000:
            # Remove oldest alerts
            sorted_alerts = sorted(self.alerts.items(), key=lambda x: x[1].timestamp)
            for alert_id, _ in sorted_alerts[:-1000]:
                del self.alerts[alert_id]
        
        # Clean up priority queue
        while len(self.priority_queue) > 1000:
            heapq.heappop(self.priority_queue)
    
    def _calculate_alert_priority(self, alert: Alert) -> float:
        """Calculate priority score for individual alert"""
        severity_weights = {
            AlertSeverity.CRITICAL: 10.0,
            AlertSeverity.HIGH: 7.0,
            AlertSeverity.MEDIUM: 4.0,
            AlertSeverity.LOW: 2.0,
            AlertSeverity.INFO: 0.5
        }
        
        base_score = severity_weights.get(alert.severity, 1.0)
        
        # Adjust based on business impact
        impact_weights = {
            "critical": 3.0,
            "high": 2.0,
            "medium": 1.5,
            "low": 1.0
        }
        
        impact_multiplier = impact_weights.get(alert.business_impact, 1.0)
        
        # Adjust based on affected users
        user_multiplier = 1.0 + min(alert.affected_users / 10000, 2.0)  # Max 3.0
        
        return base_score * impact_multiplier * user_multiplier
    
    async def _update_memory_with_correlation(self, group: CorrelatedAlertGroup):
        """Update memory with correlation results"""
        try:
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            if "correlation_groups" not in project_status["monitoring"]:
                project_status["monitoring"]["correlation_groups"] = []
            
            # Add or update group
            group_dict = group.to_dict()
            existing_index = None
            
            for i, existing_group in enumerate(project_status["monitoring"]["correlation_groups"]):
                if existing_group["id"] == group.id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                project_status["monitoring"]["correlation_groups"][existing_index] = group_dict
            else:
                project_status["monitoring"]["correlation_groups"].append(group_dict)
            
            # Keep only last 50 groups
            if len(project_status["monitoring"]["correlation_groups"]) > 50:
                project_status["monitoring"]["correlation_groups"] = \
                    project_status["monitoring"]["correlation_groups"][-50:]
            
            # Update statistics
            project_status["monitoring"]["correlation_stats"] = self.stats
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
        except Exception as e:
            print(f"[AlertCorrelator] Failed to update memory: {e}")
    
    async def get_correlation_groups(self, state: Optional[AlertState] = None,
                                   limit: int = 20) -> List[Dict[str, Any]]:
        """Get correlation groups, optionally filtered by state"""
        groups = list(self.correlation_groups.values())
        
        if state:
            groups = [g for g in groups if g.state == state]
        
        # Sort by priority score (descending) and timestamp (descending)
        groups.sort(key=lambda g: (-g.priority_score, g.updated_at), reverse=True)
        
        return [g.to_dict() for g in groups[:limit]]
    
    async def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert correlation statistics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts_total": len(self.alerts),
            "correlation_groups_total": len(self.correlation_groups),
            "groups_by_state": {
                state.value: len([g for g in self.correlation_groups.values() if g.state == state])
                for state in AlertState
            },
            "processing_stats": self.stats,
            "suppression_rules_count": len(self.suppression_rules),
            "routing_rules_count": len(self.routing_rules)
        }
    
    async def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old alerts and correlation groups"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean up old alerts
        alerts_to_remove = []
        for alert_id, alert in self.alerts.items():
            if alert.timestamp < cutoff and alert.state in [AlertState.RESOLVED, AlertState.SUPPRESSED]:
                alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.alerts[alert_id]
        
        # Clean up old correlation groups
        groups_to_remove = []
        for group_id, group in self.correlation_groups.items():
            if group.updated_at < cutoff and group.state in [AlertState.RESOLVED, AlertState.SUPPRESSED]:
                groups_to_remove.append(group_id)
        
        for group_id in groups_to_remove:
            del self.correlation_groups[group_id]
        
        # Clean up fingerprint cache
        self.fingerprint_cache = {
            fp: group_id for fp, group_id in self.fingerprint_cache.items()
            if group_id in self.correlation_groups
        }
        
        print(f"[AlertCorrelator] Cleaned up {len(alerts_to_remove)} alerts and "
              f"{len(groups_to_remove)} groups older than {max_age_hours} hours")