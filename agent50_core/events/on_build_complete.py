from agent50_core.validators.structure_check import validate_structure
from agent50_core.validators.deploy_check import check_render_readiness
from agent50_core.validators.security_check import scan_for_secrets
import json
import os

def handle_build_completion(project_path, app_type):
    print(f"\n⚡ EVENT: Build Complete for {app_type}. Starting Auto-Scan...")

    # 1. Structure Check
    # (Yahan hum contracts se required files utha sakte hain, abhi hardcode kar rahe hain)
    req_folders = ["templates", "static"] if app_type == "delivery" else []
    req_files = ["app.py", "requirements.txt"]
    
    is_structure_ok = validate_structure(project_path, req_folders, req_files)
    
    # 2. Security Check
    is_safe = scan_for_secrets(project_path)

    # 3. Deploy Readiness
    is_ready = check_render_readiness(project_path)

    if is_structure_ok and is_safe and is_ready:
        print("✅ EVENT RESULT: Project is 100% Ready for Deployment.")
        return True
    else:
        print("❌ EVENT RESULT: Issues found. Auto-Fixing needed.")
        return False