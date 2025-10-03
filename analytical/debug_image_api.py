#!/usr/bin/env python3
"""
Debug script to test the sandbox-results API endpoint and image data
"""

import os
import sys
import django
import requests
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import User
from analytics.models import AnalysisSession, SandboxExecution, SandboxResult, GeneratedImage
from analytics.services.sandbox_result_processor import SandboxResultProcessor

def debug_image_api():
    """Debug the sandbox-results API endpoint"""
    print("=== DEBUGGING SANDBOX IMAGE API ===")
    
    # Get the most recent user and session
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found")
            return
            
        session = AnalysisSession.objects.filter(user=user).first()
        if not session:
            print("❌ No sessions found")
            return
            
        print(f"✅ Using User: {user.id} ({user.username})")
        print(f"✅ Using Session: {session.id} ({session.name})")
        
        # Get sandbox results
        processor = SandboxResultProcessor()
        results = processor.get_sandbox_results(session.id, user.id)
        
        print(f"\n=== SANDBOX RESULTS ({len(results)} found) ===")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  ID: {result['id']}")
            print(f"  Execution ID: {result['execution_id']}")
            print(f"  Has Images: {result['has_images']}")
            print(f"  Image Count: {result['image_count']}")
            print(f"  Text Output Length: {len(result['text_output']) if result['text_output'] else 0}")
            print(f"  Images: {len(result['images'])}")
            
            if result['images']:
                for j, image in enumerate(result['images']):
                    print(f"    Image {j+1}:")
                    print(f"      ID: {image['id']}")
                    print(f"      Name: {image['name']}")
                    print(f"      Format: {image['image_format']}")
                    print(f"      Dimensions: {image['width']}x{image['height']}")
                    print(f"      Image Data Length: {len(image['image_data']) if image['image_data'] else 0}")
                    print(f"      Image Data Preview: {image['image_data'][:100] if image['image_data'] else 'None'}...")
                    
                    # Check if it's a valid base64 image
                    if image['image_data']:
                        if image['image_data'].startswith('data:image/'):
                            print(f"      ✅ Valid base64 image data")
                        else:
                            print(f"      ❌ Invalid base64 image data format")
                    else:
                        print(f"      ❌ No image data")
            else:
                print(f"    ❌ No images found")
        
        # Test the API endpoint directly
        print(f"\n=== TESTING API ENDPOINT ===")
        print(f"Testing: /enhanced-chat/sandbox-results/?session_id={session.id}")
        
        # Simulate the API call
        from django.test import RequestFactory
        from analytics.enhanced_chat_viewset import EnhancedChatViewSet
        
        factory = RequestFactory()
        request = factory.get(f'/enhanced-chat/sandbox-results/?session_id={session.id}')
        request.user = user
        
        viewset = EnhancedChatViewSet()
        response = viewset.sandbox_results(request)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Data: {json.dumps(response.data, indent=2)}")
        
        # Check if the response matches what the frontend expects
        if response.status_code == 200:
            data = response.data
            if data.get('success') and data.get('results'):
                print(f"✅ API endpoint working correctly")
                print(f"✅ Found {len(data['results'])} results")
                
                # Check each result for images
                for result in data['results']:
                    if result.get('images'):
                        print(f"✅ Result {result['id']} has {len(result['images'])} images")
                        for image in result['images']:
                            if image.get('image_data'):
                                print(f"✅ Image {image['id']} has valid data")
                            else:
                                print(f"❌ Image {image['id']} missing data")
                    else:
                        print(f"❌ Result {result['id']} has no images")
            else:
                print(f"❌ API response format incorrect")
        else:
            print(f"❌ API endpoint failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def check_database_images():
    """Check the database for image records"""
    print("\n=== CHECKING DATABASE IMAGES ===")
    
    try:
        # Get all GeneratedImage records
        images = GeneratedImage.objects.filter(source_type='sandbox').order_by('-created_at')[:10]
        
        print(f"Found {images.count()} sandbox images in database")
        
        for image in images:
            print(f"\nImage ID: {image.id}")
            print(f"  Name: {image.name}")
            print(f"  Source Type: {image.source_type}")
            print(f"  Format: {image.image_format}")
            print(f"  Dimensions: {image.width}x{image.height}")
            print(f"  File Path: {image.file_path}")
            print(f"  Has Base64 Data: {bool(image.image_data)}")
            print(f"  Base64 Length: {len(image.image_data) if image.image_data else 0}")
            
            if image.image_data:
                print(f"  Base64 Preview: {image.image_data[:100]}...")
                if image.image_data.startswith('data:image/'):
                    print(f"  ✅ Valid base64 format")
                else:
                    print(f"  ❌ Invalid base64 format")
            
            # Check if file exists
            if image.file_path:
                file_path = Path(image.file_path)
                if file_path.exists():
                    print(f"  ✅ File exists: {file_path}")
                    print(f"  File size: {file_path.stat().st_size} bytes")
                else:
                    print(f"  ❌ File missing: {file_path}")
                    
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_image_api()
    check_database_images()
