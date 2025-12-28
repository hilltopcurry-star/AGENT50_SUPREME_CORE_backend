"""
architect_core.py
MODULE: SUPREME ARCHITECT (v4.0 - SCHEMA DRIVEN)
Description: Generates a JSON Schema for ANY system (Entities, Roles, UI).
"""
import json
import os

MEMORY_FILE = "agent_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f: return json.load(f)
        except: pass
    return {"successful_patterns": {}, "learned_fixes": {}}

def solve_architecture(user_input):
    prompt = user_input.lower()
    
    # 1. CORE SYSTEM CONFIG
    blueprint = {
        "sys_config": {"DB_URI": "PostgreSQL_Neon", "AUTH_MODE": "JWT_Extended"},
        "stack": ["app.py", "models.py", "auth.py", "routes.py", "extensions.py"],
        "frontend": [], # List of HTML pages to generate
        "roles": ["admin", "user"],
        "entities": []  # Dynamic Database Tables
    }

    # 2. DYNAMIC SCHEMA GENERATION (The "Intelligence")
    # PATTERN: MULTI-VENDOR DELIVERY (Uber/Foodpanda)
    if any(x in prompt for x in ["food", "delivery", "uber", "grab", "driver"]):
        blueprint["roles"] = ["admin", "customer", "restaurant_owner", "driver"]
        blueprint["entities"] = [
            {"name": "Restaurant", "fields": [
                ("name", "String(100)"), ("address", "String(200)"), ("is_active", "Boolean")
            ]},
            {"name": "MenuItem", "fields": [
                ("name", "String(100)"), ("price", "Float"), ("restaurant_id", "ForeignKey('restaurant.id')")
            ]},
            {"name": "Order", "fields": [
                ("customer_id", "ForeignKey('user.id')"), ("restaurant_id", "ForeignKey('restaurant.id')"),
                ("driver_id", "ForeignKey('user.id')"), ("status", "String(50)"), ("total", "Float")
            ]},
            {"name": "Tracking", "fields": [
                ("driver_id", "ForeignKey('user.id')"), ("lat", "Float"), ("lng", "Float")
            ]}
        ]
        blueprint["frontend"] = ["login.html", "customer_dashboard.html", "driver_dashboard.html", "restaurant_panel.html", "admin_panel.html"]

    # PATTERN: E-COMMERCE (Amazon/Shopify)
    elif any(x in prompt for x in ["shop", "store", "ecommerce", "sell"]):
        blueprint["roles"] = ["admin", "buyer", "seller"]
        blueprint["entities"] = [
            {"name": "Product", "fields": [("name", "String"), ("price", "Float"), ("stock", "Integer"), ("seller_id", "ForeignKey('user.id')")]},
            {"name": "Cart", "fields": [("user_id", "ForeignKey('user.id')"), ("items_json", "Text")]},
            {"name": "Order", "fields": [("user_id", "ForeignKey('user.id')"), ("status", "String"), ("total", "Float")]}
        ]
        blueprint["frontend"] = ["login.html", "shop.html", "cart.html", "seller_dashboard.html"]
        
    # PATTERN: GENERIC SAAS (Default)
    else:
        blueprint["entities"] = [
            {"name": "Item", "fields": [("name", "String"), ("owner_id", "ForeignKey('user.id')")]}
        ]
        blueprint["frontend"] = ["login.html", "dashboard.html"]

    print(f"🧠 ARCHITECT: Defined {len(blueprint['entities'])} Entities and {len(blueprint['frontend'])} UI Pages.")
    return blueprint