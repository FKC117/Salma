#!/usr/bin/env python3
"""
Test the API endpoint directly without authentication
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from django.test import RequestFactory, Client
from analytics.models import User, AnalysisSession, SandboxResult
from analytics.enhanced_chat_viewset import EnhancedChatViewSet

def test_api_direct():
    """Test the API endpoint directly"""
    print("=== TESTING API DIRECTLY ===")
    
    # Get the most recent result with images
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No sandbox results with images found")
        return False
        
    session_id = result.session.id
    user_id = result.user.id
    print(f"Testing with Session ID: {session_id}, User ID: {user_id}")
    
    try:
        # Create a test request
        factory = RequestFactory()
        request = factory.get(f'/enhanced-chat/sandbox-results/?session_id={session_id}')
        
        # Get the user
        user = User.objects.get(id=user_id)
        request.user = user
        
        print(f"✅ User: {user.username} (ID: {user.id})")
        
        # Test the viewset
        viewset = EnhancedChatViewSet()
        response = viewset.sandbox_results(request)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ API working!")
            print(f"Response structure:")
            print(f"  Success: {data.get('success')}")
            print(f"  Count: {data.get('count')}")
            print(f"  Results: {len(data.get('results', []))}")
            
            # Check the specific result
            target_result = None
            for r in data.get('results', []):
                if r['id'] == result.id:
                    target_result = r
                    break
            
            if target_result:
                print(f"\n✅ Found target result {result.id}:")
                print(f"  Has Images: {target_result['has_images']}")
                print(f"  Image Count: {target_result['image_count']}")
                print(f"  Images: {len(target_result['images'])}")
                
                if target_result['images']:
                    print(f"  ✅ Images available for frontend")
                    for img in target_result['images']:
                        print(f"    Image {img['id']}: {img['name']}")
                        print(f"      Data Length: {len(img['image_data']) if img['image_data'] else 0}")
                        print(f"      Format: {img['image_format']}")
                        print(f"      Dimensions: {img['width']}x{img['height']}")
                        
                        # Test if the image data would work in HTML
                        if img['image_data'] and img['image_data'].startswith('data:image/'):
                            print(f"      ✅ Valid base64 data URL")
                        else:
                            print(f"      ❌ Invalid base64 format")
                else:
                    print(f"  ❌ No images in API response")
            else:
                print(f"❌ Target result {result.id} not found in API response")
                
            return True
        else:
            print(f"❌ API failed with status {response.status_code}")
            print(f"Response: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_client():
    """Test using Django test client"""
    print(f"\n=== TESTING WITH DJANGO CLIENT ===")
    
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No sandbox results with images found")
        return False
        
    session_id = result.session.id
    user_id = result.user.id
    
    try:
        # Create a test client
        client = Client()
        
        # Get the user
        user = User.objects.get(id=user_id)
        
        # Login the user
        client.force_login(user)
        
        # Make the request
        response = client.get(f'/enhanced-chat/sandbox-results/?session_id={session_id}')
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Client test working!")
            print(f"Response structure:")
            print(f"  Success: {data.get('success')}")
            print(f"  Count: {data.get('count')}")
            print(f"  Results: {len(data.get('results', []))}")
            
            # Check the specific result
            target_result = None
            for r in data.get('results', []):
                if r['id'] == result.id:
                    target_result = r
                    break
            
            if target_result and target_result['images']:
                print(f"✅ Found {len(target_result['images'])} images for result {result.id}")
                return True
            else:
                print(f"❌ No images found for result {result.id}")
                return False
        else:
            print(f"❌ Client test failed with status {response.status_code}")
            print(f"Response: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_api_direct()
    success2 = test_with_client()
    
    if success1 and success2:
        print(f"\n🎉 API is working correctly!")
        print(f"The issue is likely in the frontend JavaScript or authentication.")
    else:
        print(f"\n❌ API issues found!")

