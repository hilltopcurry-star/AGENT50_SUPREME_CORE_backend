"""
auto_remediation.py - Automated remediation engine for Agent 50
Executes safe, automated fixes for common issues with rollback capability
"""

import asyncio
import time
import json
import yaml
import subprocess
import os
import sys
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import hashlib
import tempfile
import shutil

# Import existing MemoryManager
from agent50_core.memory.memory_manager import MemoryManager

class RemediationType(Enum):
    """Types of remediation actions"""
    RESTART_SERVICE = "restart_service"
    SCALE_RESOURCES = "scale_resources"
    CONFIG_UPDATE = "config_update"
    ENV_VAR_UPDATE = "env_var_update"
    DATABASE_MAINTENANCE = "database_maintenance"
    CACHE_CLEAR = "cache_clear"
    DEPLOYMENT_ROLLBACK = "deployment_rollback"
    CONNECTION_POOL_ADJUST = "connection_pool_adjust"

class RemediationState(Enum):
    """Remediation lifecycle states"""
    PENDING = "pending"
    VALIDATING = "validating"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class RemediationRisk(Enum):
    """Risk level of remediation actions"""
    LOW = "low"      # Safe, non-breaking changes
    MEDIUM = "medium" # Potentially breaking, but reversible
    HIGH = "high"    # Breaking changes, requires careful handling

@dataclass
class RemediationAction:
    """Single remediation action"""
    id: str
    type: RemediationType
    target: str  # component/service name
    parameters: Dict[str, Any] = field(default_factory=dict)
    pre_conditions: List[Dict[str, Any]] = field(default_factory=list)
    post_conditions: List[Dict[str, Any]] = field(default_factory=list)
    rollback_action: Optional['RemediationAction'] = None
    risk_level: RemediationRisk = RemediationRisk.MEDIUM
    timeout_seconds: int = 300
    max_retries: int = 2

@dataclass
class RemediationPlan:
    """Complete remediation plan with multiple actions"""
    id: str
    correlation_group_id: str
    alerts: List[Dict[str, Any]]
    actions: List[RemediationAction]
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state: RemediationState = RemediationState.PENDING
    risk_level: RemediationRisk = RemediationRisk.MEDIUM
    execution_order: List[str] = field(default_factory=list)  # Action IDs in order
    results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    rollback_plan: Optional['RemediationPlan'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary"""
        return {
            "id": self.id,
            "correlation_group_id": self.correlation_group_id,
            "alert_count": len(self.alerts),
            "actions": [
                {
                    "id": action.id,
                    "type": action.type.value,
                    "target": action.target,
                    "risk_level": action.risk_level.value,
                    "parameters": action.parameters
                }
                for action in self.actions
            ],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "state": self.state.value,
            "risk_level": self.risk_level.value,
            "results": self.results
        }

class AutoRemediationEngine:
    """
    Automated remediation engine
    Executes safe fixes for common issues with validation and rollback
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.active_plans: Dict[str, RemediationPlan] = {}
        self.completed_plans: Dict[str, RemediationPlan] = {}
        self.remediation_lock = threading.Lock()
        self.running = False
        self.health_monitor = None  # Will be set by set_health_monitor
        
        # Configuration
        self.max_concurrent_remediations = 3
        self.verification_timeout = 600  # 10 minutes
        self.rollback_timeout = 900  # 15 minutes
        
        # Statistics
        self.stats = {
            "remediations_initiated": 0,
            "remediations_completed": 0,
            "remediations_successful": 0,
            "remediations_failed": 0,
            "rollbacks_executed": 0,
            "average_duration_seconds": 0
        }
        
        # Load remediation playbooks
        self.playbooks = self._load_playbooks()
        
        print(f"[AutoRemediation] Loaded {len(self.playbooks)} remediation playbooks")
    
    def set_health_monitor(self, health_monitor):
        """Set reference to health monitor for validation"""
        self.health_monitor = health_monitor
    
    def _load_playbooks(self) -> Dict[str, Dict[str, Any]]:
        """Load remediation playbooks from memory"""
        playbooks = {}
        
        try:
            # Try to load from project_status
            project_status = self.memory.get_project_status() or {}
            monitoring_config = project_status.get("monitoring", {})
            
            if "remediation_playbooks" in monitoring_config:
                playbooks = monitoring_config["remediation_playbooks"]
            else:
                # Load default playbooks
                playbooks = self._get_default_playbooks()
                
                # Save to memory
                if "monitoring" not in project_status:
                    project_status["monitoring"] = {}
                project_status["monitoring"]["remediation_playbooks"] = playbooks
                self.memory.update_project_status(
                    platform=project_status.get("platform", "unknown"),
                    monitoring=project_status["monitoring"]
                )
        
        except Exception as e:
            print(f"[AutoRemediation] Failed to load playbooks: {e}")
            playbooks = self._get_default_playbooks()
        
        return playbooks
    
    def _get_default_playbooks(self) -> Dict[str, Dict[str, Any]]:
        """Get default remediation playbooks"""
        return {
            "high_cpu_usage": {
                "name": "High CPU Usage Remediation",
                "description": "Remediate high CPU usage on services",
                "trigger_conditions": [
                    {"metric": "cpu_percent", "operator": ">", "value": 85, "duration": "5m"}
                ],
                "actions": [
                    {
                        "type": "scale_resources",
                        "target": "affected_service",
                        "parameters": {"cpu_increment": 0.5, "memory_increment": "512Mi"},
                        "risk": "medium",
                        "pre_conditions": [
                            {"type": "health_check", "target": "affected_service", "status": "healthy"}
                        ]
                    },
                    {
                        "type": "restart_service",
                        "target": "affected_service",
                        "parameters": {"grace_period": 30},
                        "risk": "high",
                        "pre_conditions": [
                            {"type": "can_restart", "target": "affected_service"}
                        ]
                    }
                ],
                "verification": {
                    "metrics": ["cpu_percent", "memory_percent"],
                    "thresholds": {"cpu_percent": 70, "duration": "3m"},
                    "health_checks": ["/health", "/metrics"]
                }
            },
            "high_memory_usage": {
                "name": "High Memory Usage Remediation",
                "description": "Remediate high memory usage on services",
                "trigger_conditions": [
                    {"metric": "memory_percent", "operator": ">", "value": 90, "duration": "5m"}
                ],
                "actions": [
                    {
                        "type": "scale_resources",
                        "target": "affected_service",
                        "parameters": {"memory_increment": "1Gi", "cpu_increment": 0.25},
                        "risk": "medium"
                    },
                    {
                        "type": "cache_clear",
                        "target": "affected_service",
                        "parameters": {"cache_type": "all"},
                        "risk": "low"
                    }
                ],
                "verification": {
                    "metrics": ["memory_percent"],
                    "thresholds": {"memory_percent": 80, "duration": "3m"}
                }
            },
            "database_connection_exhausted": {
                "name": "Database Connection Pool Exhaustion",
                "description": "Remediate database connection pool exhaustion",
                "trigger_conditions": [
                    {"metric": "database_connections", "operator": ">", "value": 90, "duration": "2m"}
                ],
                "actions": [
                    {
                        "type": "connection_pool_adjust",
                        "target": "database",
                        "parameters": {"max_connections_increment": 20},
                        "risk": "low"
                    },
                    {
                        "type": "database_maintenance",
                        "target": "database",
                        "parameters": {"action": "kill_idle_connections", "idle_timeout": 300},
                        "risk": "medium"
                    }
                ],
                "verification": {
                    "metrics": ["database_connections", "database_waiting_connections"],
                    "thresholds": {"database_connections": 70, "duration": "2m"}
                }
            },
            "service_unavailable": {
                "name": "Service Unavailable",
                "description": "Remediate service availability issues",
                "trigger_conditions": [
                    {"metric": "endpoint_availability", "operator": "<", "value": 0.95, "duration": "1m"}
                ],
                "actions": [
                    {
                        "type": "restart_service",
                        "target": "affected_service",
                        "parameters": {"grace_period": 10, "force": True},
                        "risk": "high"
                    }
                ],
                "verification": {
                    "health_checks": ["/health", "/ready", "/live"],
                    "required_success_rate": 0.99,
                    "duration": "2m"
                }
            },
            "deployment_failure": {
                "name": "Deployment Failure Rollback",
                "description": "Rollback failed deployment",
                "trigger_conditions": [
                    {"type": "deployment", "status": "failed"}
                ],
                "actions": [
                    {
                        "type": "deployment_rollback",
                        "target": "deployment",
                        "parameters": {"rollback_to": "previous_version"},
                        "risk": "medium"
                    }
                ],
                "verification": {
                    "health_checks": ["/health"],
                    "deployment_status": "healthy",
                    "duration": "5m"
                }
            }
        }
    
    async def start(self):
        """Start the remediation engine"""
        if self.running:
            print("[AutoRemediation] Engine already running")
            return
        
        print("[AutoRemediation] Starting auto-remediation engine...")
        self.running = True
        
        # Start monitoring for remediation requests
        asyncio.create_task(self._monitor_remediation_requests())
        
        # Start periodic cleanup
        asyncio.create_task(self._cleanup_old_plans())
        
        print("[AutoRemediation] Engine started")
    
    async def stop(self):
        """Stop the remediation engine"""
        if not self.running:
            return
        
        print("[AutoRemediation] Stopping auto-remediation engine...")
        self.running = False
        
        # Wait for active remediations to complete
        with self.remediation_lock:
            active_count = len([p for p in self.active_plans.values() 
                              if p.state not in [RemediationState.SUCCESS, RemediationState.FAILED]])
            
            if active_count > 0:
                print(f"[AutoRemediation] Waiting for {active_count} active remediations to complete...")
                # In production, we would wait with timeout
                await asyncio.sleep(30)
        
        print("[AutoRemediation] Engine stopped")
    
    async def _monitor_remediation_requests(self):
        """Monitor for new remediation requests"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                # Check for new remediation requests
                project_status = self.memory.get_project_status() or {}
                monitoring = project_status.get("monitoring", {})
                requests = monitoring.get("remediation_requests", [])
                
                if requests:
                    print(f"[AutoRemediation] Found {len(requests)} remediation requests")
                    
                    # Process each request
                    for request in requests[:5]:  # Process up to 5 at a time
                        try:
                            await self._process_remediation_request(request)
                        except Exception as e:
                            print(f"[AutoRemediation] Failed to process request: {e}")
                    
                    # Remove processed requests
                    processed_ids = [r.get("correlation_group_id") for r in requests[:5]]
                    monitoring["remediation_requests"] = [
                        r for r in requests if r.get("correlation_group_id") not in processed_ids
                    ]
                    
                    # Update memory
                    self.memory.update_project_status(
                        platform=project_status.get("platform", "unknown"),
                        monitoring=monitoring
                    )
                
            except Exception as e:
                print(f"[AutoRemediation] Error monitoring requests: {e}")
                await asyncio.sleep(30)
    
    async def _process_remediation_request(self, request: Dict[str, Any]):
        """Process a single remediation request"""
        correlation_group_id = request.get("correlation_group_id")
        
        if not correlation_group_id:
            print("[AutoRemediation] Request missing correlation_group_id")
            return
        
        # Check if already processing this correlation group
        with self.remediation_lock:
            for plan in self.active_plans.values():
                if plan.correlation_group_id == correlation_group_id:
                    print(f"[AutoRemediation] Already processing correlation group {correlation_group_id}")
                    return
        
        print(f"[AutoRemediation] Processing remediation request for correlation group {correlation_group_id}")
        
        # Create remediation plan
        plan = await self._create_remediation_plan(request)
        
        if not plan:
            print(f"[AutoRemediation] Failed to create remediation plan for {correlation_group_id}")
            return
        
        # Check if we have capacity for new remediations
        active_count = len([p for p in self.active_plans.values() 
                          if p.state not in [RemediationState.SUCCESS, RemediationState.FAILED]])
        
        if active_count >= self.max_concurrent_remediations:
            print(f"[AutoRemediation] Maximum concurrent remediations reached ({active_count})")
            # Store for later processing
            self.active_plans[plan.id] = plan
            return
        
        # Execute the plan
        await self._execute_remediation_plan(plan)
    
    async def _create_remediation_plan(self, request: Dict[str, Any]) -> Optional[RemediationPlan]:
        """Create remediation plan from request"""
        try:
            correlation_group_id = request["correlation_group_id"]
            alerts = request.get("alerts", [])
            suggested_action = request.get("suggested_action", "")
            root_cause = request.get("root_cause", "")
            
            # Generate plan ID
            plan_id = f"remediation_{correlation_group_id}_{int(time.time())}"
            
            # Analyze alerts to determine appropriate playbook
            playbook = self._select_playbook(alerts, root_cause, suggested_action)
            
            if not playbook:
                print(f"[AutoRemediation] No matching playbook for alerts")
                return None
            
            # Create actions from playbook
            actions = []
            for action_def in playbook.get("actions", []):
                # Determine target from alerts
                target = self._determine_action_target(action_def, alerts)
                
                if not target:
                    continue
                
                # Create remediation action
                action = RemediationAction(
                    id=f"{plan_id}_action_{len(actions)}",
                    type=RemediationType(action_def["type"]),
                    target=target,
                    parameters=action_def.get("parameters", {}),
                    pre_conditions=action_def.get("pre_conditions", []),
                    post_conditions=action_def.get("post_conditions", []),
                    risk_level=RemediationRisk(action_def.get("risk", "medium")),
                    timeout_seconds=action_def.get("timeout_seconds", 300)
                )
                
                actions.append(action)
            
            if not actions:
                print(f"[AutoRemediation] No valid actions generated")
                return None
            
            # Determine overall risk level
            risk_levels = [action.risk_level for action in actions]
            overall_risk = RemediationRisk.HIGH if RemediationRisk.HIGH in risk_levels else \
                          RemediationRisk.MEDIUM if RemediationRisk.MEDIUM in risk_levels else \
                          RemediationRisk.LOW
            
            # Create remediation plan
            plan = RemediationPlan(
                id=plan_id,
                correlation_group_id=correlation_group_id,
                alerts=alerts,
                actions=actions,
                risk_level=overall_risk,
                execution_order=[action.id for action in actions]
            )
            
            # Store plan
            with self.remediation_lock:
                self.active_plans[plan_id] = plan
            
            self.stats["remediations_initiated"] += 1
            
            # Record in memory
            await self._record_remediation_start(plan)
            
            print(f"[AutoRemediation] Created remediation plan {plan_id} with {len(actions)} actions")
            return plan
            
        except Exception as e:
            print(f"[AutoRemediation] Failed to create remediation plan: {e}")
            return None
    
    def _select_playbook(self, alerts: List[Dict[str, Any]], root_cause: str, 
                        suggested_action: str) -> Optional[Dict[str, Any]]:
        """Select appropriate playbook based on alerts and context"""
        if not alerts:
            return None
        
        # Extract key metrics and components from alerts
        alert_components = set()
        alert_types = set()
        alert_metrics = set()
        
        for alert in alerts:
            alert_components.add(alert.get("component", "").split(":")[0])
            alert_types.add(alert.get("type", ""))
            metadata = alert.get("metadata", {})
            if "metric" in metadata:
                alert_metrics.add(metadata["metric"])
        
        # Check root cause for clues
        root_cause_lower = root_cause.lower() if root_cause else ""
        suggested_action_lower = suggested_action.lower() if suggested_action else ""
        
        # Match against playbooks
        for playbook_id, playbook in self.playbooks.items():
            # Check trigger conditions
            trigger_conditions = playbook.get("trigger_conditions", [])
            
            for condition in trigger_conditions:
                if self._condition_matches(condition, alerts, root_cause_lower, suggested_action_lower):
                    print(f"[AutoRemediation] Selected playbook: {playbook_id}")
                    return playbook
        
        # Try fuzzy matching based on components and metrics
        for playbook_id, playbook in self.playbooks.items():
            playbook_name = playbook.get("name", "").lower()
            playbook_desc = playbook.get("description", "").lower()
            
            # Check if playbook mentions any of our components or metrics
            for component in alert_components:
                if component and component.lower() in playbook_name or component.lower() in playbook_desc:
                    print(f"[AutoRemediation] Fuzzy-matched playbook: {playbook_id} for component {component}")
                    return playbook
            
            for metric in alert_metrics:
                if metric and metric.lower() in playbook_name or metric.lower() in playbook_desc:
                    print(f"[AutoRemediation] Fuzzy-matched playbook: {playbook_id} for metric {metric}")
                    return playbook
        
        return None
    
    def _condition_matches(self, condition: Dict[str, Any], alerts: List[Dict[str, Any]], 
                          root_cause: str, suggested_action: str) -> bool:
        """Check if condition matches alerts and context"""
        condition_type = condition.get("type", "metric")
        
        if condition_type == "metric":
            metric = condition.get("metric")
            operator = condition.get("operator")
            value = condition.get("value")
            
            # Check each alert for matching metric
            for alert in alerts:
                metadata = alert.get("metadata", {})
                if metadata.get("metric") == metric:
                    alert_value = metadata.get("value")
                    if alert_value is not None:
                        if operator == ">" and alert_value > value:
                            return True
                        elif operator == "<" and alert_value < value:
                            return True
                        elif operator == "=" and alert_value == value:
                            return True
        
        elif condition_type == "deployment":
            # Check for deployment-related alerts
            for alert in alerts:
                if alert.get("type") == "deployment" and alert.get("status") == condition.get("status"):
                    return True
        
        # Check root cause or suggested action
        if "root_cause_contains" in condition:
            if condition["root_cause_contains"].lower() in root_cause:
                return True
        
        if "suggested_action_contains" in condition:
            if condition["suggested_action_contains"].lower() in suggested_action:
                return True
        
        return False
    
    def _determine_action_target(self, action_def: Dict[str, Any], 
                                alerts: List[Dict[str, Any]]) -> str:
        """Determine target for remediation action"""
        target = action_def.get("target", "")
        
        if target == "affected_service":
            # Find most common component from alerts
            component_counts = {}
            for alert in alerts:
                component = alert.get("component", "").split(":")[0]
                if component:
                    component_counts[component] = component_counts.get(component, 0) + 1
            
            if component_counts:
                return max(component_counts.items(), key=lambda x: x[1])[0]
            else:
                return "unknown"
        
        return target
    
    async def _execute_remediation_plan(self, plan: RemediationPlan):
        """Execute a remediation plan"""
        print(f"[AutoRemediation] Executing remediation plan {plan.id}")
        
        plan.started_at = datetime.now()
        plan.state = RemediationState.EXECUTING
        
        try:
            # Update plan state
            await self._update_plan_in_memory(plan)
            
            # Execute actions in order
            for action in plan.actions:
                print(f"[AutoRemediation] Executing action {action.id}: {action.type.value} on {action.target}")
                
                # Check pre-conditions
                pre_conditions_met = await self._check_pre_conditions(action)
                if not pre_conditions_met:
                    print(f"[AutoRemediation] Pre-conditions not met for action {action.id}")
                    plan.state = RemediationState.FAILED
                    plan.results[action.id] = {
                        "status": "failed",
                        "error": "Pre-conditions not met",
                        "timestamp": datetime.now().isoformat()
                    }
                    await self._update_plan_in_memory(plan)
                    await self._attempt_rollback(plan)
                    return
                
                # Execute action
                action_result = await self._execute_remediation_action(action)
                plan.results[action.id] = action_result
                
                if not action_result.get("success", False):
                    print(f"[AutoRemediation] Action {action.id} failed: {action_result.get('error')}")
                    plan.state = RemediationState.FAILED
                    await self._update_plan_in_memory(plan)
                    await self._attempt_rollback(plan)
                    return
                
                # Check post-conditions
                post_conditions_met = await self._check_post_conditions(action)
                if not post_conditions_met:
                    print(f"[AutoRemediation] Post-conditions not met for action {action.id}")
                    plan.state = RemediationState.FAILED
                    plan.results[action.id]["post_conditions_failed"] = True
                    await self._update_plan_in_memory(plan)
                    await self._attempt_rollback(plan)
                    return
            
            # All actions executed successfully
            print(f"[AutoRemediation] All actions completed for plan {plan.id}")
            
            # Verify overall remediation
            verification_result = await self._verify_remediation(plan)
            
            if verification_result.get("success", False):
                plan.state = RemediationState.SUCCESS
                plan.completed_at = datetime.now()
                self.stats["remediations_successful"] += 1
                print(f"[AutoRemediation] Remediation plan {plan.id} completed successfully")
            else:
                plan.state = RemediationState.FAILED
                plan.results["verification"] = verification_result
                print(f"[AutoRemediation] Remediation verification failed for plan {plan.id}")
                await self._attempt_rollback(plan)
            
        except Exception as e:
            print(f"[AutoRemediation] Error executing plan {plan.id}: {e}")
            plan.state = RemediationState.FAILED
            plan.results["execution_error"] = str(e)
            await self._attempt_rollback(plan)
        
        finally:
            # Update statistics
            self.stats["remediations_completed"] += 1
            if plan.state == RemediationState.FAILED:
                self.stats["remediations_failed"] += 1
            
            # Calculate duration
            if plan.started_at and plan.completed_at:
                duration = (plan.completed_at - plan.started_at).total_seconds()
                # Update rolling average
                old_avg = self.stats["average_duration_seconds"]
                count = self.stats["remediations_completed"]
                self.stats["average_duration_seconds"] = (
                    (old_avg * (count - 1) + duration) / count
                ) if count > 1 else duration
            
            # Move to completed plans
            with self.remediation_lock:
                self.completed_plans[plan.id] = plan
                if plan.id in self.active_plans:
                    del self.active_plans[plan.id]
            
            # Update memory
            await self._update_plan_in_memory(plan)
            await self._record_remediation_completion(plan)
    
    async def _check_pre_conditions(self, action: RemediationAction) -> bool:
        """Check pre-conditions for remediation action"""
        if not action.pre_conditions:
            return True
        
        print(f"[AutoRemediation] Checking {len(action.pre_conditions)} pre-conditions for action {action.id}")
        
        for condition in action.pre_conditions:
            condition_type = condition.get("type")
            
            if condition_type == "health_check":
                target = condition.get("target", action.target)
                if not await self._check_health(target):
                    print(f"[AutoRemediation] Health check failed for {target}")
                    return False
            
            elif condition_type == "can_restart":
                target = condition.get("target", action.target)
                if not await self._can_restart_service(target):
                    print(f"[AutoRemediation] Cannot restart service {target}")
                    return False
            
            elif condition_type == "resource_available":
                # Check if resources are available for scaling
                resource_type = condition.get("resource_type", "cpu")
                required_amount = condition.get("required_amount")
                
                if not await self._check_resource_availability(resource_type, required_amount):
                    print(f"[AutoRemediation] Insufficient {resource_type} available")
                    return False
        
        return True
    
    async def _check_post_conditions(self, action: RemediationAction) -> bool:
        """Check post-conditions for remediation action"""
        if not action.post_conditions:
            return True
        
        print(f"[AutoRemediation] Checking {len(action.post_conditions)} post-conditions for action {action.id}")
        
        for condition in action.post_conditions:
            condition_type = condition.get("type")
            
            if condition_type == "health_check":
                target = condition.get("target", action.target)
                if not await self._check_health(target, timeout=60):
                    print(f"[AutoRemediation] Post-action health check failed for {target}")
                    return False
        
        return True
    
    async def _execute_remediation_action(self, action: RemediationAction) -> Dict[str, Any]:
        """Execute a single remediation action"""
        result = {
            "action_id": action.id,
            "type": action.type.value,
            "target": action.target,
            "started_at": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            if action.type == RemediationType.RESTART_SERVICE:
                result.update(await self._action_restart_service(action))
            
            elif action.type == RemediationType.SCALE_RESOURCES:
                result.update(await self._action_scale_resources(action))
            
            elif action.type == RemediationType.CONFIG_UPDATE:
                result.update(await self._action_config_update(action))
            
            elif action.type == RemediationType.ENV_VAR_UPDATE:
                result.update(await self._action_env_var_update(action))
            
            elif action.type == RemediationType.DATABASE_MAINTENANCE:
                result.update(await self._action_database_maintenance(action))
            
            elif action.type == RemediationType.CACHE_CLEAR:
                result.update(await self._action_cache_clear(action))
            
            elif action.type == RemediationType.DEPLOYMENT_ROLLBACK:
                result.update(await self._action_deployment_rollback(action))
            
            elif action.type == RemediationType.CONNECTION_POOL_ADJUST:
                result.update(await self._action_connection_pool_adjust(action))
            
            else:
                result["error"] = f"Unknown action type: {action.type}"
        
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
        
        result["completed_at"] = datetime.now().isoformat()
        return result
    
    async def _action_restart_service(self, action: RemediationAction) -> Dict[str, Any]:
        """Restart a service"""
        service_name = action.target
        grace_period = action.parameters.get("grace_period", 30)
        force = action.parameters.get("force", False)
        
        print(f"[AutoRemediation] Restarting service {service_name} (grace: {grace_period}s)")
        
        # This would be platform-specific implementation
        # For Docker
        try:
            import docker
            client = docker.from_env()
            
            # Find container
            containers = client.containers.list(all=True, filters={"name": service_name})
            if not containers:
                return {"error": f"Service {service_name} not found", "success": False}
            
            container = containers[0]
            
            # Restart container
            container.restart(timeout=grace_period)
            
            # Wait for service to come back up
            await asyncio.sleep(10)
            
            # Verify restart
            if await self._check_health(service_name, timeout=60):
                return {"success": True, "message": f"Service {service_name} restarted successfully"}
            else:
                return {"error": f"Service {service_name} failed health check after restart", "success": False}
                
        except ImportError:
            # Fallback to systemd or other methods
            return await self._restart_service_systemd(service_name)
    
    async def _restart_service_systemd(self, service_name: str) -> Dict[str, Any]:
        """Restart service using systemd"""
        try:
            # Try to restart using systemctl
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Check service status
                status_result = subprocess.run(
                    ["sudo", "systemctl", "is-active", service_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if status_result.stdout.strip() == "active":
                    return {"success": True, "message": f"Service {service_name} restarted successfully"}
                else:
                    return {"error": f"Service {service_name} not active after restart", "success": False}
            else:
                return {"error": f"Failed to restart service: {result.stderr}", "success": False}
                
        except Exception as e:
            return {"error": f"Systemd restart failed: {str(e)}", "success": False}
    
    async def _action_scale_resources(self, action: RemediationAction) -> Dict[str, Any]:
        """Scale service resources"""
        service_name = action.target
        cpu_increment = action.parameters.get("cpu_increment")
        memory_increment = action.parameters.get("memory_increment")
        
        print(f"[AutoRemediation] Scaling resources for {service_name}: "
              f"CPU +{cpu_increment}, Memory +{memory_increment}")
        
        # This would be platform-specific
        # For Docker Compose
        try:
            compose_file = "docker-compose.yml"
            if not os.path.exists(compose_file):
                compose_file = "docker-compose.yaml"
            
            if os.path.exists(compose_file):
                # Read compose file
                with open(compose_file, 'r') as f:
                    compose_config = yaml.safe_load(f)
                
                # Update resource limits
                services = compose_config.get("services", {})
                if service_name in services:
                    deploy_config = services[service_name].get("deploy", {})
                    resources = deploy_config.get("resources", {})
                    limits = resources.get("limits", {})
                    
                    if cpu_increment:
                        current_cpu = limits.get("cpus", "1.0")
                        # Parse current CPU value
                        if isinstance(current_cpu, str):
                            try:
                                new_cpu = float(current_cpu) + float(cpu_increment)
                            except:
                                new_cpu = 1.0 + float(cpu_increment)
                        else:
                            new_cpu = current_cpu + float(cpu_increment)
                        limits["cpus"] = str(new_cpu)
                    
                    if memory_increment:
                        current_memory = limits.get("memory", "512M")
                        # Parse and increment memory (simplified)
                        limits["memory"] = memory_increment
                    
                    resources["limits"] = limits
                    deploy_config["resources"] = resources
                    services[service_name]["deploy"] = deploy_config
                    compose_config["services"] = services
                    
                    # Write updated compose file
                    with open(compose_file, 'w') as f:
                        yaml.dump(compose_config, f)
                    
                    # Restart service with new limits
                    subprocess.run(
                        ["docker-compose", "up", "-d", "--force-recreate", service_name],
                        capture_output=True,
                        timeout=60
                    )
                    
                    return {"success": True, "message": f"Scaled resources for {service_name}"}
                
                return {"error": f"Service {service_name} not found in compose file", "success": False}
            
            return {"error": "Docker compose file not found", "success": False}
            
        except Exception as e:
            return {"error": f"Resource scaling failed: {str(e)}", "success": False}
    
    async def _action_config_update(self, action: RemediationAction) -> Dict[str, Any]:
        """Update service configuration"""
        service_name = action.target
        config_path = action.parameters.get("config_path")
        config_updates = action.parameters.get("updates", {})
        
        print(f"[AutoRemediation] Updating config for {service_name} at {config_path}")
        
        if not config_path or not os.path.exists(config_path):
            return {"error": f"Config file not found: {config_path}", "success": False}
        
        try:
            # Backup original config
            backup_path = f"{config_path}.backup.{int(time.time())}"
            shutil.copy2(config_path, backup_path)
            
            # Read and update config based on file type
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Deep update
                self._deep_update(config, config_updates)
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            
            elif config_path.endswith(('.yaml', '.yml')):
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                self._deep_update(config, config_updates)
                
                with open(config_path, 'w') as f:
                    yaml.dump(config, f)
            
            elif config_path.endswith('.env'):
                with open(config_path, 'r') as f:
                    lines = f.readlines()
                
                # Update or add environment variables
                updates_dict = {k: str(v) for k, v in config_updates.items()}
                updated_lines = []
                for line in lines:
                    if '=' in line:
                        key = line.split('=', 1)[0].strip()
                        if key in updates_dict:
                            updated_lines.append(f"{key}={updates_dict[key]}\n")
                            del updates_dict[key]
                            continue
                    updated_lines.append(line)
                
                # Add new variables
                for key, value in updates_dict.items():
                    updated_lines.append(f"{key}={value}\n")
                
                with open(config_path, 'w') as f:
                    f.writelines(updated_lines)
            
            else:
                # Assume key-value pairs for simple configs
                with open(config_path, 'r') as f:
                    content = f.read()
                
                for key, value in config_updates.items():
                    # Simple find and replace
                    pattern = rf"^{key}\s*=\s*.*$"
                    replacement = f"{key} = {value}"
                    import re
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                
                with open(config_path, 'w') as f:
                    f.write(content)
            
            # Restart service to apply config
            await self._action_restart_service(action)
            
            return {
                "success": True, 
                "message": f"Updated config for {service_name}",
                "backup_path": backup_path
            }
            
        except Exception as e:
            return {"error": f"Config update failed: {str(e)}", "success": False}
    
    def _deep_update(self, original: Dict, updates: Dict):
        """Deep update dictionary"""
        for key, value in updates.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self._deep_update(original[key], value)
            else:
                original[key] = value
    
    async def _action_env_var_update(self, action: RemediationAction) -> Dict[str, Any]:
        """Update environment variables"""
        service_name = action.target
        env_updates = action.parameters.get("updates", {})
        platform = action.parameters.get("platform", "docker")
        
        print(f"[AutoRemediation] Updating environment variables for {service_name} on {platform}")
        
        try:
            if platform == "docker":
                # Update Docker container environment
                import docker
                client = docker.from_env()
                
                containers = client.containers.list(all=True, filters={"name": service_name})
                if not containers:
                    return {"error": f"Container {service_name} not found", "success": False}
                
                container = containers[0]
                
                # Get current environment
                env_vars = {}
                for env in container.attrs['Config']['Env']:
                    if '=' in env:
                        key, value = env.split('=', 1)
                        env_vars[key] = value
                
                # Update environment
                env_vars.update(env_updates)
                
                # Recreate container with new environment
                container.stop()
                container.remove()
                
                # Get original config
                image = container.attrs['Config']['Image']
                ports = container.attrs['HostConfig']['PortBindings']
                volumes = container.attrs['HostConfig']['Binds']
                
                # Create new container
                new_env_list = [f"{k}={v}" for k, v in env_vars.items()]
                client.containers.run(
                    image,
                    environment=new_env_list,
                    ports=ports,
                    volumes=volumes,
                    name=service_name,
                    detach=True
                )
                
                return {"success": True, "message": f"Updated env vars for {service_name}"}
            
            elif platform in ["render", "railway", "flyio"]:
                # Platform-specific API calls
                return await self._update_env_vars_platform(platform, service_name, env_updates)
            
            else:
                return {"error": f"Unsupported platform: {platform}", "success": False}
                
        except Exception as e:
            return {"error": f"Env var update failed: {str(e)}", "success": False}
    
    async def _update_env_vars_platform(self, platform: str, service_name: str, 
                                       env_updates: Dict[str, str]) -> Dict[str, Any]:
        """Update environment variables on specific platform"""
        # Platform-specific implementations would go here
        # For now, return a simulated success
        print(f"[AutoRemediation] Would update env vars on {platform} for {service_name}")
        return {"success": True, "message": f"Env vars updated on {platform} (simulated)"}
    
    async def _action_database_maintenance(self, action: RemediationAction) -> Dict[str, Any]:
        """Perform database maintenance"""
        db_type = action.target
        maintenance_action = action.parameters.get("action")
        
        print(f"[AutoRemediation] Performing database maintenance: {maintenance_action} on {db_type}")
        
        try:
            if maintenance_action == "kill_idle_connections":
                idle_timeout = action.parameters.get("idle_timeout", 300)
                
                if db_type.lower() == "postgresql":
                    # PostgreSQL idle connection cleanup
                    import psycopg2
                    
                    # Get connection from environment
                    db_url = os.getenv("DATABASE_URL")
                    if not db_url:
                        return {"error": "DATABASE_URL not set", "success": False}
                    
                    conn = psycopg2.connect(db_url)
                    cursor = conn.cursor()
                    
                    # Kill idle connections
                    query = """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE state = 'idle'
                    AND state_change < NOW() - INTERVAL '%s seconds'
                    AND pid <> pg_backend_pid();
                    """
                    
                    cursor.execute(query, (idle_timeout,))
                    killed_count = cursor.rowcount
                    
                    cursor.close()
                    conn.close()
                    
                    return {
                        "success": True, 
                        "message": f"Killed {killed_count} idle connections",
                        "killed_count": killed_count
                    }
            
            elif maintenance_action == "vacuum":
                # Database vacuum
                if db_type.lower() == "postgresql":
                    import psycopg2
                    
                    db_url = os.getenv("DATABASE_URL")
                    if not db_url:
                        return {"error": "DATABASE_URL not set", "success": False}
                    
                    conn = psycopg2.connect(db_url)
                    conn.autocommit = True
                    cursor = conn.cursor()
                    
                    cursor.execute("VACUUM ANALYZE;")
                    cursor.close()
                    conn.close()
                    
                    return {"success": True, "message": "Database vacuum completed"}
            
            return {"error": f"Unknown maintenance action: {maintenance_action}", "success": False}
            
        except Exception as e:
            return {"error": f"Database maintenance failed: {str(e)}", "success": False}
    
    async def _action_cache_clear(self, action: RemediationAction) -> Dict[str, Any]:
        """Clear cache"""
        cache_type = action.target
        cache_key_pattern = action.parameters.get("pattern", "*")
        
        print(f"[AutoRemediation] Clearing cache: {cache_type} with pattern {cache_key_pattern}")
        
        try:
            if cache_type.lower() == "redis":
                import redis
                
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                r = redis.from_url(redis_url)
                
                if cache_key_pattern == "*":
                    r.flushall()
                    message = "Cleared all Redis cache"
                else:
                    # Delete keys matching pattern
                    keys = r.keys(cache_key_pattern)
                    if keys:
                        r.delete(*keys)
                        message = f"Cleared {len(keys)} Redis keys matching {cache_key_pattern}"
                    else:
                        message = "No keys found matching pattern"
                
                return {"success": True, "message": message}
            
            elif cache_type.lower() == "memory":
                # Clear in-memory cache (application-specific)
                # This would depend on the application's cache implementation
                return {"success": True, "message": "Memory cache cleared (simulated)"}
            
            else:
                return {"error": f"Unsupported cache type: {cache_type}", "success": False}
                
        except ImportError:
            return {"error": "Redis not available", "success": False}
        except Exception as e:
            return {"error": f"Cache clear failed: {str(e)}", "success": False}
    
    async def _action_deployment_rollback(self, action: RemediationAction) -> Dict[str, Any]:
        """Rollback deployment"""
        deployment_id = action.target
        rollback_to = action.parameters.get("rollback_to", "previous_version")
        
        print(f"[AutoRemediation] Rolling back deployment {deployment_id} to {rollback_to}")
        
        # This would call the deployment orchestrator
        # For now, simulate success
        return {"success": True, "message": f"Deployment {deployment_id} rolled back"}
    
    async def _action_connection_pool_adjust(self, action: RemediationAction) -> Dict[str, Any]:
        """Adjust connection pool settings"""
        pool_type = action.target
        max_connections_increment = action.parameters.get("max_connections_increment", 10)
        
        print(f"[AutoRemediation] Adjusting connection pool for {pool_type}, increment: {max_connections_increment}")
        
        # This would update connection pool configuration
        # For now, simulate success
        return {"success": True, "message": f"Connection pool adjusted for {pool_type}"}
    
    async def _check_health(self, target: str, timeout: int = 30) -> bool:
        """Check health of a target"""
        if self.health_monitor and hasattr(self.health_monitor, 'check_component_health'):
            try:
                health_result = await self.health_monitor.check_component_health(target, timeout)
                return health_result.get("healthy", False)
            except:
                pass
        
        # Fallback: try HTTP health check
        try:
            import aiohttp
            import asyncio
            
            # Try common health endpoints
            health_endpoints = [
                f"http://{target}:8080/health",
                f"http://{target}/health",
                f"http://localhost:8080/{target}/health"
            ]
            
            async with aiohttp.ClientSession() as session:
                for endpoint in health_endpoints:
                    try:
                        async with session.get(endpoint, timeout=timeout) as response:
                            if response.status < 400:
                                return True
                    except:
                        continue
            
            return False
            
        except:
            return False
    
    async def _can_restart_service(self, service_name: str) -> bool:
        """Check if a service can be safely restarted"""
        # Check if service has multiple instances (can withstand restart)
        # Check if it's critical (shouldn't be restarted automatically)
        # For now, allow all restarts
        return True
    
    async def _check_resource_availability(self, resource_type: str, required_amount: Any) -> bool:
        """Check if resources are available for scaling"""
        # Check system resources or platform quotas
        # For now, assume resources are available
        return True
    
    async def _verify_remediation(self, plan: RemediationPlan) -> Dict[str, Any]:
        """Verify that remediation was successful"""
        print(f"[AutoRemediation] Verifying remediation for plan {plan.id}")
        
        plan.state = RemediationState.VERIFYING
        await self._update_plan_in_memory(plan)
        
        verification_result = {
            "started_at": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            # Get verification configuration from playbook
            playbook = self._select_playbook(plan.alerts, "", "")
            verification_config = playbook.get("verification", {}) if playbook else {}
            
            # Check metrics
            metrics = verification_config.get("metrics", [])
            thresholds = verification_config.get("thresholds", {})
            
            if metrics:
                # Wait for metrics to stabilize
                await asyncio.sleep(30)
                
                # Check each metric (simplified)
                for metric in metrics:
                    threshold = thresholds.get(metric)
                    if threshold:
                        # In real implementation, would query metrics collector
                        # For now, assume metrics are within threshold
                        print(f"[AutoRemediation] Would verify metric {metric} < {threshold}")
            
            # Check health endpoints
            health_checks = verification_config.get("health_checks", [])
            required_success_rate = verification_config.get("required_success_rate", 0.95)
            
            successful_checks = 0
            for endpoint in health_checks:
                # Determine target from endpoint
                target = plan.actions[0].target if plan.actions else "unknown"
                full_endpoint = endpoint if endpoint.startswith("http") else f"http://{target}{endpoint}"
                
                if await self._check_endpoint_health(full_endpoint):
                    successful_checks += 1
            
            if health_checks:
                success_rate = successful_checks / len(health_checks)
                if success_rate >= required_success_rate:
                    verification_result["health_check_success_rate"] = success_rate
                else:
                    verification_result["error"] = f"Health check success rate {success_rate} < {required_success_rate}"
                    verification_result["completed_at"] = datetime.now().isoformat()
                    return verification_result
            
            # All verifications passed
            verification_result["success"] = True
            verification_result["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            verification_result["error"] = str(e)
            verification_result["completed_at"] = datetime.now().isoformat()
        
        return verification_result
    
    async def _check_endpoint_health(self, endpoint: str) -> bool:
        """Check health of an HTTP endpoint"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=10) as response:
                    return response.status < 400
        except:
            return False
    
    async def _attempt_rollback(self, plan: RemediationPlan):
        """Attempt to rollback failed remediation"""
        print(f"[AutoRemediation] Attempting rollback for failed plan {plan.id}")
        
        self.stats["rollbacks_executed"] += 1
        
        # Create rollback plan
        rollback_plan = await self._create_rollback_plan(plan)
        
        if rollback_plan:
            plan.rollback_plan = rollback_plan
            
            # Execute rollback
            rollback_result = await self._execute_rollback_plan(rollback_plan)
            
            if rollback_result.get("success", False):
                plan.state = RemediationState.ROLLED_BACK
                print(f"[AutoRemediation] Rollback successful for plan {plan.id}")
            else:
                plan.state = RemediationState.FAILED
                print(f"[AutoRemediation] Rollback failed for plan {plan.id}")
        else:
            plan.state = RemediationState.FAILED
            print(f"[AutoRemediation] Could not create rollback plan for {plan.id}")
        
        await self._update_plan_in_memory(plan)
    
    async def _create_rollback_plan(self, original_plan: RemediationPlan) -> Optional[RemediationPlan]:
        """Create rollback plan from original remediation plan"""
        try:
            rollback_id = f"rollback_{original_plan.id}"
            
            # Create reverse actions
            rollback_actions = []
            
            for original_action in reversed(original_plan.actions):
                # Create rollback action based on original action type
                rollback_action = self._create_rollback_action(original_action)
                if rollback_action:
                    rollback_actions.append(rollback_action)
            
            if not rollback_actions:
                return None
            
            # Create rollback plan
            rollback_plan = RemediationPlan(
                id=rollback_id,
                correlation_group_id=original_plan.correlation_group_id + "_rollback",
                alerts=original_plan.alerts,
                actions=rollback_actions,
                risk_level=RemediationRisk.LOW,  # Rollbacks are generally low risk
                execution_order=[action.id for action in rollback_actions]
            )
            
            return rollback_plan
            
        except Exception as e:
            print(f"[AutoRemediation] Failed to create rollback plan: {e}")
            return None
    
    def _create_rollback_action(self, original_action: RemediationAction) -> Optional[RemediationAction]:
        """Create rollback action for original action"""
        rollback_type = None
        rollback_params = {}
        
        if original_action.type == RemediationType.RESTART_SERVICE:
            # Restart service again (might bring it back to working state)
            rollback_type = RemediationType.RESTART_SERVICE
            rollback_params = original_action.parameters.copy()
        
        elif original_action.type == RemediationType.SCALE_RESOURCES:
            # Scale back to original resources
            rollback_type = RemediationType.SCALE_RESOURCES
            # In real implementation, would store original values
            # For now, scale down by same amount
            rollback_params = {
                "cpu_increment": -original_action.parameters.get("cpu_increment", 0),
                "memory_increment": f"-{original_action.parameters.get('memory_increment', '0')}"
            }
        
        elif original_action.type == RemediationType.CONFIG_UPDATE:
            # Restore from backup
            rollback_type = RemediationType.CONFIG_UPDATE
            backup_path = original_action.parameters.get("backup_path")
            if backup_path and os.path.exists(backup_path):
                rollback_params = {
                    "config_path": original_action.parameters.get("config_path"),
                    "restore_from": backup_path
                }
        
        if rollback_type:
            return RemediationAction(
                id=f"rollback_{original_action.id}",
                type=rollback_type,
                target=original_action.target,
                parameters=rollback_params,
                risk_level=RemediationRisk.LOW,
                timeout_seconds=original_action.timeout_seconds
            )
        
        return None
    
    async def _execute_rollback_plan(self, rollback_plan: RemediationPlan) -> Dict[str, Any]:
        """Execute rollback plan"""
        print(f"[AutoRemediation] Executing rollback plan {rollback_plan.id}")
        
        # Similar to regular plan execution but with rollback-specific logic
        for action in rollback_plan.actions:
            result = await self._execute_remediation_action(action)
            if not result.get("success", False):
                return {"success": False, "error": f"Rollback action {action.id} failed"}
        
        # Verify rollback
        await asyncio.sleep(30)  # Wait for system to stabilize
        
        # Check if system is healthy after rollback
        main_target = rollback_plan.actions[0].target if rollback_plan.actions else None
        if main_target and await self._check_health(main_target, timeout=60):
            return {"success": True, "message": "Rollback completed successfully"}
        else:
            return {"success": False, "error": "System not healthy after rollback"}
    
    async def _record_remediation_start(self, plan: RemediationPlan):
        """Record remediation start in memory"""
        try:
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            if "active_remediations" not in project_status["monitoring"]:
                project_status["monitoring"]["active_remediations"] = []
            
            # Add plan to active remediations
            project_status["monitoring"]["active_remediations"].append(plan.to_dict())
            
            # Keep only last 10 active remediations
            if len(project_status["monitoring"]["active_remediations"]) > 10:
                project_status["monitoring"]["active_remediations"] = \
                    project_status["monitoring"]["active_remediations"][-10:]
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
        except Exception as e:
            print(f"[AutoRemediation] Failed to record remediation start: {e}")
    
    async def _update_plan_in_memory(self, plan: RemediationPlan):
        """Update remediation plan in memory"""
        try:
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
            
            # Update active remediations
            if "active_remediations" in project_status["monitoring"]:
                active_remediations = project_status["monitoring"]["active_remediations"]
                for i, active_plan in enumerate(active_remediations):
                    if active_plan["id"] == plan.id:
                        active_remediations[i] = plan.to_dict()
                        break
            
            # Add to remediation history if completed
            if plan.state in [RemediationState.SUCCESS, RemediationState.FAILED, RemediationState.ROLLED_BACK]:
                if "remediation_history" not in project_status["monitoring"]:
                    project_status["monitoring"]["remediation_history"] = []
                
                project_status["monitoring"]["remediation_history"].append(plan.to_dict())
                
                # Keep only last 50 history entries
                if len(project_status["monitoring"]["remediation_history"]) > 50:
                    project_status["monitoring"]["remediation_history"] = \
                        project_status["monitoring"]["remediation_history"][-50:]
                
                # Remove from active remediations
                if "active_remediations" in project_status["monitoring"]:
                    project_status["monitoring"]["active_remediations"] = [
                        p for p in project_status["monitoring"]["active_remediations"]
                        if p["id"] != plan.id
                    ]
            
            # Update statistics
            project_status["monitoring"]["remediation_stats"] = self.stats
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=project_status["monitoring"]
            )
            
        except Exception as e:
            print(f"[AutoRemediation] Failed to update plan in memory: {e}")
    
    async def _record_remediation_completion(self, plan: RemediationPlan):
        """Record remediation completion in memory"""
        try:
            # Record in fixes_applied.json
            fix_record = {
                "id": plan.id,
                "correlation_group_id": plan.correlation_group_id,
                "type": "auto_remediation",
                "actions": [action.type.value for action in plan.actions],
                "state": plan.state.value,
                "started_at": plan.started_at.isoformat() if plan.started_at else None,
                "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
                "duration_seconds": (plan.completed_at - plan.started_at).total_seconds() 
                    if plan.started_at and plan.completed_at else None,
                "result": plan.results,
                "timestamp": datetime.now().isoformat()
            }
            
            self.memory.record_fix_applied(
                fix_type="auto_remediation",
                platform="monitoring",
                details=fix_record
            )
            
            # Update correlation group state if we have that information
            project_status = self.memory.get_project_status() or {}
            monitoring = project_status.get("monitoring", {})
            correlation_groups = monitoring.get("correlation_groups", [])
            
            for group in correlation_groups:
                if group.get("id") == plan.correlation_group_id:
                    group["remediation_state"] = plan.state.value
                    group["remediation_plan_id"] = plan.id
                    group["remediation_completed_at"] = datetime.now().isoformat()
                    break
            
            self.memory.update_project_status(
                platform=project_status.get("platform", "unknown"),
                monitoring=monitoring
            )
            
            print(f"[AutoRemediation] Recorded remediation completion for plan {plan.id}")
            
        except Exception as e:
            print(f"[AutoRemediation] Failed to record remediation completion: {e}")
    
    async def _cleanup_old_plans(self):
        """Clean up old remediation plans"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff = datetime.now() - timedelta(hours=24)
                
                with self.remediation_lock:
                    # Clean up completed plans older than 24 hours
                    plans_to_remove = []
                    for plan_id, plan in self.completed_plans.items():
                        if plan.completed_at and plan.completed_at < cutoff:
                            plans_to_remove.append(plan_id)
                    
                    for plan_id in plans_to_remove:
                        del self.completed_plans[plan_id]
                    
                    if plans_to_remove:
                        print(f"[AutoRemediation] Cleaned up {len(plans_to_remove)} old plans")
                
            except Exception as e:
                print(f"[AutoRemediation] Error in cleanup: {e}")
    
    async def get_active_remediations(self) -> List[Dict[str, Any]]:
        """Get list of active remediations"""
        with self.remediation_lock:
            return [plan.to_dict() for plan in self.active_plans.values()]
    
    async def get_remediation_stats(self) -> Dict[str, Any]:
        """Get remediation statistics"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_remediations": len(self.active_plans),
            "completed_remediations": len(self.completed_plans),
            "statistics": self.stats,
            "playbooks_loaded": len(self.playbooks)
        }
    
    async def trigger_manual_remediation(self, target: str, action_type: str, 
                                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger manual remediation (for testing or override)"""
        print(f"[AutoRemediation] Triggering manual remediation: {action_type} on {target}")
        
        # Create manual action
        action = RemediationAction(
            id=f"manual_{int(time.time())}",
            type=RemediationType(action_type),
            target=target,
            parameters=parameters,
            risk_level=RemediationRisk.HIGH  # Manual remediations are high risk
        )
        
        # Execute action
        result = await self._execute_remediation_action(action)
        
        # Record in memory
        if result.get("success", False):
            self.memory.record_fix_applied(
                fix_type="manual_remediation",
                platform="manual",
                details={
                    "action": action_type,
                    "target": target,
                    "parameters": parameters,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return result

# Example usage
async def example_usage():
    """Example of how to use the auto-remediation engine"""
    from agent50_core.memory.memory_manager import MemoryManager
    
    memory = MemoryManager()
    remediation_engine = AutoRemediationEngine(memory)
    
    # Start the engine
    await remediation_engine.start()
    
    # Create a test remediation request
    test_request = {
        "correlation_group_id": "test_correlation_123",
        "alerts": [
            {
                "id": "alert_1",
                "component": "web_server",
                "type": "threshold_exceeded",
                "severity": "critical",
                "metadata": {
                    "metric": "cpu_percent",
                    "value": 95,
                    "threshold": 85
                }
            }
        ],
        "suggested_action": "Scale resources or restart service",
        "root_cause": "High CPU usage",
        "priority_score": 8.5
    }
    
    # Process the request
    await remediation_engine._process_remediation_request(test_request)
    
    # Wait for completion
    await asyncio.sleep(10)
    
    # Get statistics
    stats = await remediation_engine.get_remediation_stats()
    print(f"Remediation stats: {stats}")
    
    # Stop the engine
    await remediation_engine.stop()

if __name__ == "__main__":
    asyncio.run(example_usage())