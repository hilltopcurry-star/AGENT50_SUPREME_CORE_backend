import json
import re

class ArchitectureEngine:
    def __init__(self):
        self.memory = []

    def analyze_intent(self, user_prompt):
        """
        Ye function user ki baat sun kar Technical Blueprint banata hai.
        Dummy nahi hai - ye keywords aur logic use karke faisla karta hai.
        """
        user_prompt = user_prompt.lower()
        
        # 1. Project Name Extract Karna (Smart Logic)
        project_name = "startup_app" # Default
        if "taxi" in user_prompt: project_name = "taxi_management_system"
        elif "food" in user_prompt: project_name = "food_delivery_portal"
        elif "e-commerce" in user_prompt or "shop" in user_prompt: project_name = "online_store_v1"
        elif "build a" in user_prompt:
            # "Build a X" -> X ko naam bana lo
            parts = user_prompt.split("build a ")
            if len(parts) > 1:
                raw_name = parts[1].split(" ")[0]
                project_name = f"{raw_name}_app"

        # 2. Archetype Detection (Kis tarah ki app hai?)
        archetype = "saas" # Default
        
        # ✅ FIX: Yahan 'w' missing tha, maine laga diya hai
        if any(w in user_prompt for w in ["dashboard", "admin", "panel", "management"]):
            archetype = "dashboard"
        elif any(w in user_prompt for w in ["shop", "store", "sell", "cart", "commerce"]):
            archetype = "ecommerce"
        elif any(w in user_prompt for w in ["api", "backend", "server"]):
            archetype = "backend_api"

        # 3. Stack Selection (Decision Making)
        stack = {
            "frontend": "html_css_tailwind",
            "backend": "flask",
            "database": "sqlite" # Default light DB
        }

        # 4. Feature Extraction (Kya kya chahiye?)
        features = ["basic_structure"]
        if "login" in user_prompt or "auth" in user_prompt or archetype == "dashboard":
            features.append("user_authentication")
        if "chart" in user_prompt or "analytics" in user_prompt or archetype == "dashboard":
            features.append("data_visualization")
        if "pay" in user_prompt or "stripe" in user_prompt:
            features.append("payment_gateway")

        # 5. The Blueprint (Final Naksha)
        blueprint = {
            "project_name": project_name,
            "archetype": archetype,
            "stack": stack,
            "features": features,
            "status": "BLUEPRINT_LOCKED"
        }
        
        self.memory.append(blueprint)
        return blueprint