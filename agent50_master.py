"""
agent50_master.py (SUPREME CORE - NO EXCUSES EDITION)
"""
import os
import shutil
import architect_core
import code_weaver

def build_project(project_name, blueprint):
    base_path = os.path.join("projects", project_name)
    
    # 1. CLEAN SLATE PROTOCOL
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
    os.makedirs(base_path)
    os.makedirs(os.path.join(base_path, "templates")) # Frontend folder
    
    print(f"\n🔨 BUILDER: Creating '{project_name}'...")
    
    # 2. GENERATE BACKEND
    for f in blueprint["stack"]:
        print(f"... Weaving Backend: {f}")
        content = code_weaver.generate_file_content(f, blueprint)
        with open(os.path.join(base_path, f), "w") as file:
            file.write(content)

    # 3. GENERATE FRONTEND (HTML)
    for page in blueprint["frontend"]:
        print(f"... Weaving Frontend: {page}")
        content = code_weaver.generate_file_content(page, blueprint)
        with open(os.path.join(base_path, "templates", page), "w") as file:
            file.write(content)
            
    # 4. DEPENDENCIES
    with open(os.path.join(base_path, "requirements.txt"), "w") as f:
        f.write(code_weaver.generate_file_content("requirements.txt", blueprint))

    print(f"✅ BUILD COMPLETE: {base_path}")
    print(f"👉 Frontend Templates located in: {base_path}/templates")

def main():
    print("==============================================")
    print("🤖 AGENT 50 SUPREME: FULL STACK ARCHITECT")
    print("==============================================")
    
    p_name = input("Project Name: ")
    prompt = input("Describe System (e.g. 'Food Delivery with drivers'): ")
    
    # 1. ARCHITECT
    blueprint = architect_core.solve_architecture(prompt)
    
    # 2. BUILD
    build_project(p_name, blueprint)
    
    # 3. VERIFY
    print("\n🛡️ STATUS: READY FOR DEPLOYMENT.")
    print("   Run: cd projects/" + p_name + " && python app.py")

if __name__ == "__main__":
    main()