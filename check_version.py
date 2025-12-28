import google.generativeai as genai
import os

os.environ["GEMINI_API_KEY"] = "AIzaSyBY0X4Gv16SgFMoJBCEAo2uTbHy6KTmHWg"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

print("\n🔍 MODELS LIST:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")