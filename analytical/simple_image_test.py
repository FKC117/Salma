#!/usr/bin/env python3
"""
Simple test to check image data and API response
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

from analytics.models import User, AnalysisSession, SandboxExecution, SandboxResult, GeneratedImage
from analytics.services.sandbox_result_processor import SandboxResultProcessor

def test_image_data():
    """Test image data directly"""
    print("=== TESTING IMAGE DATA ===")
    
    # Get the most recent sandbox result with images
    result = SandboxResult.objects.filter(has_images=True).first()
    if not result:
        print("❌ No sandbox results with images found")
        return
        
    print(f"✅ Found SandboxResult: {result.id}")
    print(f"  Session ID: {result.session.id}")
    print(f"  User ID: {result.user.id}")
    print(f"  Has Images: {result.has_images}")
    print(f"  Image Count: {result.image_count}")
    
    # Get images for this result
    images = result.get_images()
    print(f"  Images found: {len(images)}")
    
    for i, image in enumerate(images):
        print(f"\n  Image {i+1}:")
        print(f"    ID: {image.id}")
        print(f"    Name: {image.name}")
        print(f"    Format: {image.image_format}")
        print(f"    Dimensions: {image.width}x{image.height}")
        print(f"    Has Base64: {bool(image.image_data)}")
        print(f"    Base64 Length: {len(image.image_data) if image.image_data else 0}")
        
        if image.image_data:
            print(f"    Base64 Preview: {image.image_data[:50]}...")
            if image.image_data.startswith('data:image/'):
                print(f"    ✅ Valid base64 format")
            else:
                print(f"    ❌ Invalid base64 format")
    
    # Test the processor
    print(f"\n=== TESTING PROCESSOR ===")
    processor = SandboxResultProcessor()
    results = processor.get_sandbox_results(result.session.id, result.user.id)
    
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
                if img['image_data']:
                    print(f"      Preview: {img['image_data'][:50]}...")

def test_frontend_simulation():
    """Simulate what the frontend receives"""
    print(f"\n=== SIMULATING FRONTEND REQUEST ===")
    
    # Get a result with images
    result = SandboxResult.objects.filter(has_images=True).first()
    if not result:
        print("❌ No results with images found")
        return
        
    # Simulate the API response
    processor = SandboxResultProcessor()
    results = processor.get_sandbox_results(result.session.id, result.user.id)
    
    # Create the response structure that frontend expects
    api_response = {
        'success': True,
        'results': results,
        'count': len(results)
    }
    
    print(f"API Response Structure:")
    print(f"  Success: {api_response['success']}")
    print(f"  Count: {api_response['count']}")
    print(f"  Results: {len(api_response['results'])}")
    
    # Check what frontend would receive
    for result_data in api_response['results']:
        print(f"\nResult {result_data['id']} for frontend:")
        print(f"  Has Images: {result_data['has_images']}")
        print(f"  Image Count: {result_data['image_count']}")
        
        if result_data['images']:
            print(f"  ✅ {len(result_data['images'])} images available")
            for img in result_data['images']:
                print(f"    Image {img['id']}: {img['name']}")
                print(f"      Data available: {bool(img['image_data'])}")
                print(f"      Data length: {len(img['image_data']) if img['image_data'] else 0}")
                
                # Test if this would work in HTML
                if img['image_data'] and img['image_data'].startswith('data:image/'):
                    print(f"      ✅ Would work in <img src='{img['image_data'][:50]}...'>")
                else:
                    print(f"      ❌ Would NOT work in <img> tag")
        else:
            print(f"  ❌ No images in result")

if __name__ == "__main__":
    test_image_data()
    test_frontend_simulation()
