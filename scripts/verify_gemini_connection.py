"""Verify Gemini API Connection and List Models.

This script:
1. Configures Gemini with the stored API key.
2. Lists all available models accessible with the key.
3. Attempts to generate text using the configured waterfall models.
"""
import sys
import os
import asyncio
import google.generativeai as genai

# Add project root to python path
sys.path.append(os.getcwd())

from frontend.services.ai_service import get_config_manager

async def verify_connection():
    print("=" * 60)
    print("🤖 Gemini AI Connection Verification & Model List")
    print("=" * 60)
    
    config = get_config_manager()
    api_key = config.api_key
    
    if not api_key:
        print("❌ No API Key found in AI Config Manager.")
        return

    masked_key = f"{api_key[:5]}...{api_key[-5:]}"
    print(f"🔑 Using API Key: {masked_key}")
    
    genai.configure(api_key=api_key)
    
    # 1. List Available Models
    print("\n📋 Available Models for this Key:")
    available_model_names = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"   - {m.name} ({m.display_name})")
                available_model_names.append(m.name)
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        if "400" in str(e) or "API key" in str(e):
             print("   (Likely invalid API Key)")
             return

    # 2. Test Configured Models
    print("\n🧪 Testing Configured Waterfall Models:")
    active_models = config.active_models
    
    success = False
    for model_name in active_models:
        print(f"   ► Testing '{model_name}'...", end=" ")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hello")
            print("✅ OK")
            success = True
            break # Stop at first working model
        except Exception as e:
            print(f"❌ Failed")
            # print(f"      Error: {e}")

    if success:
        print("\n✅ Verification Successful! At least one model is working.")
    else:
        print("\n❌ Verification Failed! No configured models are working with this key.")
        print("   Please update 'ai_settings.json' with one of the Available Models listed above.")
        
        # Suggest a fix
        suggested = [m for m in available_model_names if "flash" in m or "pro" in m]
        if suggested:
            print(f"\n💡 Suggestion: Try using '{suggested[0].replace('models/', '')}'")

if __name__ == "__main__":
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(verify_connection())
