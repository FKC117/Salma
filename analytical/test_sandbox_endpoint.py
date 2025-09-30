"""
Test script to verify the sandbox execution endpoint works correctly
"""
import os
import sys
import django
from django.contrib.auth import get_user_model
import json
from rest_framework.test import APIClient

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

def test_sandbox_endpoint():
    """Test the sandbox execution endpoint"""
    # Create test client
    client = APIClient()
    
    # Get or create user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Login
    client.login(username='testuser', password='testpass123')
    
    # Test successful code execution
    print("Testing successful code execution...")
    response = client.post('/api/sandbox/execute/', {
        'code': 'print("Hello, World!")',
        'language': 'python'
    }, format='json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test code with error
    print("\nTesting code with error...")
    response = client.post('/api/sandbox/execute/', {
        'code': 'print(undefined_variable)',
        'language': 'python'
    }, format='json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test missing code
    print("\nTesting missing code...")
    response = client.post('/api/sandbox/execute/', {
        'language': 'python'
    }, format='json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == '__main__':
    test_sandbox_endpoint()