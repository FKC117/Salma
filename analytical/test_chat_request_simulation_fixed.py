"""
Test that simulates the exact HTTP request the frontend makes
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

# NOW we can import Django modules
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.http import JsonResponse
import json

from analytics.views import ChatViewSet

def simulate_frontend_request():
    """Simulate the exact request the frontend makes"""
    print("=== Simulating Frontend Request ===")
    
    # Create a request factory
    factory = RequestFactory()
    
    # Create the POST request exactly like the frontend does
    request = factory.post('/api/chat/messages/', {
        'message': 'Hello, this is a test message from the frontend simulation'
    })
    
    # Add a user to the request (like the real request would have)
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(
            username='test_frontend_user',
            email='frontend_test@example.com',
            password='testpassword'
        )
    request.user = user
    
    # Create the ChatViewSet instance
    viewset = ChatViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    try:
        print("Sending request to ChatViewSet.messages...")
        response = viewset.messages(request)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response data: {response.data}")
        
        if response.status_code == 200:
            print("✓ Request successful!")
            return True
        elif response.status_code == 400:
            print("✗ Request failed with 400 Bad Request")
            print(f"Error: {response.data}")
            return False
        else:
            print(f"✗ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during request: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_empty_message():
    """Test with an empty message to see if that causes the 400 error"""
    print("\n=== Testing with Empty Message ===")
    
    factory = RequestFactory()
    request = factory.post('/api/chat/messages/', {
        'message': ''  # Empty message
    })
    
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(
            username='test_empty_user',
            email='empty_test@example.com',
            password='testpassword'
        )
    request.user = user
    
    viewset = ChatViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    try:
        response = viewset.messages(request)
        print(f"Response status code: {response.status_code}")
        if response.status_code == 400:
            print(f"Error (expected for empty message): {response.data}")
        return response.status_code != 400  # We expect this to fail
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def test_with_missing_message():
    """Test with missing message field"""
    print("\n=== Testing with Missing Message Field ===")
    
    factory = RequestFactory()
    request = factory.post('/api/chat/messages/', {
        # No 'message' field
        'other_field': 'some_value'
    })
    
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(
            username='test_missing_user',
            email='missing_test@example.com',
            password='testpassword'
        )
    request.user = user
    
    viewset = ChatViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    try:
        response = viewset.messages(request)
        print(f"Response status code: {response.status_code}")
        if response.status_code == 400:
            print(f"Error (expected for missing message): {response.data}")
        return response.status_code != 400  # We expect this to fail
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Testing chat request simulation...")
    
    # Test normal request
    success1 = simulate_frontend_request()
    
    # Test edge cases
    success2 = test_with_empty_message()  # This should fail (expected)
    success3 = test_with_missing_message()  # This should fail (expected)
    
    if success1:
        print("\n🎉 Normal request test passed!")
    else:
        print("\n❌ Normal request test failed!")
    
    print("\nNote: Empty message and missing message tests are expected to fail (400 errors)")

if __name__ == "__main__":
    main()