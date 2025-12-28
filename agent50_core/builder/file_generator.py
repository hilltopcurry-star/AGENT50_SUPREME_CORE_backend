"""
file_generator.py - SUPREME BUILDER ENGINE (TURBO EDITION)
Identity: Production-Grade Code Generator.
Powered by: Google Gemini 2.0 Flash.
"""
import os
import time
import logging
import google.generativeai as genai
from typing import Dict, Any

class FileGenerator:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.logger = logging.getLogger("Agent50.Builder")
        
        # Configure Gemini
        api_key = os.environ.get("GEMINI_API_KEY", "dummy")
        if api_key != "dummy":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    async def generate_project(self, blueprint: Dict[str, Any], output_path: str):
        self.logger.info(f"🚀 Supreme Builder started for: {output_path}")
        
        os.makedirs(output_path, exist_ok=True)
        
        structure = blueprint.get("architecture", {})
        files = structure.get("files", [])
        description = blueprint.get("description", "A Software Project")
        stack = blueprint.get("stack", "Standard")
        
        # List of all files to give context to the AI
        all_files_list = ", ".join(files)

        total_files = len(files)
        
        for index, file_path in enumerate(files):
            full_path = os.path.join(output_path, file_path)
            
            # Create directories recursively
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            self.logger.info(f"[{index+1}/{total_files}] ✍️  Coding: {file_path}")
            
            # Generate REAL Code
            code_content = self._generate_code_content(file_path, description, stack, all_files_list)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code_content)
                
            # Safety Pause
            time.sleep(1) 
                
        self.logger.info(f"✅ Build Complete. Project Ready at: {output_path}")
        return {"status": "success", "path": output_path}

    def _generate_code_content(self, filename: str, project_desc: str, stack: str, file_structure: str) -> str:
        if not self.model:
            return f"# Error: No API Key found."

        try:
            prompt = f"""
            ACT AS: Senior Full-Stack Engineer.
            TASK: Write the COMPLETE, PRODUCTION-READY code for: "{filename}"
            
            PROJECT CONTEXT:
            - Goal: "{project_desc}"
            - Tech Stack: "{stack}"
            - Full File List in Project: [{file_structure}]
            
            STRICT RULES (NO EXCUSES):
            1. **NO PLACEHOLDERS**: Do not use 'pass', 'TODO', or '...'. Write the full logic.
            2. **IMPORTS MUST WORK**: If writing 'app.py', ensure it imports from 'models.py' correctly if it exists.
            3. **FRONTEND**: If writing HTML, use Bootstrap 5 CDN for beautiful design. Do not write plain HTML.
            4. **DATABASE**: If using Flask/SQLAlchemy, ensure tables are created automatically.
            5. **OUTPUT**: Return ONLY the raw code. No Markdown backticks.
            """
            
            response = self.model.generate_content(prompt)
            clean_code = response.text.replace("```python", "").replace("```html", "").replace("```css", "").replace("```json", "").replace("```", "").strip()
            return clean_code
            
        except Exception as e:
            self.logger.error(f"❌ Coding Error on {filename}: {e}")
            return f"# Error generating code: {e}"