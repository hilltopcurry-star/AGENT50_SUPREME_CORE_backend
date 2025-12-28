import sys
import os
import asyncio

# Raste (Path) set karna taake python files dhoond sake
sys.path.append(os.path.abspath("agent50_core"))

try:
    print("⏳ Checking Deployer System...")
    from agent50_core.deployer.deploy_orchestrator import DeployOrchestrator
    print("✅ Deploy Orchestrator Found!")
    
    from agent50_core.deployer.docker_adapter import DockerAdapter
    print("✅ Docker Adapter Found!")

    from agent50_core.deployer.vercel_adapter import VercelAdapter
    print("✅ Vercel Adapter Found!")
    
    print("\n🎉 MUBARAK HO! Aapka Deployer System Zinda hai.")
    print("Hum isay ab 'TaskMaster_Pro' par test kar sakte hain.")

except ImportError as e:
    print(f"\n❌ CRITICAL ERROR: Koi file missing hai ya connect nahi ho rahi.")
    print(f"Error Details: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")