"""
agent_fixer.py - The Self-Healing Module (Auto-Fixer with Key)
Identity: Debugger & Fixer.
Function: Reads the broken file, takes the error, and forces Agent 50 to rewrite it.
"""
import os
import google.generativeai as genai

# ==========================================
# 👇 AAPKI API KEY YAHAN SET HAI 👇
# ==========================================
MY_API_KEY = "AIzaSyBY0X4Gv16SgFMoJBCEAo2uTbHy6KTmHWg"

# --- CONFIGURATION ---
PROJECT_NAME = "taskmaster_pro"
FILE_TO_FIX = "app.py"
ERROR_MSG = "AttributeError: 'Flask' object has no attribute 'before_first_request'. (Use 'with app.app_context():' instead)"

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "projects", PROJECT_NAME, FILE_TO_FIX)

# Configure Gemini
genai.configure(api_key=MY_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def fix_the_code():
    if not os.path.exists(FILE_PATH):
        print(f"❌ File not found: {FILE_PATH}")
        return

    print(f"🩺 Agent 50 Doctor is examining: {FILE_TO_FIX}...")
    
    # 1. Read the Broken Code
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        broken_code = f.read()

    # 2. Scold Agent 50 & Demand a Fix
    prompt = f"""
    ACT AS: Senior Python Debugger.
    TASK: Fix the following Python code based on the error provided.
    
    BROKEN CODE:
    ```python
    {broken_code}
    ```
    
    ERROR ENCOUNTERED:
    {ERROR_MSG}
    
    INSTRUCTIONS:
    1. The error happens because 'before_first_request' is removed in Flask 3.0.
    2. Replace it with the modern 'with app.app_context(): db.create_all()' approach inside 'if __name__ == "__main__":'.
    3. Keep the rest of the logic exactly the same.
    4. RETURN ONLY THE FIXED CODE. NO MARKDOWN. NO EXPLANATIONS.
    """

    print("🧠 Consulting Gemini Brain for a solution...")
    try:
        response = model.generate_content(prompt)
        fixed_code = response.text.replace("```python", "").replace("```", "").strip()

        # 3. Overwrite the File automatically
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write(fixed_code)

        print(f"✅ FIXED! Agent 50 has rewritten '{FILE_TO_FIX}'.")
        print("🚀 You can now run the app.")
        
    except Exception as e:
        print(f"❌ Error connecting to Gemini: {e}")

if __name__ == "__main__":
    fix_the_code()