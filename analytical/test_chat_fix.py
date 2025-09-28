"""
Test script to verify the chat functionality fix
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.contrib.auth import get_user_model
from analytics.services.llm_processor import LLMProcessor

def test_chat_message_processing():
    """Test chat message processing without session"""
    print("Testing chat message processing...")
    
    # Get or create a test user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'is_active': True
        }
    )
    
    if created:
        user.set_password('testpassword')
        user.save()
        print("Created test user")
    
    # Create LLM processor
    llm_processor = LLMProcessor()
    
    # Test message processing without session
    try:
        result = llm_processor.process_message(
            user=user,
            message="Hello, this is a test message",
            session_id=None
        )
        
        print("Message processing result:")
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response', 'No response')}")
        print(f"Error: {result.get('error', 'No error')}")
        
        if result.get('success'):
            print("✓ Chat message processing works correctly!")
            return True
        else:
            print("✗ Chat message processing failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during message processing: {str(e)}")
        return False

if __name__ == "__main__":
    test_chat_message_processing()