import os
from pathlib import Path

def validate_structure(base_path, required_folders, required_files):
    """
    Check karta hai ke zaroori files aur folders ban gaye ya nahi.
    """
    base = Path(base_path)
    missing_items = []

    # 1. Check Folders
    for folder in required_folders:
        folder_path = base / folder
        if not folder_path.exists():
            missing_items.append(f"📁 Missing Folder: {folder}")

    # 2. Check Files
    for file in required_files:
        file_path = base / file
        if not file_path.exists():
            missing_items.append(f"📄 Missing File: {file}")

    # Result
    if missing_items:
        print("❌ Structure Validation Failed!")
        for item in missing_items:
            print(f"   - {item}")
        return False
    else:
        print("✅ Structure Validation Passed (All files present)")
        return True