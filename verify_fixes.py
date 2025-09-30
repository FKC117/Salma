#!/usr/bin/env python
"""
Verify that the fixes for Gemini API connection are working
"""
import os
import sys

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

def verify_settings():
    """Verify that settings are correct"""
    print("=== Verifying Settings ===")
    
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"USE_OLLAMA: {settings.USE_OLLAMA}")
        print(f"GOOGLE_AI_API_KEY: {'SET' if settings.GOOGLE_AI_API_KEY else 'NOT SET'}")
        print(f"GOOGLE_AI_MODEL: {settings.GOOGLE_AI_MODEL}")
        
        if settings.USE_OLLAMA:
            print("❌ ISSUE: USE_OLLAMA is still True")
            print("   This will cause fallback to Ollama even when Gemini is selected")
            return False
        else:
            print("✅ GOOD: USE_OLLAMA is False")
            
        if not settings.GOOGLE_AI_API_KEY:
            print("❌ ISSUE: GOOGLE_AI_API_KEY is not set")
            return False
        else:
            print("✅ GOOD: GOOGLE_AI_API_KEY is set")
            
        return True
        
    except Exception as e:
        print(f"Error verifying settings: {str(e)}")
        return False

def verify_llm_processor():
    """Verify LLM processor initialization"""
    print("\n=== Verifying LLM Processor ===")
    
    try:
        from analytics.services.llm_processor import LLMProcessor
        
        # Test with Gemini model
        llm = LLMProcessor(model_name='gemini')
        print(f"LLM Processor model_name: {llm.model_name}")
        
        if llm.model_name == 'gemini':
            print("✅ GOOD: LLM Processor correctly initialized with Gemini")
            return True
        else:
            print("❌ ISSUE: LLM Processor did not initialize with Gemini")
            return False
            
    except Exception as e:
        print(f"Error initializing LLM Processor: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("Verifying fixes for Gemini API connection issues...\n")
    
    settings_ok = verify_settings()
    llm_ok = verify_llm_processor()
    
    print("\n=== Summary ===")
    print(f"Settings verification: {'✅ PASS' if settings_ok else '❌ FAIL'}")
    print(f"LLM Processor verification: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    
    if settings_ok and llm_ok:
        print("\n🎉 All fixes verified! Gemini should now work in the UI.")
        print("To test in the UI:")
        print("1. Refresh the chat interface")
        print("2. Select 'Google Gemini' from the model dropdown")
        print("3. Send a test message")
    else:
        print("\n❌ Some issues remain. Please check the output above.")

if __name__ == "__main__":
    main()