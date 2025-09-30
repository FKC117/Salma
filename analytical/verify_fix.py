import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

print("=== Verifying Gemini API Fix ===")

try:
    from analytics.services.llm_processor import LLMProcessor
    
    # Test default initialization
    llm_processor = LLMProcessor()
    print(f"Default model: {llm_processor.model_name}")
    
    # Test explicit Gemini initialization
    llm_gemini = LLMProcessor(model_name='gemini')
    print(f"Explicit Gemini model: {llm_gemini.model_name}")
    
    if llm_processor.model_name == 'gemini':
        print("✅ SUCCESS: LLMProcessor correctly defaults to Gemini when USE_OLLAMA=False")
    else:
        print("❌ ISSUE: LLMProcessor should default to Gemini but got:", llm_processor.model_name)
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()