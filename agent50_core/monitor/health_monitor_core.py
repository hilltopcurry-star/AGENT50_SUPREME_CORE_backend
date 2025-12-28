"""
health_monitor_core.py - Central Health Monitoring Engine for Agent 50.
Orchestrates health checks, calculates health scores, and manages system state.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime
from enum import Enum
import statistics

# Import existing MemoryManager
from agent50_core.memory.memory_manager import MemoryManager

class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"      # 100-90 score
    DEGRADED = "degraded"    # 89-50 score
    UNHEALTHY = "unhealthy"  # < 50 score
    UNKNOWN = "unknown"      # No data

class CheckType(Enum):
    """Types of health checks"""
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    DATABASE = "database"
    EXTERNAL = "external"
    BUSINESS = "business"

class HealthCheckResult:
    """Standardized result container for any health check"""
    def __init__(self, 
                 name: str, 
                 status: bool, 
                 latency_ms: float, 
                 message: str = "",
                 details: Dict[str, Any] = None,
                 check_type: CheckType = CheckType.APPLICATION):
        self.name = name
        self.status = status  # True = Pass, False = Fail
        self.latency_ms = latency_ms
        self.message = message
        self.details = details or {}
        self.check_type = check_type
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": "pass" if self.status else "fail",
            "latency_ms": self.latency_ms,
            "message": self.message,
            "details": self.details,
            "type": self.check_type.value,
            "timestamp": self.timestamp
        }

class HealthMonitorCore:
    """
    Central engine for health monitoring.
    - Manages plugin registry
    - Schedules checks
    - Calculates composite health scores
    - Persists state to MemoryManager
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.logger = logging.getLogger("Agent50.Monitor.Core")
        
        # State
        self.is_running = False
        self.checks: Dict[str, Callable[[], Awaitable[HealthCheckResult]]] = {}
        self.check_configs: Dict[str, Dict[str, Any]] = {}
        self.check_history: Dict[str, List[HealthCheckResult]] = {}
        
        # Current Health State
        self.current_health = {
            "score": 100,
            "status": HealthStatus.UNKNOWN,
            "components": {}
        }
        
        # Configuration
        self.default_interval = 60  # seconds
        self.check_timeout = 10     # seconds
        self.history_size = 50      # keep last 50 results per check

    def register_check(self, 
                       name: str, 
                       check_func: Callable[[], Awaitable[HealthCheckResult]], 
                       interval: int = 60,
                       weight: float = 1.0,
                       check_type: CheckType = CheckType.APPLICATION):
        """
        Register a health check plugin.
        
        Args:
            name: Unique identifier for the check
            check_func: Async function returning HealthCheckResult
            interval: How often to run (seconds)
            weight: Importance in overall score (1.0 = standard, 5.0 = critical)
            check_type: Category of check
        """
        self.checks[name] = check_func
        self.check_configs[name] = {
            "interval": interval,
            "weight": weight,
            "type": check_type,
            "last_run": 0
        }
        self.check_history[name] = []
        self.logger.info(f"Registered health check: {name} (Type: {check_type.value}, Weight: {weight})")

    async def start(self):
        """Start the main monitoring loop."""
        if self.is_running:
            self.logger.warning("Health Monitor is already running")
            return
            
        self.is_running = True
        self.logger.info("Starting Health Monitor Core...")
        
        # Start the loop task
        asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop the monitoring loop."""
        self.is_running = False
        self.logger.info("Stopping Health Monitor Core...")

    async def _monitor_loop(self):
        """Main event loop for scheduling checks."""
        while self.is_running:
            try:
                current_time = time.time()
                tasks = []
                
                # Identify checks due for execution
                for name, config in self.check_configs.items():
                    if current_time - config["last_run"] >= config["interval"]:
                        tasks.append(self._execute_check(name))
                        config["last_run"] = current_time
                
                if tasks:
                    await asyncio.gather(*tasks)
                    
                    # After batch execution, recalculate overall health
                    self._recalculate_health()
                    
                    # Persist state
                    self._persist_state()
                
                # Small sleep to prevent tight loop
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)

    async def _execute_check(self, name: str):
        """Execute a single check safely with timeout."""
        check_func = self.checks.get(name)
        if not check_func:
            return
            
        try:
            # Enforce timeout
            result = await asyncio.wait_for(check_func(), timeout=self.check_timeout)
            
        except asyncio.TimeoutError:
            result = HealthCheckResult(
                name=name,
                status=False,
                latency_ms=self.check_timeout * 1000,
                message="Check timed out",
                check_type=self.check_configs[name]["type"]
            )
        except Exception as e:
            result = HealthCheckResult(
                name=name,
                status=False,
                latency_ms=0,
                message=f"Check raised exception: {str(e)}",
                check_type=self.check_configs[name]["type"]
            )
            
        # Update history
        history = self.check_history[name]
        history.append(result)
        if len(history) > self.history_size:
            history.pop(0)
            
        # Update current component state
        self.current_health["components"][name] = {
            "status": "healthy" if result.status else "unhealthy",
            "latency": result.latency_ms,
            "message": result.message,
            "last_check": result.timestamp
        }
        
        # If check failed, trigger alert immediately (Integration Point)
        if not result.status:
            await self._trigger_alert(result)

    def _recalculate_health(self):
        """Calculate composite health score based on weighted checks."""
        total_weight = 0
        earned_score = 0
        
        for name, history in self.check_history.items():
            if not history:
                continue
                
            latest = history[-1]
            config = self.check_configs[name]
            weight = config["weight"]
            
            total_weight += weight
            
            if latest.status:
                earned_score += (100 * weight)
            else:
                # 0 score for failing check
                pass
                
        if total_weight == 0:
            final_score = 100 # Default if no checks
        else:
            final_score = int(earned_score / total_weight)
            
        self.current_health["score"] = final_score
        
        # Map score to status enum
        if final_score >= 90:
            self.current_health["status"] = HealthStatus.HEALTHY
        elif final_score >= 50:
            self.current_health["status"] = HealthStatus.DEGRADED
        else:
            self.current_health["status"] = HealthStatus.UNHEALTHY
            
        self.logger.debug(f"Health Recalculated: Score={final_score}, Status={self.current_health['status'].value}")

    async def _trigger_alert(self, result: HealthCheckResult):
        """Push failure event to MemoryManager for AlertCorrelator (Group 7C)."""
        alert_data = {
            "source": "health_monitor",
            "type": "availability",
            "severity": "high" if self.check_configs[result.name]["weight"] > 1.0 else "medium",
            "component": result.name,
            "message": result.message or f"Health check {result.name} failed",
            "metadata": result.details,
            "timestamp": result.timestamp
        }
        
        # We assume MemoryManager has a method to queue/record alerts or status updates
        # This allows 7C (Alert Correlator) to pick it up via polling or shared memory
        try:
            project_status = self.memory.get_project_status() or {}
            
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
                
            if "alerts_queue" not in project_status["monitoring"]:
                project_status["monitoring"]["alerts_queue"] = []
                
            project_status["monitoring"]["alerts_queue"].append(alert_data)
            
            # Keep queue size manageable
            if len(project_status["monitoring"]["alerts_queue"]) > 100:
                 project_status["monitoring"]["alerts_queue"] = project_status["monitoring"]["alerts_queue"][-100:]

            self.memory.update_project_status(project_status)
            
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")

    def _persist_state(self):
        """Save full health state to MemoryManager."""
        try:
            status_update = {
                "health_score": self.current_health["score"],
                "health_status": self.current_health["status"].value,
                "last_update": datetime.now().isoformat(),
                "components": self.current_health["components"]
            }
            
            project_status = self.memory.get_project_status() or {}
            if "monitoring" not in project_status:
                project_status["monitoring"] = {}
                
            project_status["monitoring"].update(status_update)
            self.memory.update_project_status(project_status)
            
        except Exception as e:
            self.logger.error(f"Failed to persist state: {e}")

    # --- Public API for Integration ---

    async def record_health_degradation(self, data: Dict[str, Any]):
        """
        Callback for MetricsCollector (7B) to report threshold breaches.
        Allows external components to influence health score.
        """
        component = data.get("component", "unknown")
        metric = data.get("metric", "unknown")
        
        self.logger.warning(f"Health Degradation Reported: {component} - {metric}")
        
        # Impact score logic could go here
        # For now, we log it and force a persistence update to show degraded state
        
        # You could dynamically create a 'virtual' check that fails
        # to impact the score mathematically
        self.current_health["score"] = max(0, self.current_health["score"] - 5) # Penalize score
        if self.current_health["score"] < 90:
            self.current_health["status"] = HealthStatus.DEGRADED
            
        self._persist_state()

    async def check_component_health(self, component_name: str, timeout: int = 5) -> Dict[str, Any]:
        """
        On-demand check for a specific component.
        Used by Auto-Remediation (7D) for pre/post condition checks.
        """
        if component_name in self.checks:
            result = await self._execute_check(component_name)
            # Return last result
            history = self.check_history.get(component_name, [])
            if history:
                latest = history[-1]
                return {
                    "healthy": latest.status,
                    "latency": latest.latency_ms,
                    "details": latest.details
                }
        return {"healthy": False, "error": "Component not monitored"}