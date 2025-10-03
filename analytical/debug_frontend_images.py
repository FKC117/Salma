#!/usr/bin/env python3
"""
Debug the frontend image loading issue
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

from analytics.models import User, AnalysisSession, SandboxResult, GeneratedImage
from analytics.services.sandbox_result_processor import SandboxResultProcessor

def debug_latest_execution():
    """Debug the latest sandbox execution"""
    print("=== DEBUGGING LATEST EXECUTION ===")
    
    # Get the most recent sandbox result with images
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No sandbox results with images found")
        return
        
    print(f"✅ Latest SandboxResult: {result.id}")
    print(f"  Session ID: {result.session.id}")
    print(f"  User ID: {result.user.id}")
    print(f"  Created: {result.created_at}")
    print(f"  Has Images: {result.has_images}")
    print(f"  Image Count: {result.image_count}")
    
    # Get images
    images = result.get_images()
    print(f"  Images found: {len(images)}")
    
    for i, image in enumerate(images):
        print(f"\n  Image {i+1}:")
        print(f"    ID: {image.id}")
        print(f"    Name: {image.name}")
        print(f"    Description: {image.description}")
        print(f"    Format: {image.image_format}")
        print(f"    Dimensions: {image.width}x{image.height}")
        print(f"    File Path: {image.file_path}")
        print(f"    Has Base64: {bool(image.image_data)}")
        print(f"    Base64 Length: {len(image.image_data) if image.image_data else 0}")
        
        # Check if the image name is unique and descriptive
        if image.name:
            if "Chart" in image.name:
                print(f"    ✅ Name contains 'Chart'")
            else:
                print(f"    ⚠️  Name doesn't contain 'Chart'")
        else:
            print(f"    ❌ No name")
    
    return result

def test_api_call_simulation():
    """Simulate the exact API call the frontend makes"""
    print(f"\n=== SIMULATING FRONTEND API CALL ===")
    
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No results found")
        return
        
    session_id = result.session.id
    print(f"Simulating API call for Session ID: {session_id}")
    
    # Test the processor
    processor = SandboxResultProcessor()
    results = processor.get_sandbox_results(session_id, result.user.id)
    
    print(f"API Response:")
    print(f"  Success: True")
    print(f"  Count: {len(results)}")
    print(f"  Results: {len(results)}")
    
    # Find the specific result
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
        else:
            print(f"  ❌ No images in API response")
    else:
        print(f"❌ Target result {result.id} not found in API response")

def check_image_naming():
    """Check if image names are unique and descriptive"""
    print(f"\n=== CHECKING IMAGE NAMING ===")
    
    # Get all recent images
    images = GeneratedImage.objects.filter(source_type='sandbox').order_by('-created_at')[:20]
    
    print(f"Checking {len(images)} recent images:")
    
    name_counts = {}
    for image in images:
        name = image.name or "No Name"
        name_counts[name] = name_counts.get(name, 0) + 1
        
        print(f"  Image {image.id}: {name}")
        print(f"    Created: {image.created_at}")
        print(f"    Result ID: {image.sandbox_result.id}")
    
    print(f"\nName frequency analysis:")
    for name, count in name_counts.items():
        if count > 1:
            print(f"  ⚠️  '{name}' appears {count} times (not unique)")
        else:
            print(f"  ✅ '{name}' appears {count} time (unique)")

def create_improved_image_names():
    """Create improved image names based on content"""
    print(f"\n=== CREATING IMPROVED IMAGE NAMES ===")
    
    # Get images without descriptive names
    images = GeneratedImage.objects.filter(
        source_type='sandbox',
        name__in=['Sandbox Chart 1', 'Sandbox Chart 2', 'Sandbox Chart 3', 'Sandbox Chart 4', 'Sandbox Chart 5']
    ).order_by('created_at')
    
    print(f"Found {len(images)} images with generic names")
    
    # Create better names based on the analysis content
    improved_names = [
        "Temporal Trends Analysis",
        "Geographical Comparison Chart", 
        "Correlation Analysis Heatmap",
        "Prevalence Distribution Chart",
        "Mental Health Trends Overview"
    ]
    
    for i, image in enumerate(images):
        if i < len(improved_names):
            old_name = image.name
            new_name = improved_names[i]
            image.name = new_name
            image.save()
            print(f"  ✅ Updated Image {image.id}: '{old_name}' → '{new_name}'")

if __name__ == "__main__":
    result = debug_latest_execution()
    if result:
        test_api_call_simulation()
        check_image_naming()
        create_improved_image_names()

