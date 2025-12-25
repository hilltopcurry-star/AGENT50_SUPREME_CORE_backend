import requests

# 🔗 Live Server URL
url = "https://agent50-supreme-core-backend-server.onrender.com/orders"

# 🍔 Order Data
data = {
    "restaurant_id": "res_1", 
    "total_amount": 850, 
    "items": ["Special Biryani x2", "Coke x2"]
}

# 🚀 Send Order
try:
    resp = requests.post(url, json=data)
    print("✅ Server Response:", resp.json())
except Exception as e:
    print("❌ Error:", e)