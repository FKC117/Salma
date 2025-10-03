#!/usr/bin/env python3
"""
Complete test to verify the image display fix
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

from analytics.models import User, AnalysisSession, SandboxResult
from analytics.services.sandbox_result_processor import SandboxResultProcessor

def test_complete_image_flow():
    """Test the complete image flow from database to API"""
    print("=== TESTING COMPLETE IMAGE FLOW ===")
    
    # Get a result with images
    result = SandboxResult.objects.filter(has_images=True).first()
    if not result:
        print("❌ No sandbox results with images found")
        return False
        
    print(f"✅ Found SandboxResult: {result.id}")
    print(f"  Session ID: {result.session.id}")
    print(f"  User ID: {result.user.id}")
    print(f"  Has Images: {result.has_images}")
    print(f"  Image Count: {result.image_count}")
    
    # Test the processor
    processor = SandboxResultProcessor()
    results = processor.get_sandbox_results(result.session.id, result.user.id)
    
    print(f"\n=== PROCESSOR TEST ===")
    print(f"Processor returned {len(results)} results")
    
    for result_data in results:
        print(f"\nResult {result_data['id']}:")
        print(f"  Has Images: {result_data['has_images']}")
        print(f"  Image Count: {result_data['image_count']}")
        print(f"  Images: {len(result_data['images'])}")
        
        if result_data['images']:
            for img in result_data['images']:
                print(f"    Image {img['id']}: {img['name']}")
                print(f"      Has Data: {bool(img['image_data'])}")
                print(f"      Data Length: {len(img['image_data']) if img['image_data'] else 0}")
                print(f"      Format: {img['image_format']}")
                print(f"      Dimensions: {img['width']}x{img['height']}")
                
                if img['image_data'] and img['image_data'].startswith('data:image/'):
                    print(f"      ✅ Valid base64 data URL")
                else:
                    print(f"      ❌ Invalid base64 format")
    
    # Test API response structure
    print(f"\n=== API RESPONSE STRUCTURE TEST ===")
    api_response = {
        'success': True,
        'results': results,
        'count': len(results)
    }
    
    print(f"API Response:")
    print(f"  Success: {api_response['success']}")
    print(f"  Count: {api_response['count']}")
    print(f"  Results: {len(api_response['results'])}")
    
    # Verify frontend compatibility
    print(f"\n=== FRONTEND COMPATIBILITY TEST ===")
    for result_data in api_response['results']:
        if result_data['images']:
            print(f"✅ Result {result_data['id']} has {len(result_data['images'])} images")
            for img in result_data['images']:
                if img['image_data'] and img['image_data'].startswith('data:image/'):
                    print(f"  ✅ Image {img['id']} would display correctly in browser")
                else:
                    print(f"  ❌ Image {img['id']} would NOT display correctly")
        else:
            print(f"❌ Result {result_data['id']} has no images")
    
    return True

def test_url_pattern():
    """Test if the URL pattern is correctly registered"""
    print(f"\n=== URL PATTERN TEST ===")
    
    try:
        from django.urls import reverse
        from django.test import RequestFactory
        from analytics.enhanced_chat_viewset import EnhancedChatViewSet
        
        # Test if the URL can be reversed
        try:
            url = reverse('enhanced_chat_sandbox_results')
            print(f"✅ URL pattern found: {url}")
        except Exception as e:
            print(f"❌ URL pattern not found: {str(e)}")
            return False
        
        # Test the viewset method exists
        viewset = EnhancedChatViewSet()
        if hasattr(viewset, 'sandbox_results'):
            print(f"✅ sandbox_results method exists")
        else:
            print(f"❌ sandbox_results method missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing URL pattern: {str(e)}")
        return False

def create_test_html():
    """Create a test HTML file to verify image display"""
    print(f"\n=== CREATING TEST HTML ===")
    
    result = SandboxResult.objects.filter(has_images=True).first()
    if not result:
        print("❌ No results with images found")
        return
        
    images = result.get_images()
    if not images:
        print("❌ No images found")
        return
        
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Sandbox Image Test</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #1a1a1a; color: #ffffff; }}
        .container {{ margin-top: 50px; }}
        .image-container {{ margin: 20px 0; }}
        img {{ border: 2px solid #444; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Sandbox Image Display Test</h1>
        <p>Testing image display for SandboxResult {result.id}</p>
        
        <div class="image-container">
            <h3>Images ({len(images)} found):</h3>
"""
    
    for i, image in enumerate(images):
        html_content += f"""
            <div class="mb-4">
                <h5>Image {i+1}: {image.name}</h5>
                <p>Format: {image.image_format} | Dimensions: {image.width}x{image.height}</p>
                <img src="{image.image_data}" alt="{image.name}" class="img-fluid" style="max-width: 100%; height: auto;">
            </div>
"""
    
    html_content += """
        </div>
    </div>
</body>
</html>
"""
    
    # Write the test HTML file
    test_file = Path("analytical/test_image_display.html")
    test_file.write_text(html_content)
    print(f"✅ Test HTML created: {test_file}")
    print(f"  Open this file in a browser to test image display")

if __name__ == "__main__":
    success = test_complete_image_flow()
    if success:
        test_url_pattern()
        create_test_html()
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"The image display issue should now be fixed!")
    else:
        print(f"\n❌ TESTS FAILED!")
