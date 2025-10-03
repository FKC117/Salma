#!/usr/bin/env python3
"""
Test the LLM fix for Google AI response extraction
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import User, AnalysisSession, Dataset
from analytics.services.llm_processor import LLMProcessor

def test_llm_fix():
    """Test the LLM processor with the fix"""
    print("=== TESTING LLM FIX ===")
    
    try:
        # Get a user and dataset
        user = User.objects.first()
        if not user:
            print("❌ No users found")
            return False
            
        dataset = Dataset.objects.first()
        if not dataset:
            print("❌ No datasets found")
            return False
            
        print(f"✅ Using User: {user.username} (ID: {user.id})")
        print(f"✅ Using Dataset: {dataset.name} (ID: {dataset.id})")
        
        # Create a session
        session = AnalysisSession.objects.create(
            user=user,
            primary_dataset=dataset,
            name="LLM Test Session"
        )
        print(f"✅ Created Session: {session.id}")
        
        # Test the LLM processor
        processor = LLMProcessor(model_name='gemini')
        
        # Simple test prompt
        test_prompt = "What analysis would you recommend for this dataset?"
        
        print(f"\n=== TESTING LLM GENERATION ===")
        print(f"Prompt: {test_prompt}")
        print(f"Prompt length: {len(test_prompt)}")
        
        # Generate response
        response = processor.generate_text(
            prompt=test_prompt,
            user=user,
            session=session
        )
        
        print(f"\n=== LLM RESPONSE ===")
        print(f"Text length: {len(response.get('text', ''))}")
        print(f"Text preview: {response.get('text', '')[:200]}...")
        print(f"Input tokens: {response.get('input_tokens', 'N/A')}")
        print(f"Output tokens: {response.get('output_tokens', 'N/A')}")
        print(f"Total cost: {response.get('total_cost', 'N/A')}")
        print(f"Execution time: {response.get('execution_time', 'N/A')}s")
        
        if response.get('text') and len(response.get('text', '')) > 0:
            print(f"✅ LLM fix working correctly!")
            return True
        else:
            print(f"❌ LLM fix failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_fix()
    
    if success:
        print(f"\n🎉 LLM FIX SUCCESSFUL!")
        print(f"The Google AI response extraction is now working!")
    else:
        print(f"\n❌ LLM FIX FAILED!")
        print(f"Additional debugging needed.")
