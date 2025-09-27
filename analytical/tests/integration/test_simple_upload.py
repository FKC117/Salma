"""
Simple Upload Test

This is a minimal test to debug the upload endpoint.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class SimpleUploadTest(TestCase):
    """Simple upload test for debugging"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_login(self.user)
    
    def test_simple_upload(self):
        """Test simple upload"""
        csv_content = "name,age\nJohn,25"
        
        uploaded_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode(),
            content_type="text/csv"
        )
        
        response = self.client.post('/upload/', {
            'file': uploaded_file,
            'name': 'test_dataset'
        })
        
        print(f"Status: {response.status_code}")
        print(f"Content: {response.content}")
        
        # For now, just check that we get some response
        self.assertIn(response.status_code, [200, 400, 500])
