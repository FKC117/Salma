"""
Test script to check available Google AI models with the provided API key
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_available_models():
    """Test which Google AI models are available with the current API key"""
    print("Testing available Google AI models...")
    
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        # Get API key from settings
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
        if not api_key:
            print("✗ GOOGLE_AI_API_KEY not found in settings")
            return False
        
        print(f"✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
        
        # Configure Google AI
        genai.configure(api_key=api_key)
        
        # List available models
        print("\n--- Available Models ---")
        try:
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    print(f"✓ {model.name} - {model.display_name}")
        except Exception as e:
            print(f"Could not list models: {str(e)}")
            print("This is normal for some API configurations.")
        
        # Test common models
        common_models = [
            'gemini-pro',
            'gemini-1.0-pro',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-pro-vision'
        ]
        
        print("\n--- Testing Common Models ---")
        working_models = []
        
        for model_name in common_models:
            try:
                model = genai.GenerativeModel(model_name)
                # Test with a simple prompt
                response = model.generate_content("Say 'hello' in one word")
                print(f"✓ {model_name} - Working (response: {response.text.strip()})")
                working_models.append(model_name)
            except Exception as e:
                print(f"✗ {model_name} - Not available ({str(e)})")
        
        print(f"\n--- Summary ---")
        print(f"Working models: {working_models}")
        
        if working_models:
            # Update settings to use the first working model
            first_model = working_models[0]
            print(f"\nRecommendation: Use '{first_model}' as the default model")
            return first_model
        else:
            print("\nNo working models found. Please check your API key and permissions.")
            return None
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    model = test_available_models()
    if model:
        print(f"\n🎉 Recommended model: {model}")
    else:
        print("\n❌ No models available with current configuration")