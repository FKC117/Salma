"""
Test script to verify the Google AI model works with the updated settings
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_google_ai_model():
    """Test if the configured Google AI model works correctly"""
    print("Testing Google AI model configuration...")
    
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        # Get configuration from settings
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
        model_name = getattr(settings, 'GOOGLE_AI_MODEL', None)
        
        if not api_key:
            print("✗ GOOGLE_AI_API_KEY not found in settings")
            return False
            
        if not model_name:
            print("✗ GOOGLE_AI_MODEL not found in settings")
            return False
        
        print(f"✓ API Key: {api_key[:10]}...{api_key[-5:]}")
        print(f"✓ Model Name: {model_name}")
        
        # Configure Google AI
        genai.configure(api_key=api_key)
        
        # Create model instance
        model = genai.GenerativeModel(model_name=model_name)
        
        print(f"✓ Model instance created successfully")
        
        # Test generation
        print("\n--- Testing Text Generation ---")
        response = model.generate_content("Say 'Hello, World!' in a friendly way")
        print(f"✓ Response: {response.text}")
        
        # Test with a more complex prompt
        print("\n--- Testing Complex Generation ---")
        response2 = model.generate_content("Explain what artificial intelligence is in one sentence")
        print(f"✓ Response: {response2.text}")
        
        print("\n🎉 Google AI model is working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_processor():
    """Test the LLMProcessor directly"""
    print("\n=== Testing LLMProcessor ===")
    
    try:
        from django.contrib.auth import get_user_model
        from analytics.services.llm_processor import LLMProcessor
        
        # Get or create a test user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_ai_user',
                email='test_ai@example.com',
                password='testpassword'
            )
            print("✓ Created test user")
        else:
            print("✓ Using existing user")
        
        # Create LLM processor
        llm_processor = LLMProcessor()
        print("✓ LLMProcessor created successfully")
        
        # Test text generation
        print("\n--- Testing LLMProcessor.generate_text ---")
        result = llm_processor.generate_text(
            prompt="What is the capital of France?",
            user=user
        )
        
        print(f"✓ Generated text: {result['text']}")
        print(f"✓ Input tokens: {result['input_tokens']}")
        print(f"✓ Output tokens: {result['output_tokens']}")
        print(f"✓ Total cost: ${result['total_cost']:.6f}")
        
        print("\n🎉 LLMProcessor is working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error in LLMProcessor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Google AI integration with updated configuration...\n")
    
    success1 = test_google_ai_model()
    success2 = test_llm_processor()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Google AI integration is working correctly.")
        print("You can now restart the Django server and test the chat functionality.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")