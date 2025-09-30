#!/usr/bin/env python
"""
Simple test to verify Gemini API connection fixes
"""
import os
import sys

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytical'))

def check_settings_fix():
    """Check if the key fix (USE_OLLAMA = False) is in place"""
    print("=== Checking Key Fix ===")
    
    try:
        # Read settings file directly
        settings_file = os.path.join(os.path.dirname(__file__), 'analytical', 'analytical', 'settings.py')
        
        with open(settings_file, 'r') as f:
            content = f.read()
        
        # Check if USE_OLLAMA = False is in the file
        if 'USE_OLLAMA = False' in content:
            print("✅ GOOD: USE_OLLAMA is set to False in settings.py")
            return True
        elif 'USE_OLLAMA = True' in content:
            print("❌ ISSUE: USE_OLLAMA is still set to True in settings.py")
            return False
        else:
            print("⚠️  WARNING: Could not find USE_OLLAMA setting in settings.py")
            return False
            
    except Exception as e:
        print(f"Error checking settings: {str(e)}")
        return False

def check_google_ai_fix():
    """Check if Google AI generation is enabled"""
    print("\n=== Checking Google AI Fix ===")
    
    try:
        # Read LLM processor file
        llm_file = os.path.join(os.path.dirname(__file__), 'analytical', 'analytics', 'services', 'llm_processor.py')
        
        with open(llm_file, 'r') as f:
            content = f.read()
        
        # Check if the Google AI generation is enabled (not commented out)
        if '# response = self.model.generate_content(prompt)' in content:
            print("❌ ISSUE: Google AI generation is still commented out")
            return False
        elif 'response = self.model.generate_content(prompt)' in content:
            print("✅ GOOD: Google AI generation is enabled")
            return True
        else:
            print("⚠️  WARNING: Could not find Google AI generation code")
            return False
            
    except Exception as e:
        print(f"Error checking LLM processor: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Testing fixes for Gemini API connection issues...\n")
    
    settings_fix = check_settings_fix()
    google_ai_fix = check_google_ai_fix()
    
    print("\n=== Summary ===")
    print(f"Settings fix (USE_OLLAMA = False): {'✅ PASS' if settings_fix else '❌ FAIL'}")
    print(f"Google AI fix (generation enabled): {'✅ PASS' if google_ai_fix else '❌ FAIL'}")
    
    if settings_fix and google_ai_fix:
        print("\n🎉 All critical fixes are in place!")
        print("Gemini API should now work correctly in the UI.")
        print("\nTo test:")
        print("1. Restart the Django development server")
        print("2. Open the chat interface in your browser")
        print("3. Select 'Google Gemini' from the model dropdown")
        print("4. Send a test message")
    else:
        print("\n❌ Some fixes are missing. Please check the output above.")

if __name__ == "__main__":
    main()