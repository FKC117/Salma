import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')

# Setup Django
django.setup()

from analytics.services.google_ai_service import GoogleAIService

def test_google_ai():
    try:
        print("Testing Google AI Service...")
        service = GoogleAIService()
        print(f"Service initialized successfully")
        print(f"API Key exists: {bool(service.api_key)}")
        print(f"Model name: {service.model_name}")
        
        # Test a simple prompt
        print("\nTesting simple prompt...")
        result = service.generate_response("Hello, how are you?", user_id=1)
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Response: {result['response'][:100]}...")
            print(f"Tokens used: {result['tokens_used']}")
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_ai()