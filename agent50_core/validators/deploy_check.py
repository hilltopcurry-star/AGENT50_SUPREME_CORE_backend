import os
from pathlib import Path

def check_render_readiness(base_path):
    """
    Render par deploy hone se pehle mandatory checks.
    """
    base = Path(base_path)
    critical_files = ["requirements.txt", "Procfile", "app.py"]
    errors = []

    print("🔍 Running Pre-Deployment Scan...")

    # 1. Files Check
    for file in critical_files:
        if not (base / file).exists():
            errors.append(f"CRITICAL: {file} is missing! Render will fail.")

    # 2. Content Check (Procfile)
    procfile_path = base / "Procfile"
    if procfile_path.exists():
        content = procfile_path.read_text()
        if "gunicorn" not in content:
            errors.append("WARNING: Procfile does not contain 'gunicorn'. App might not start.")

    if errors:
        print("❌ Deployment Check Failed!")
        for e in errors:
            print(f"   - {e}")
        return False
    
    print("✅ Deployment Check Passed! Ready for Render.")
    return True