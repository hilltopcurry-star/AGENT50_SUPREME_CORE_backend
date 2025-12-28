"""
Agent 50 Configuration Manager
Handles environment variables, API keys, and global settings.
"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class APIConfig:
    """API configuration for external services."""
    gemini_api_key: str
    render_api_key: str
    github_token: str

@dataclass
class PathConfig:
    """Path configuration for Agent 50."""
    projects_root: str = "./projects"
    memory_dir: str = "./memory"
    templates_dir: str = "./builder/templates"
    
class Config:
    """Main configuration manager for Agent 50."""
    
    def __init__(self):
        """Initialize configuration and validate required environment variables."""
        self.api = self._load_api_config()
        self.paths = PathConfig()
        self.flags = self._load_flags()
        
        # Validate all required configuration
        self._validate()
    
    def _load_api_config(self) -> APIConfig:
        """Load API keys from environment variables."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        render_key = os.environ.get("RENDER_API_KEY")
        github_token = os.environ.get("GITHUB_TOKEN")
        
        return APIConfig(
            gemini_api_key=gemini_key,
            render_api_key=render_key,
            github_token=github_token
        )
    
    def _load_flags(self) -> dict:
        """Load feature flags from environment variables."""
        return {
            "debug": os.environ.get("AGENT50_DEBUG", "false").lower() == "true",
            "auto_fix": os.environ.get("AGENT50_AUTO_FIX", "true").lower() == "true",
            "auto_deploy": os.environ.get("AGENT50_AUTO_DEPLOY", "true").lower() == "true",
            "skip_security": os.environ.get("AGENT50_SKIP_SECURITY", "false").lower() == "true",
            "dry_run": os.environ.get("AGENT50_DRY_RUN", "false").lower() == "true"
        }
    
    def _validate(self):
        """Validate that all required configuration is present."""
        missing = []
        
        # Check API keys
        if not self.api.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if not self.api.render_api_key:
            missing.append("RENDER_API_KEY")
        if not self.api.github_token:
            missing.append("GITHUB_TOKEN")
        
        # Validate project paths
        required_dirs = [
            self.paths.projects_root,
            self.paths.memory_dir,
            self.paths.templates_dir
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Raise error if any required config is missing
        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            error_msg += "\nPlease set these variables before running Agent 50."
            raise EnvironmentError(error_msg)
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value by key."""
        # Check in flags first
        if key in self.flags:
            return self.flags[key]
        
        # Check in API config
        if hasattr(self.api, key):
            return getattr(self.api, key)
        
        # Check in paths config
        if hasattr(self.paths, key):
            return getattr(self.paths, key)
        
        return default
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.flags["debug"]
    
    def is_auto_fix_enabled(self) -> bool:
        """Check if auto-fix is enabled."""
        return self.flags["auto_fix"]
    
    def is_auto_deploy_enabled(self) -> bool:
        """Check if auto-deploy is enabled."""
        return self.flags["auto_deploy"]

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance."""
    return config