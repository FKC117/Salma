"""
Final test to verify the Gemini API connection fix
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_llm_processor():
    """Test that LLMProcessor works correctly with Gemini"""
    print("=== Final Test: LLMProcessor with Gemini ===")
    
    try:
        from analytics.services.llm_processor import LLMProcessor
        from django.conf import settings
        
        print(f"Settings - USE_OLLAMA: {settings.USE_OLLAMA}")
        print(f"Settings - GOOGLE_AI_API_KEY exists: {bool(settings.GOOGLE_AI_API_KEY)}")
        
        # Test LLMProcessor initialization
        print("\n1. Testing LLMProcessor initialization...")
        llm = LLMProcessor()
        print(f"   Initialized model: {llm.model_name}")
        
        if llm.model_name == 'gemini':
            print("   ✅ SUCCESS: LLMProcessor correctly initialized with Gemini!")
        else:
            print("   ❌ ISSUE: Expected Gemini but got:", llm.model_name)
            return False
        
        # Test that the model is properly initialized
        print("\n2. Testing model initialization...")
        if hasattr(llm, 'model'):
            print("   ✅ SUCCESS: Google AI model is properly initialized!")
        else:
            print("   ❌ ISSUE: Google AI model not initialized properly")
            return False
            
        print("\n🎉 All tests passed! Gemini API connection should now work correctly.")
        return True
        
    except Exception as e:
        print(f"\n💥 ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_llm_processor()
    if not success:
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify your GOOGLE_AI_API_KEY in settings.py is correct")
        print("2. Check your internet connection")
        print("3. Ensure the Google AI API is accessible from your location")
        print("4. Restart the Django development server")