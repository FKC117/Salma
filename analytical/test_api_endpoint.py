#!/usr/bin/env python3
"""
Test the actual API endpoint
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

from analytics.models import User, AnalysisSession, SandboxResult

def test_api_endpoint():
    """Test the actual API endpoint"""
    print("=== TESTING API ENDPOINT ===")
    
    # Get a session with sandbox results
    result = SandboxResult.objects.filter(has_images=True).first()
    if not result:
        print("❌ No sandbox results with images found")
        return
        
    session_id = result.session.id
    print(f"Testing with Session ID: {session_id}")
    
    # Test the API endpoint
    url = f"http://localhost:8000/enhanced-chat/sandbox-results/?session_id={session_id}"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Data:")
            print(json.dumps(data, indent=2))
            
            if data.get('success') and data.get('results'):
                print(f"✅ API working correctly")
                print(f"✅ Found {len(data['results'])} results")
                
                for result_data in data['results']:
                    if result_data.get('images'):
                        print(f"✅ Result {result_data['id']} has {len(result_data['images'])} images")
                        for img in result_data['images']:
                            if img.get('image_data'):
                                print(f"✅ Image {img['id']} has valid data ({len(img['image_data'])} chars)")
                            else:
                                print(f"❌ Image {img['id']} missing data")
                    else:
                        print(f"❌ Result {result_data['id']} has no images")
            else:
                print(f"❌ API response format incorrect")
        else:
            print(f"❌ API failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_frontend_html():
    """Test if the image data would work in HTML"""
    print(f"\n=== TESTING HTML COMPATIBILITY ===")
    
    result = SandboxResult.objects.filter(has_images=True).first()
    if not result:
        print("❌ No results with images found")
        return
        
    images = result.get_images()
    print(f"Testing {len(images)} images for HTML compatibility")
    
    for i, image in enumerate(images):
        print(f"\nImage {i+1}: {image.name}")
        print(f"  Format: {image.image_format}")
        print(f"  Dimensions: {image.width}x{image.height}")
        
        if image.image_data:
            # Test if it's valid base64
            if image.image_data.startswith('data:image/'):
                print(f"  ✅ Valid base64 data URL")
                
                # Create a test HTML snippet
                html_snippet = f'<img src="{image.image_data[:100]}..." alt="{image.name}" class="img-fluid">'
                print(f"  HTML: {html_snippet}")
                
                # Check data length
                data_length = len(image.image_data)
                if data_length > 1000000:  # 1MB
                    print(f"  ⚠️  Large image data: {data_length} bytes")
                else:
                    print(f"  ✅ Reasonable size: {data_length} bytes")
            else:
                print(f"  ❌ Invalid base64 format")
        else:
            print(f"  ❌ No image data")

if __name__ == "__main__":
    test_api_endpoint()
    test_frontend_html()
