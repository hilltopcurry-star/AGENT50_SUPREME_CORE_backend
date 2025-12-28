"""
runtime_config_manager.py - Dynamic configuration management for Agent 50
Allows updating settings, feature flags, and environment variables without full redeployment.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from memory.memory_manager import MemoryManager

class ConfigSource(Enum):
    ENV = "environment"
    FILE = "file"
    DATABASE = "database"
    MEMORY = "memory"

class RuntimeConfigManager:
    """
    Manages dynamic configuration updates.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.logger = logging.getLogger("Agent50.Monitor.ConfigManager")
        self.config_cache: Dict[str, Any] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.last_reload = 0
        self.reload_interval = 30  # Seconds
        
        # Initialize
        self._load_initial_config()

    def _load_initial_config(self):
        """Load initial configuration from available sources."""
        # 1. Load from Environment
        self.config_cache.update(dict(os.environ))
        
        # 2. Load from Memory (Persistent settings)
        project_status = self.memory.get_project_status() or {}
        runtime_settings = project_status.get("runtime_settings", {})
        self.config_cache.update(runtime_settings)
        
        # 3. Load Feature Flags
        self.feature_flags = project_status.get("feature_flags", {
            "maintenance_mode": False,
            "debug_logging": False,
            "beta_features": False
        })
        
        self.logger.info("Runtime configuration initialized")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        self._check_reload()
        return self.config_cache.get(key, default)

    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get a feature flag status."""
        self._check_reload()
        return self.feature_flags.get(flag_name, default)

    def update_setting(self, key: str, value: Any, source: str = "user_override") -> bool:
        """
        Dynamically update a setting.
        Returns True if successful.
        """
        try:
            self.logger.info(f"Updating setting {key} to {value} (Source: {source})")
            
            # Update cache
            self.config_cache[key] = value
            
            # Persist to Memory
            project_status = self.memory.get_project_status() or {}
            if "runtime_settings" not in project_status:
                project_status["runtime_settings"] = {}
                
            project_status["runtime_settings"][key] = value
            
            # Record change history
            if "config_history" not in project_status:
                project_status["config_history"] = []
                
            project_status["config_history"].append({
                "key": key,
                "value": value,
                "source": source,
                "timestamp": time.time()
            })
            
            # Keep history clean
            if len(project_status["config_history"]) > 50:
                project_status["config_history"] = project_status["config_history"][-50:]
                
            self.memory.update_project_status(project_status)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update setting {key}: {e}")
            return False

    def set_feature_flag(self, flag_name: str, enabled: bool) -> bool:
        """Toggle a feature flag."""
        try:
            self.logger.info(f"Setting feature flag {flag_name} to {enabled}")
            
            self.feature_flags[flag_name] = enabled
            
            # Persist
            project_status = self.memory.get_project_status() or {}
            project_status["feature_flags"] = self.feature_flags
            self.memory.update_project_status(project_status)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to set feature flag {flag_name}: {e}")
            return False

    def _check_reload(self):
        """Check if config needs reloading (e.g. from external file changes)."""
        if time.time() - self.last_reload > self.reload_interval:
            # In a real scenario, this might check a DB or remote config server
            # For now, we just refresh from memory
            self._load_initial_config()
            self.last_reload = time.time()

    def get_all_config(self) -> Dict[str, Any]:
        """Return full configuration snapshot (sanitized)."""
        safe_config = self.config_cache.copy()
        # Hide secrets
        for key in safe_config:
            if any(s in key.lower() for s in ['key', 'secret', 'password', 'token']):
                safe_config[key] = '********'
        return {
            "settings": safe_config,
            "feature_flags": self.feature_flags
        }