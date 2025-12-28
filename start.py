import os
import sys
import asyncio
import logging
import webbrowser
import uvicorn

# --- 1. SUPER PATH FIX ---
current_dir = os.getcwd()
inner_dir = os.path.join(current_dir, "agent50_core")
sys.path.append(current_dir)
sys.path.append(inner_dir)

# --- 2. REAL KEYS (SECURED FOR GITHUB UPLOAD) ---
# Note: Asli keys ko kabhi bhi code me hardcode karke GitHub par nahi dalte.
# Jab aap local chalayen to yahan keys wapis daal sakte hain ya .env file use karein.
os.environ["GEMINI_API_KEY"] = ""
os.environ["RENDER_API_KEY"] = ""
os.environ["GITHUB_TOKEN"] = ""  # Yahan se secret hata diya gaya hai
os.environ["RAILWAY_API_TOKEN"] = ""

# --- 3. LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Agent50")

async def main():
    print(f"\n🚀 LAUNCHING AGENT 50 from {current_dir}...\n")
    
    try:
        from agent50_core.memory.memory_manager import MemoryManager
        from agent50_core.console_server import create_app
        from agent50_core.monitor.health_monitor_core import HealthMonitorCore
        from agent50_core.monitor.metrics_collector import MetricsCollector
        from agent50_core.monitor.alert_correlator import AlertCorrelationEngine
        from agent50_core.monitor.auto_remediation import AutoRemediationEngine
        from agent50_core.deployer.deploy_orchestrator import DeployOrchestrator
        
        print("✅ Core Modules Loaded Successfully.")
        
        # Initialize
        memory = MemoryManager()
        deployer = DeployOrchestrator(memory)
        health = HealthMonitorCore(memory)
        metrics = MetricsCollector(memory)
        alerts = AlertCorrelationEngine(memory)
        
        # --- FIX: Removed 'deployer' from here as per your error ---
        remediation = AutoRemediationEngine(memory) 
        
        # Wiring
        metrics.set_health_monitor(health)
        remediation.set_health_monitor(health)

        # Services Start
        await health.start()
        await metrics.start()
        
        # API Server
        app = create_app(memory, health, metrics, alerts, remediation, deployer)
        
        # Browser Open (Seedha Dashboard)
        url = "http://localhost:8000"
        print(f"\n🎉 SYSTEM LIVE! Opening Dashboard: {url}")
        webbrowser.open(url)

        # Server Run
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        print(f"Python Path: {sys.path}")
    except Exception as e:
        print(f"\n❌ SYSTEM ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())