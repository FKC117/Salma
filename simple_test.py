#!/usr/bin/env python
"""
Simple test to verify the system is working
"""
import os
import sys
import django

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class SimpleTest(TestCase):
    def test_basic_functionality(self):
        """Test basic Django functionality"""
        print("Testing basic Django functionality...")
        
        # Test user creation
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        print(f"Created user: {user.username}")
        
        # Test client
        client = Client()
        response = client.get('/')
        
        print(f"Home page status: {response.status_code}")
        
        # Basic assertions
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        
        print("Basic functionality test passed!")

if __name__ == '__main__':
    import unittest
    unittest.main()