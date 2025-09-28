"""
Comprehensive test script to verify the chat functionality fix
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
from analytics.models import AnalysisSession, Dataset

def create_test_user():
    """Create a test user"""
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
        print("✓ Created test user")
    else:
        print("✓ Using existing test user")
    
    return user

def create_test_dataset(user):
    """Create a test dataset"""
    dataset, created = Dataset.objects.get_or_create(
        name='Test Dataset',
        user=user,
        defaults={
            'original_filename': 'test.csv',
            'file_size_bytes': 1000,
            'file_hash': 'test_hash',
            'original_format': 'csv',
            'parquet_path': 'test.parquet',
            'row_count': 100,
            'column_count': 5,
            'processing_status': 'completed'
        }
    )
    
    if created:
        print("✓ Created test dataset")
    else:
        print("✓ Using existing test dataset")
    
    return dataset

def create_test_session(user, dataset):
    """Create a test session"""
    session, created = AnalysisSession.objects.get_or_create(
        name='Test Session',
        user=user,
        primary_dataset=dataset,
        defaults={
            'description': 'Test session for chat functionality'
        }
    )
    
    if created:
        print("✓ Created test session")
    else:
        print("✓ Using existing test session")
    
    return session

def test_chat_without_session():
    """Test chat message processing without session"""
    print("\n=== Testing Chat Without Session ===")
    
    user = create_test_user()
    llm_processor = LLMProcessor()
    
    try:
        result = llm_processor.process_message(
            user=user,
            message="Hello, this is a test message without session",
            session_id=None
        )
        
        print("Message processing result:")
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response', 'No response')[:100]}...")
        print(f"Error: {result.get('error', 'No error')}")
        
        if result.get('success'):
            print("✓ Chat message processing without session works correctly!")
            return True
        else:
            print("✗ Chat message processing without session failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during message processing without session: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_with_session():
    """Test chat message processing with session"""
    print("\n=== Testing Chat With Session ===")
    
    user = create_test_user()
    dataset = create_test_dataset(user)
    session = create_test_session(user, dataset)
    
    llm_processor = LLMProcessor()
    
    try:
        result = llm_processor.process_message(
            user=user,
            message="Hello, this is a test message with session",
            session_id=str(session.id)
        )
        
        print("Message processing result:")
        print(f"Success: {result.get('success')}")
        print(f"Response: {result.get('response', 'No response')[:100]}...")
        print(f"Error: {result.get('error', 'No error')}")
        
        if result.get('success'):
            print("✓ Chat message processing with session works correctly!")
            return True
        else:
            print("✗ Chat message processing with session failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during message processing with session: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Testing chat functionality fix...")
    
    # Test both scenarios
    success1 = test_chat_without_session()
    success2 = test_chat_with_session()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Chat functionality should be working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    main()