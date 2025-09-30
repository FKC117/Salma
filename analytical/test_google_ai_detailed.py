import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')

# Setup Django
django.setup()

def test_google_ai_detailed():
    try:
        print("Testing Google AI Service...")
        
        # Import Django settings to check configuration
        from django.conf import settings
        print(f"USE_OLLAMA: {settings.USE_OLLAMA}")
        print(f"GOOGLE_AI_API_KEY exists: {bool(settings.GOOGLE_AI_API_KEY)}")
        print(f"GOOGLE_AI_MODEL: {settings.GOOGLE_AI_MODEL}")
        
        # Import Google AI service
        from analytics.services.google_ai_service import GoogleAIService
        print("GoogleAIService imported successfully")
        
        # Initialize service
        service = GoogleAIService()
        print(f"Service initialized")
        print(f"Service API key: {service.api_key[:10]}...")  # Show first 10 chars for security
        print(f"Service model name: {service.model_name}")
        
        # Test API key validation
        print("\nTesting API key validation...")
        is_valid = service.validate_api_key()
        print(f"API key valid: {is_valid}")
        
        if is_valid:
            # Test a simple prompt
            print("\nTesting simple prompt...")
            result = service.generate_response("Hello, how are you?", user_id=1)
            print(f"Success: {result['success']}")
            if result['success']:
                print(f"Response: {result['response'][:100]}...")
                print(f"Input tokens: {result['input_tokens']}")
                print(f"Output tokens: {result['output_tokens']}")
                print(f"Total tokens: {result['total_tokens']}")
                print(f"Cost: {result['cost']}")
            else:
                print(f"Error: {result['error']}")
        else:
            print("API key validation failed")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_ai_detailed()