#!/usr/bin/env python3
"""
Test Google AI API Configuration
This script tests the Google AI API integration with Gemini 1.5 Flash
"""

import os
import sys
import django

# Add the Django project to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.services.google_ai_service import GoogleAIService

def test_google_ai():
    """Test Google AI API configuration"""
    print("🤖 Testing Google AI API Configuration")
    print("=" * 50)
    
    try:
        # Initialize service
        ai_service = GoogleAIService()
        
        print(f"✅ API Key: {ai_service.api_key[:20]}...")
        print(f"✅ Model: {ai_service.model_name}")
        print(f"✅ Generation Config: {ai_service.generation_config}")
        print(f"✅ Safety Settings: {len(ai_service.safety_settings)} configured")
        
        # Test API key validation
        print("\n🔍 Testing API Key Validation...")
        if ai_service.validate_api_key():
            print("✅ API Key is valid")
        else:
            print("❌ API Key validation failed")
            return False
        
        # Test simple generation
        print("\n🧪 Testing Simple Generation...")
        test_prompt = "Hello! Please respond with a short greeting."
        
        result = ai_service.generate_response(test_prompt, user_id=1)
        
        if result['success']:
            print("✅ Generation successful!")
            print(f"📝 Response: {result['response'][:100]}...")
            print(f"🔢 Input Tokens: {result['input_tokens']}")
            print(f"🔢 Output Tokens: {result['output_tokens']}")
            print(f"💰 Cost: ${result['cost']:.6f}")
            print(f"⏱️ Generation Time: {result['generation_time']:.2f}s")
        else:
            print(f"❌ Generation failed: {result['error']}")
            return False
        
        # Test token usage tracking
        print("\n📊 Testing Token Usage Tracking...")
        stats = ai_service.get_user_usage_stats(user_id=1)
        print(f"✅ User Token Usage:")
        print(f"   Input Tokens: {stats['input_tokens']}")
        print(f"   Output Tokens: {stats['output_tokens']}")
        print(f"   Total Tokens: {stats['total_tokens']}")
        print(f"   Total Cost: ${stats['total_cost']:.6f}")
        print(f"   Remaining Tokens: {stats['remaining_tokens']}")
        print(f"   Usage Percentage: {stats['usage_percentage']:.2f}%")
        
        print("\n🎉 All tests passed! Google AI is configured correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_google_ai()
    sys.exit(0 if success else 1)
