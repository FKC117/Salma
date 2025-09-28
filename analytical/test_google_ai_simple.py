import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_google_ai():
    """Test if Google AI is working"""
    print("Testing Google AI connection...")
    
    try:
        from django.conf import settings
        import google.generativeai as genai
        
        # Get API key
        api_key = getattr(settings, 'GOOGLE_AI_API_KEY', None)
        if not api_key:
            print("✗ GOOGLE_AI_API_KEY not found in settings")
            return False
        
        print(f"✓ API Key found")
        
        # Configure Google AI
        genai.configure(api_key=api_key)
        
        # Create model
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✓ Google AI model created")
        
        # Test generation
        response = model.generate_content("Say hello in one word")
        print(f"✓ Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_ai()
    if success:
        print("\n🎉 Google AI is working!")
    else:
        print("\n❌ Google AI is not working!")