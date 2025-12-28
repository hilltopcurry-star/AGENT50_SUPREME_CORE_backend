"""
canary_manager.py - Safe deployment manager for Agent 50.
Handles Canary and Blue-Green deployments with automated traffic shifting and rollback.
"""

import asyncio
import logging
import time
import json
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

from memory.memory_manager import MemoryManager
from monitor.runtime_config_manager import RuntimeConfigManager
from monitor.health_monitor_core import HealthMonitorCore

class DeploymentStrategy(Enum):
    CANARY = "canary"          # Gradual rollout (5% -> 20% -> 50% -> 100%)
    BLUE_GREEN = "blue_green"  # Instant switch between two full environments
    IMMEDIATE = "immediate"    # 100% rollout instantly (High Risk)

class RolloutState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    MONITORING = "monitoring"
    PROMOTING = "promoting"
    COMPLETED = "completed"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"

class CanaryManager:
    """
    Manages progressive delivery of new versions.
    """
    
    def __init__(self, 
                 memory_manager: MemoryManager, 
                 config_manager: RuntimeConfigManager,
                 health_monitor: HealthMonitorCore):
        
        self.memory = memory_manager
        self.config = config_manager
        self.health = health_monitor
        self.logger = logging.getLogger("Agent50.Monitor.Canary")
        
        # Default Canary Steps: % traffic, duration to wait (minutes)
        self.canary_steps = [
            (5, 5),   # 5% traffic, wait 5 mins
            (20, 10), # 20% traffic, wait 10 mins
            (50, 15), # 50% traffic, wait 15 mins
            (100, 0)  # 100% traffic, done
        ]
        
        self.current_rollout: Dict[str, Any] = self._load_state()
        self.is_running = False

    def _load_state(self) -> Dict[str, Any]:
        """Load active rollout state from memory."""
        status = self.memory.get_project_status() or {}
        return status.get("canary_state", {
            "state": RolloutState.IDLE.value,
            "version": None,
            "traffic_percent": 0,
            "current_step_index": 0,
            "step_start_time": 0
        })

    def _save_state(self):
        """Persist rollout state."""
        status = self.memory.get_project_status() or {}
        status["canary_state"] = self.current_rollout
        self.memory.update_project_status(status)

    async def start_rollout(self, new_version: str, strategy: DeploymentStrategy = DeploymentStrategy.CANARY):
        """Initiate a new deployment rollout."""
        if self.current_rollout["state"] not in [RolloutState.IDLE.value, RolloutState.COMPLETED.value, RolloutState.FAILED.value]:
            self.logger.warning(f"Cannot start rollout: Active rollout in state {self.current_rollout['state']}")
            return False

        self.logger.info(f"Starting {strategy.value} rollout for version {new_version}")
        
        self.current_rollout = {
            "state": RolloutState.STARTING.value,
            "version": new_version,
            "strategy": strategy.value,
            "traffic_percent": 0,
            "current_step_index": 0,
            "step_start_time": time.time(),
            "start_time": datetime.now().isoformat()
        }
        self._save_state()
        
        # Start the monitoring loop
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._rollout_loop())
            
        return True

    async def stop(self):
        """Stop the manager."""
        self.is_running = False

    async def _rollout_loop(self):
        """Main loop managing the rollout lifecycle."""
        self.logger.info("Canary Manager loop started.")
        
        while self.is_running:
            try:
                state = self.current_rollout["state"]
                
                if state == RolloutState.IDLE.value:
                    await asyncio.sleep(5)
                    continue

                if state == RolloutState.STARTING.value:
                    await self._execute_step()
                
                elif state == RolloutState.MONITORING.value:
                    await self._monitor_health()
                
                elif state == RolloutState.PROMOTING.value:
                    await self._promote_next_step()
                
                elif state == RolloutState.ROLLING_BACK.value:
                    await self._execute_rollback()

                await asyncio.sleep(10) # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in rollout loop: {e}")
                await asyncio.sleep(5)

    async def _monitor_health(self):
        """Check system health. If bad, trigger rollback."""
        # Check Health Monitor Score
        # We assume HealthMonitorCore is updating the score in memory
        status = self.memory.get_project_status() or {}
        health_data = status.get("monitoring", {})
        health_score = health_data.get("health_score", 100)
        
        # Threshold: If health drops below 90 during rollout, rollback.
        if health_score < 90:
            self.logger.error(f"Health score dropped to {health_score} during rollout. Initiating Rollback.")
            self.current_rollout["state"] = RolloutState.ROLLING_BACK.value
            self.current_rollout["failure_reason"] = f"Health score dropped to {health_score}"
            self._save_state()
            return

        # Check if step duration is complete
        step_idx = self.current_rollout["current_step_index"]
        target_percent, duration_min = self.canary_steps[step_idx]
        
        elapsed_min = (time.time() - self.current_rollout["step_start_time"]) / 60
        
        if elapsed_min >= duration_min:
            # Time to promote
            if target_percent < 100:
                self.current_rollout["state"] = RolloutState.PROMOTING.value
            else:
                self.current_rollout["state"] = RolloutState.COMPLETED.value
                self.logger.info("Rollout Completed Successfully.")
            self._save_state()

    async def _execute_step(self):
        """Apply the traffic percentage for the current step."""
        step_idx = self.current_rollout["current_step_index"]
        target_percent, _ = self.canary_steps[step_idx]
        
        self.logger.info(f"Setting traffic to {target_percent}% for version {self.current_rollout['version']}")
        
        # Integration Point: Update Runtime Config (Group 7E)
        # In a real system, this would update Load Balancer / Ingress rules
        success = self.config.update_setting(
            key="traffic_routing_weight", 
            value=target_percent, 
            source="canary_manager"
        )
        
        if success:
            self.current_rollout["traffic_percent"] = target_percent
            self.current_rollout["state"] = RolloutState.MONITORING.value
            self.current_rollout["step_start_time"] = time.time()
        else:
            self.logger.error("Failed to update traffic routing.")
            # Retry or fail? For now, retry next loop
            
        self._save_state()

    async def _promote_next_step(self):
        """Move to the next step in the canary plan."""
        current_idx = self.current_rollout["current_step_index"]
        
        if current_idx < len(self.canary_steps) - 1:
            self.current_rollout["current_step_index"] += 1
            self.current_rollout["state"] = RolloutState.STARTING.value # Loop back to apply new %
            self.logger.info(f"Promoting to step {self.current_rollout['current_step_index']}")
        else:
            self.current_rollout["state"] = RolloutState.COMPLETED.value
            
        self._save_state()

    async def _execute_rollback(self):
        """Revert traffic to 0% for new version immediately."""
        self.logger.warning("Executing Rollback...")
        
        # Reset traffic to 0 (back to stable version)
        success = self.config.update_setting(
            key="traffic_routing_weight", 
            value=0, 
            source="canary_rollback"
        )
        
        if success:
            self.current_rollout["traffic_percent"] = 0
            self.current_rollout["state"] = RolloutState.FAILED.value
            self.logger.info("Rollback complete. System stabilized.")
        else:
            self.logger.critical("Rollback failed to apply config! Manual intervention required.")
            
        self._save_state()
        
        # Stop loop until manual reset
        self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """Public API to get status."""
        return self.current_rollout