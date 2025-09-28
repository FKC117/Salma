"""
Detailed test to identify the exact error in chat processing
"""
import os
import sys
import django
import traceback

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.contrib.auth import get_user_model
from analytics.services.llm_processor import LLMProcessor

def test_chat_processing():
    """Test chat processing with detailed error reporting"""
    print("=== Detailed Chat Processing Test ===")
    
    # Get or create a test user
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_user_detailed',
                email='test_detailed@example.com',
                password='testpassword'
            )
            print("✓ Created test user")
        else:
            print("✓ Using existing user")
    except Exception as e:
        print(f"✗ Error getting/creating user: {str(e)}")
        traceback.print_exc()
        return False
    
    # Create LLM processor
    try:
        llm_processor = LLMProcessor()
        print("✓ LLM Processor created successfully")
    except Exception as e:
        print(f"✗ Error creating LLM Processor: {str(e)}")
        traceback.print_exc()
        return False
    
    # Test message processing with detailed error catching
    try:
        print("\n--- Testing process_message with detailed error catching ---")
        print("Message: 'Hello, test message'")
        print("Session ID: None")
        print("Context: {}")
        
        result = llm_processor.process_message(
            user=user,
            message="Hello, test message",
            session_id=None,
            context={}
        )
        
        print("Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        if result.get('success'):
            print("✓ Message processing successful")
            return True
        else:
            print("✗ Message processing failed")
            error = result.get('error', 'Unknown error')
            print(f"Error details: {error}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during message processing: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def test_google_ai_connection():
    """Test if we can connect to Google AI"""
    print("\n=== Testing Google AI Connection ===")
    
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
        if not api_key:
            print("✗ GOOGLE_AI_API_KEY not found in settings")
            return False
        
        print(f"✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
        
        # Test initialization
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✓ Google AI client initialized successfully")
        
        # Test simple generation
        response = model.generate_content("Say hello")
        print(f"✓ Simple generation test: {response.text[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing Google AI connection: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Starting detailed chat processing tests...")
    
    # Test Google AI connection first
    success1 = test_google_ai_connection()
    
    # Test chat processing
    success2 = test_chat_processing() if success1 else False
    
    if success1 and success2:
        print("\n🎉 All tests passed! Chat functionality should be working.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return success1 and success2

if __name__ == "__main__":
    main()