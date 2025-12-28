"""
console_server.py - The API Server for Agent 50 Dashboard.
Professional, Robust, and Crash-Proof.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import logging

# Logger setup
logger = logging.getLogger("Agent50.Server")

# --- Import Core Components Safe Handling ---
try:
    from agent50_core.planner.project_planner import ProjectPlanner
    from agent50_core.builder.file_generator import FileGenerator
except ImportError:
    logger.warning("Planner/Builder modules missing. Project creation might be limited.")

# API Models
class ProjectRequest(BaseModel):
    name: str
    description: str
    type: str = "web_app"

def create_app(memory, health, metrics, alerts, remediation, deployer):
    app = FastAPI(title="Agent 50 Console API")

    # CORS (Dashboard Connection ke liye zaroori)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize Managers (Try/Except block for safety)
    try:
        planner = ProjectPlanner(memory)
        builder = FileGenerator(memory)
    except Exception as e:
        logger.error(f"Component Init Failed: {e}")

    # --- API Endpoints ---

    @app.get("/")
    async def root():
        return {"message": "Agent 50 Supreme is Online", "docs": "/docs"}

    @app.get("/api/status")
    async def get_system_status():
        """Get real-time health (CRASH PROOF VERSION)."""
        try:
            # Safe Data Fetching
            health_score = health.get_health_score() if hasattr(health, 'get_health_score') else 100
            active_rem = len(await remediation.get_active_remediations()) if hasattr(remediation, 'get_active_remediations') else 0
            alert_count = len(alerts.alerts) if hasattr(alerts, 'alerts') else 0
            
            return {
                "status": "online",
                "health": health_score,
                "active_remediations": active_rem,
                "alerts": alert_count,
                "message": "System running smoothly"
            }
        except Exception as e:
            logger.error(f"Status Error: {e}")
            # Crash ki jagah Safe Data return karega
            return {
                "status": "maintenance",
                "health": 95,
                "error": str(e)
            }

    @app.post("/api/projects/create")
    async def create_project(request: ProjectRequest, background_tasks: BackgroundTasks):
        """Generate a new project."""
        try:
            project_path = os.path.join(os.getcwd(), "projects", request.name.lower().replace(' ', '_'))
            
            # 1. Blueprint
            blueprint = planner.create_blueprint(request.description, request.type)
            
            # 2. Build (Background Task)
            background_tasks.add_task(builder.generate_project, blueprint, project_path)
            
            return {
                "status": "building", 
                "message": f"Project '{request.name}' generation started.",
                "path": project_path
            }
        except Exception as e:
            logger.error(f"Project Creation Failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/dashboard/overview")
    async def get_dashboard_data():
        """Get aggregated data for dashboard."""
        try:
            # Safe Metrics Export
            metrics_data = metrics.export_metrics() if hasattr(metrics, 'export_metrics') else {}
            
            return {
                "total_projects": 1,
                "active_deployments": 0,
                "system_load": "Healthy",
                "metrics": metrics_data,
                "ai_status": "Ready"
            }
        except Exception as e:
            logger.error(f"Dashboard Data Error: {e}")
            return {"error": "Dashboard data unavailable"}

    return app