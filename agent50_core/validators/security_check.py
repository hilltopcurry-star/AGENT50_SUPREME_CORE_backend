import os
from pathlib import Path

def scan_for_secrets(base_path):
    """
    Files ko scan karta hai taake API Keys leak na hon.
    """
    base = Path(base_path)
    suspicious_patterns = ["sk-", "AIza", "API_KEY", "SECRET_KEY"]
    leaks = []

    # Sirf .py files check karein
    for file_path in base.glob("**/*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
            for pattern in suspicious_patterns:
                if pattern in content and "os.getenv" not in content:
                    # Agar key hardcoded hai (env variable nahi hai)
                    leaks.append(f"⚠️ Potential Secret Leak in {file_path.name}: '{pattern}' found")
        except:
            continue

    if leaks:
        print("⚠️ Security Alert!")
        for leak in leaks:
            print(f"   - {leak}")
        print("   -> Tip: Use .env file for secrets.")
        return False
    
    print("✅ Security Scan Passed (No hardcoded secrets found)")
    return True