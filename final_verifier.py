"""
final_verifier.py
MODULE: AUTONOMY CONFIRMATION SIGNAL (GAP 3 CLOSED)
Description: Final determinist check. No reflex loop needed if this passes.
"""
import os
import ast
import sys

def check_syntax(filepath):
    """Parses Python file to ensure it's syntactically valid (No half-written code)."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True
    except Exception as e:
        print(f"❌ SYNTAX ERROR in {filepath}: {e}")
        return False

def verify_project(project_path, blueprint):
    print(f"\n🛡️ FINAL VERIFIER: Auditing '{project_path}'...")
    
    files = [f.split(" ")[0] for f in blueprint.get("derived_architecture", [])]
    files.append("extensions.py")
    files.append("requirements.txt")
    
    all_passed = True
    
    # Check 1: File Existence
    for f in files:
        full_path = os.path.join(project_path, f)
        if not os.path.exists(full_path):
            print(f"❌ MISSING FILE: {f}")
            all_passed = False
        else:
            # Check 2: Syntax Validity (for .py files)
            if f.endswith(".py"):
                if not check_syntax(full_path):
                    all_passed = False
    
    if all_passed:
        print("✅ INTEGRITY CHECK: PASSED (All files exist & compile)")
        return True
    else:
        print("❌ INTEGRITY CHECK: FAILED")
        return False