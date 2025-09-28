"""
Test that simulates exactly what the ChatViewSet does
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.contrib.auth import get_user_model
from analytics.services.llm_processor import LLMProcessor

def simulate_chat_viewset():
    """Simulate exactly what the ChatViewSet does"""
    print("=== Simulating ChatViewSet ===")
    
    # This is what the ChatViewSet does:
    # 1. Get user (or create default)
    # 2. Process message with LLM processor
    # 3. Return response based on result
    
    try:
        # Get user (like ChatViewSet does)
        User = get_user_model()
        user = User.objects.first()
        if not user:
            user = User.objects.create(
                username='default_user',
                email='user@example.com'
            )
        print(f"✓ User: {user.username}")
        
        # Process message (like ChatViewSet does)
        llm_processor = LLMProcessor()
        
        # This is the exact call the ChatViewSet makes:
        result = llm_processor.process_message(
            user=user,
            message="Test message from simulation",
            session_id=None,
            context={}
        )
        
        print("Result from process_message:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        # This is what the ChatViewSet does with the result:
        if result['success']:
            response_data = {
                'success': True,
                'response': result['response'],
                'message_id': result['message_id'],
                'token_usage': result.get('token_usage', {}),
                'message': 'Message processed successfully'
            }
            print("✓ Would return 200 OK with data:")
            print(f"  Response: {response_data['response'][:100]}...")
        else:
            response_data = {
                'success': False,
                'error': result.get('error', 'Message processing failed')
            }
            print("✗ Would return 400 Bad Request with error:")
            print(f"  Error: {response_data['error']}")
            
        return result['success']
        
    except Exception as e:
        print(f"✗ Exception in simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simulate_chat_viewset()
    if success:
        print("\n🎉 Simulation successful!")
    else:
        print("\n❌ Simulation failed!")