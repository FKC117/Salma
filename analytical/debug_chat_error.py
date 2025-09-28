"""
Debug script to get detailed information about the chat error
"""
import os
import sys
import django
import json
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

import logging
from django.contrib.auth import get_user_model
from analytics.services.llm_processor import LLMProcessor
from analytics.models import AnalysisSession, Dataset

# Set up logging to see detailed error information
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_chat_message():
    """Debug chat message processing to see detailed error information"""
    print("=== Debugging Chat Message Processing ===")
    
    # Get or create a test user
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='debug_user',
                email='debug@example.com',
                password='debugpassword'
            )
            print("✓ Created debug user")
        else:
            print("✓ Using existing user")
    except Exception as e:
        print(f"✗ Error getting/creating user: {str(e)}")
        return False
    
    # Create LLM processor
    try:
        llm_processor = LLMProcessor()
        print("✓ LLM Processor created successfully")
    except Exception as e:
        print(f"✗ Error creating LLM Processor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test message processing
    try:
        print("\n--- Testing process_message ---")
        result = llm_processor.process_message(
            user=user,
            message="Debug test message",
            session_id=None
        )
        
        print("Result:")
        print(json.dumps(result, indent=2, default=str))
        
        if result.get('success'):
            print("✓ Message processing successful")
            return True
        else:
            print("✗ Message processing failed")
            return False
            
    except Exception as e:
        print(f"✗ Exception during message processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_viewset_directly():
    """Test the ChatViewSet directly to see what error it returns"""
    print("\n=== Testing ChatViewSet Directly ===")
    
    from analytics.views import ChatViewSet
    from rest_framework.test import APIRequestFactory
    from rest_framework.request import Request
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='debug_user2',
                email='debug2@example.com',
                password='debugpassword'
            )
    except Exception as e:
        print(f"✗ Error getting/creating user: {str(e)}")
        return False
    
    # Create a request factory
    factory = APIRequestFactory()
    
    # Create a POST request
    request = factory.post('/api/chat/messages/', {
        'message': 'Test message from debug script'
    })
    
    # Set the user on the request
    request.user = user
    
    # Create the viewset
    viewset = ChatViewSet()
    viewset.request = Request(request)
    
    try:
        print("\n--- Calling ChatViewSet messages method ---")
        response = viewset.messages(request)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        return True
    except Exception as e:
        print(f"✗ Exception in ChatViewSet: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    print("Starting detailed chat error debugging...")
    
    # Test direct processing
    success1 = debug_chat_message()
    
    # Test viewset
    success2 = test_chat_viewset_directly()
    
    if success1 and success2:
        print("\n🎉 All debug tests passed!")
    else:
        print("\n❌ Some debug tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()