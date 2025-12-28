"""
deploy_app.py - The Deployment Trigger (FINAL LOCATION FIX)
Identity: Release Manager.
Function: Moves into the project folder, runs the empty deployer, and comes back.
"""
import sys
import os
import inspect

# Agent 50 Core ka rasta set karna
sys.path.append(os.path.abspath("agent50_core"))

try:
    from agent50_core.deployer.vercel_adapter import VercelAdapter
    from agent50_core.deployer.deploy_orchestrator import DeployOrchestrator
except ImportError:
    print("⚠️ Warning: Adapters not found directly. Using placeholders.")

def start_deployment():
    print("========================================")
    print("🚀 AGENT 50: AUTO-DEPLOYMENT SYSTEM")
    print("========================================")

    # 1. Project Select
    project_name = input("📁 Project Folder Name (e.g., taskmaster_pro): ").strip()
    if not project_name:
        project_name = "taskmaster_pro"
    
    current_dir = os.getcwd()
    base_path = os.path.join(current_dir, "projects", project_name)
    
    if not os.path.exists(base_path):
        print(f"❌ Error: Project folder nahi mila: {base_path}")
        return

    print(f"✅ Project Selected: {project_name}")

    # 2. Platform Select
    print("\nKahan Deploy karna hai?")
    print("1. Vercel (Free Cloud Hosting)")
    print("2. Docker (Local Container)")
    choice = input("👉 Enter 1 or 2: ").strip()

    # 3. Environment & Execution
    if choice == "1":
        print("\n🔑 Vercel Token (Press Enter to skip for simulation).")
        token = input("Paste Vercel Token: ").strip()
        os.environ["VERCEL_TOKEN"] = token if token else "simulation_mode"
        
        print(f"\n⏳ Switching Directory to Project & Deploying...")
        
        try:
            # Step A: Initialize
            try:
                adapter = VercelAdapter()
            except TypeError:
                class FakeMem: pass
                adapter = VercelAdapter(memory=FakeMem())

            # Step B: CHANGE DIRECTORY (Ye hai wo Jaadu) 🪄
            os.chdir(base_path) 
            
            # Step C: Call without arguments
            try:
                result = adapter.deploy() 
            finally:
                # Wapis apni jagah aana zaroori hai
                os.chdir(current_dir)

            # AGAR YAHAN TAK AA GAYE TO SUCCESS HAI
            print("\n" + "="*40)
            print("🎉 SUCCESS (SIMULATION COMPLETE)!")
            print("Agent 50 ne files pack kar li hain.")
            print("Kyunke ye Simulation thi, koi Live URL nahi hai.")
            print("="*40)

        except Exception as e:
            # Wapis directory change agar error aye
            os.chdir(current_dir)
            print(f"❌ Adapter Error: {e}")

    elif choice == "2":
        class FakeMem: pass
        orchestrator = DeployOrchestrator(memory=FakeMem())
        result = orchestrator.deploy(project_path=base_path, platform="docker")

    else:
        print("❌ Ghalat Option.")

if __name__ == "__main__":
    start_deployment()