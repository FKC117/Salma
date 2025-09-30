#!/usr/bin/env python
"""
Simple test to check the LLM processor model selection logic
"""
import sys
import os

# Add the analytical directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

# Mock Django settings for testing
class MockSettings:
    GOOGLE_AI_API_KEY = 'AIzaSyBZMrHbI623A5Nbjz2QEK1_4nguL5wTm8s'
    GOOGLE_AI_MODEL = 'gemini-flash-latest'
    USE_OLLAMA = True  # This is the issue!
    OLLAMA_URL = 'http://localhost:11434'
    OLLAMA_MODEL = 'deepseek-r1:8b'

# Mock Django conf
import django.conf
django.conf.settings = MockSettings()

def test_model_selection():
    """Test the model selection logic in LLMProcessor"""
    print("=== Testing LLM Processor Model Selection ===")
    
    try:
        # Import the LLMProcessor
        from analytics.services.llm_processor import LLMProcessor
        
        # Test with Ollama (default)
        llm_ollama = LLMProcessor()
        print(f"Default model (should be ollama): {llm_ollama.model_name}")
        
        # Test with explicit Gemini
        llm_gemini = LLMProcessor(model_name='gemini')
        print(f"Gemini model (should be gemini): {llm_gemini.model_name}")
        
        # Check the settings
        print(f"\nSettings:")
        print(f"  USE_OLLAMA: {MockSettings.USE_OLLAMA}")
        print(f"  GOOGLE_AI_API_KEY: {MockSettings.GOOGLE_AI_API_KEY[:10]}...")
        print(f"  GOOGLE_AI_MODEL: {MockSettings.GOOGLE_AI_MODEL}")
        
        if MockSettings.USE_OLLAMA:
            print("\n⚠️  ISSUE FOUND: USE_OLLAMA is set to True")
            print("This causes the LLMProcessor to always fallback to Ollama")
            print("even when Gemini is explicitly selected!")
            print("\n🔧 FIX: Set USE_OLLAMA = False in settings.py")
            
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_model_selection()