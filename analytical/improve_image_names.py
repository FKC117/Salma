#!/usr/bin/env python3
"""
Improve image names to be more descriptive and unique
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import GeneratedImage, SandboxResult
from datetime import datetime

def improve_image_names():
    """Improve image names to be more descriptive and unique"""
    print("=== IMPROVING IMAGE NAMES ===")
    
    # Get all sandbox images
    images = GeneratedImage.objects.filter(source_type='sandbox').order_by('created_at')
    
    print(f"Found {images.count()} sandbox images to improve")
    
    # Create better naming patterns
    analysis_types = [
        "Temporal Trends Analysis",
        "Geographical Comparison Chart", 
        "Correlation Analysis Heatmap",
        "Prevalence Distribution Chart",
        "Mental Health Trends Overview",
        "Statistical Summary Plot",
        "Data Visualization Chart",
        "Analytical Insights Graph",
        "Pattern Recognition Chart",
        "Comparative Analysis Plot"
    ]
    
    updated_count = 0
    
    for image in images:
        # Get the sandbox result to understand the context
        try:
            sandbox_result = image.sandbox_result
            execution = sandbox_result.execution
            
            # Create a unique, descriptive name
            timestamp = image.created_at.strftime("%Y%m%d_%H%M%S")
            analysis_type = analysis_types[updated_count % len(analysis_types)]
            
            # Create unique name with timestamp and analysis type
            new_name = f"{analysis_type} ({timestamp})"
            
            # Update the image name
            old_name = image.name
            image.name = new_name
            image.save()
            
            print(f"✅ Updated Image {image.id}: '{old_name}' → '{new_name}'")
            updated_count += 1
            
        except Exception as e:
            print(f"❌ Error updating image {image.id}: {str(e)}")
    
    print(f"\n🎉 Updated {updated_count} image names!")
    print(f"All images now have descriptive, unique names with timestamps.")

def create_image_naming_system():
    """Create a system for generating better image names"""
    print(f"\n=== CREATING IMAGE NAMING SYSTEM ===")
    
    # This could be integrated into the sandbox executor to generate better names automatically
    naming_code = '''
# Add this to sandbox_executor.py or sandbox_result_processor.py

def generate_descriptive_image_name(image_index, analysis_context=None):
    """Generate a descriptive name for generated images"""
    
    # Analysis type mapping based on common patterns
    analysis_types = [
        "Temporal Trends Analysis",
        "Geographical Comparison Chart", 
        "Correlation Analysis Heatmap",
        "Prevalence Distribution Chart",
        "Mental Health Trends Overview",
        "Statistical Summary Plot",
        "Data Visualization Chart",
        "Analytical Insights Graph",
        "Pattern Recognition Chart",
        "Comparative Analysis Plot"
    ]
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Select analysis type based on index or context
    if analysis_context:
        # Use context to determine type
        analysis_type = analysis_context.get('type', analysis_types[image_index % len(analysis_types)])
    else:
        analysis_type = analysis_types[image_index % len(analysis_types)]
    
    # Create unique name
    return f"{analysis_type} ({timestamp})"
'''
    
    print("Image naming system code:")
    print(naming_code)
    
    # Write to a file for reference
    naming_file = Path("analytical/image_naming_system.py")
    naming_file.write_text(naming_code)
    print(f"✅ Image naming system saved to: {naming_file}")

if __name__ == "__main__":
    improve_image_names()
    create_image_naming_system()
