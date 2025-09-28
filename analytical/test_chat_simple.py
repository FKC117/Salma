import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.contrib.auth import get_user_model
from analytics.services.llm_processor import LLMProcessor

def test_chat():
    """Simple test to verify chat functionality works"""
    print("Testing chat functionality...")
    
    try:
        # Get or create a test user
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username='test_chat_user',
                email='test_chat@example.com',
                password='testpassword'
            )
            print("✓ Created test user")
        else:
            print("✓ Using existing user")
        
        # Create LLM processor
        llm_processor = LLMProcessor()
        print("✓ LLMProcessor created successfully")
        
        # Test process_message
        print("\n--- Testing process_message ---")
        result = llm_processor.process_message(
            user=user,
            message="What is the capital of France?",
            session_id=None
        )
        
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Response: {result.get('response')}")
            print("🎉 Chat functionality is working!")
            return True
        else:
            print(f"Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chat()
    if success:
        print("\nYou can now test the chat functionality in the web interface!")
    else:
        print("\nThere are still issues with the chat functionality.")