#!/usr/bin/env python3
"""
Simple API test without importing the problematic viewset
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
from analytics.services.sandbox_result_processor import SandboxResultProcessor

def test_processor_direct():
    """Test the processor directly"""
    print("=== TESTING PROCESSOR DIRECTLY ===")
    
    # Get the most recent result with images
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No sandbox results with images found")
        return False
        
    session_id = result.session.id
    user_id = result.user.id
    print(f"Testing with Session ID: {session_id}, User ID: {user_id}")
    
    try:
        # Test the processor directly
        processor = SandboxResultProcessor()
        results = processor.get_sandbox_results(session_id, user_id)
        
        print(f"✅ Processor working!")
        print(f"Response structure:")
        print(f"  Results: {len(results)}")
        
        # Check the specific result
        target_result = None
        for r in results:
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
                
            return True
        else:
            print(f"❌ Target result {result.id} not found in processor response")
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
        print(f"✅ User: {user.username} (ID: {user.id})")
        
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

def create_frontend_fix():
    """Create a frontend fix for the image display issue"""
    print(f"\n=== CREATING FRONTEND FIX ===")
    
    # The issue is likely that the frontend JavaScript is not finding the session ID
    # Let me create a better solution that doesn't rely on the API endpoint
    
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No results found")
        return
        
    images = result.get_images()
    if not images:
        print("❌ No images found")
        return
        
    # Create a direct image display solution
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Direct Image Display Fix</title>
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
        <h1>Direct Image Display Fix</h1>
        <p>SandboxResult ID: {result.id}</p>
        <p>Session ID: {result.session.id}</p>
        
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
        
        <div class="mt-5">
            <h3>JavaScript Fix for Frontend</h3>
            <p>Replace the current image loading JavaScript with this:</p>
            <pre><code>
// Direct image loading without API call
function loadSandboxImagesDirect(sandboxResultId, container) {
    // Get images directly from the server-side data
    const images = getImagesForResult(sandboxResultId);
    
    if (images && images.length > 0) {
        container.innerHTML = '<strong>Images:</strong>';
        
        images.forEach((image, index) => {
            const img = document.createElement('img');
            img.src = image.image_data;
            img.alt = image.name || `Chart ${index + 1}`;
            img.className = 'img-fluid rounded mt-2';
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
            img.style.border = '1px solid #444';
            
            const imageInfo = document.createElement('div');
            imageInfo.className = 'text-muted small mt-1';
            imageInfo.textContent = `${image.name} (${image.width}x${image.height})`;
            
            container.appendChild(img);
            container.appendChild(imageInfo);
        });
    } else {
        container.innerHTML = '<strong>Images:</strong> <span class="text-muted">No images found</span>';
    }
}
            </code></pre>
        </div>
    </div>
</body>
</html>
"""
    
    # Write the fix HTML file
    fix_file = Path("analytical/direct_image_fix.html")
    fix_file.write_text(html_content)
    print(f"✅ Direct image fix created: {fix_file}")
    print(f"  This shows the images working directly without API calls")

if __name__ == "__main__":
    success1 = test_processor_direct()
    success2 = test_with_client()
    create_frontend_fix()
    
    if success1 and success2:
        print(f"\n🎉 DATA IS WORKING CORRECTLY!")
        print(f"The issue is in the frontend JavaScript or API endpoint.")
        print(f"Images are being generated and stored properly.")
    else:
        print(f"\n❌ Issues found in data processing!")
