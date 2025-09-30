"""
Test script to verify the Gemini API fix works correctly
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_gemini_initialization():
    """Test that LLMProcessor correctly initializes with Gemini when USE_OLLAMA=False"""
    print("=== Testing Gemini API Initialization Fix ===")
    
    try:
        from analytics.services.llm_processor import LLMProcessor
        from django.conf import settings
        
        print(f"USE_OLLAMA setting: {settings.USE_OLLAMA}")
        print(f"GOOGLE_AI_API_KEY exists: {bool(settings.GOOGLE_AI_API_KEY)}")
        
        # Test default initialization (should use settings to determine model)
        llm_processor = LLMProcessor()
        print(f"Default LLMProcessor model_name: {llm_processor.model_name}")
        
        # Test explicit Gemini initialization
        llm_gemini = LLMProcessor(model_name='gemini')
        print(f"Explicit Gemini LLMProcessor model_name: {llm_gemini.model_name}")
        
        # Verify the fix worked
        if settings.USE_OLLAMA == False and settings.GOOGLE_AI_API_KEY:
            expected_model = 'gemini'
        else:
            expected_model = 'ollama'
            
        print(f"Expected model based on settings: {expected_model}")
        
        if llm_processor.model_name == expected_model:
            print("✅ SUCCESS: LLMProcessor correctly initialized based on settings!")
            return True
        else:
            print("❌ FAILURE: LLMProcessor did not initialize correctly")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_gemini_initialization()
    if success:
        print("\n🎉 Gemini API initialization fix is working correctly!")
    else:
        print("\n💥 Gemini API initialization fix needs more work.")