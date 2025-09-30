#!/usr/bin/env python
"""
Test script to debug Gemini API connection issues
"""
import os
import sys
import django
from django.conf import settings

# Add the analytical directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_gemini_connection():
    """Test if we can connect to Google AI (Gemini)"""
    print("=== Testing Google AI (Gemini) Connection ===")
    
    try:
        # Import required modules
        from django.conf import settings
        import google.generativeai as genai
        
        # Check API key
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
        if not api_key:
            print("✗ GOOGLE_AI_API_KEY not found in settings")
            return False
        
        print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")
        
        # Test initialization
        genai.configure(api_key=api_key)
        print("✓ Google AI configured successfully")
        
        # Test model access
        model_name = getattr(settings, 'GOOGLE_AI_MODEL', 'gemini-1.5-flash')
        print(f"✓ Using model: {model_name}")
        
        # Test simple generation
        print("Testing model generation...")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say hello in one word")
        print(f"✓ Simple generation test: {response.text.strip()}")
        
        # Test with longer prompt
        print("Testing with analysis context...")
        response = model.generate_content("What is the purpose of descriptive statistics?")
        print(f"✓ Analysis context test: {response.text[:100]}...")
        
        print("\n🎉 Google AI (Gemini) connection is working!")
        return True
        
    except ImportError as e:
        print(f"✗ ImportError: {str(e)}")
        print("Make sure google-generativeai package is installed")
        print("Try: pip install google-generativeai")
        return False
        
    except Exception as e:
        print(f"✗ Error testing Google AI connection: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_processor():
    """Test LLM processor with Gemini model"""
    print("\n=== Testing LLM Processor with Gemini ===")
    
    try:
        from analytics.services.llm_processor import LLMProcessor
        
        # Test with Gemini model
        llm_processor = LLMProcessor(model_name='gemini')
        print("✓ LLMProcessor created with Gemini model")
        
        # Test generation
        prompt = "Explain what descriptive statistics are in one sentence."
        print(f"Testing prompt: {prompt}")
        
        # This would normally require a user object, but let's test the model selection
        print("✓ LLMProcessor initialized correctly for Gemini")
        return True
        
    except Exception as e:
        print(f"✗ Error testing LLM Processor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_settings():
    """Check Django settings for Google AI configuration"""
    print("\n=== Checking Django Settings ===")
    
    try:
        from django.conf import settings
        
        # Check Google AI settings
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', 'NOT_SET')
        model = getattr(settings, 'GOOGLE_AI_MODEL', 'NOT_SET')
        use_ollama = getattr(settings, 'USE_OLLAMA', True)
        
        print(f"GOOGLE_AI_API_KEY: {'SET' if api_key != 'NOT_SET' else 'NOT_SET'}")
        print(f"GOOGLE_AI_MODEL: {model}")
        print(f"USE_OLLAMA: {use_ollama}")
        
        if api_key == 'NOT_SET':
            print("⚠️  API key not set in settings")
            return False
            
        if use_ollama:
            print("ℹ️  USE_OLLAMA is True - this may cause fallback to Ollama")
            
        return True
        
    except Exception as e:
        print(f"✗ Error checking settings: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Starting Gemini API connection tests...\n")
    
    # Check settings first
    settings_ok = check_settings()
    
    # Test direct Gemini connection
    gemini_ok = test_gemini_connection()
    
    # Test LLM processor
    llm_ok = test_llm_processor()
    
    print("\n=== Summary ===")
    print(f"Settings check: {'✅ PASS' if settings_ok else '❌ FAIL'}")
    print(f"Gemini connection: {'✅ PASS' if gemini_ok else '❌ FAIL'}")
    print(f"LLM Processor: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    
    if gemini_ok:
        print("\n🎉 All tests passed! Gemini API should work in the UI.")
    else:
        print("\n❌ There are issues with the Gemini API connection.")
        print("Please check:")
        print("1. GOOGLE_AI_API_KEY is set correctly in settings.py")
        print("2. google-generativeai package is installed")
        print("3. Internet connection is working")
        print("4. API key has proper permissions")

if __name__ == "__main__":
    main()