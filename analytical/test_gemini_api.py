import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')

# Setup Django
django.setup()

def test_gemini_api():
    try:
        print("Testing Google AI API directly...")
        
        # Import Django settings to check configuration
        from django.conf import settings
        print(f"GOOGLE_AI_API_KEY exists: {bool(settings.GOOGLE_AI_API_KEY)}")
        print(f"GOOGLE_AI_MODEL: {settings.GOOGLE_AI_MODEL}")
        
        # Import Google Generative AI
        import google.generativeai as genai
        print("Google Generative AI imported successfully")
        
        # Configure API key
        api_key = settings.GOOGLE_AI_API_KEY
        genai.configure(api_key=api_key)
        print("Google AI configured successfully")
        
        # List available models
        print("\nListing available models...")
        for model in genai.list_models():
            print(f"Model: {model.name}")
        
        # Test with the specific model
        print(f"\nTesting with model: {settings.GOOGLE_AI_MODEL}")
        model = genai.GenerativeModel(settings.GOOGLE_AI_MODEL)
        print("Model created successfully")
        
        # Test generation
        print("\nTesting generation...")
        response = model.generate_content("Hello, how are you?")
        print(f"Response: {response.text[:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_api()