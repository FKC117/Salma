import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.services.code_extraction_service import CodeExtractionService

def test_code_detection():
    """Test if code detection is working after removing duplicate ViewSet"""
    
    # Sample LLM response with Python code
    sample_text = """
    This is an excellent way to visualize the relationships between features. 
    Since the dataset has over 30 columns, plotting the correlation matrix of all features 
    would result in a very cluttered and unreadable heatmap.
    
    Python Code
    
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
    
    # Create correlation heatmap
    plt.figure(figsize=(12, 10))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
    plt.title('Correlation Heatmap')
    plt.show()
    """
    
    print("=== TESTING CODE DETECTION ===")
    
    # Test code extraction
    extractor = CodeExtractionService()
    code_blocks = extractor.extract_python_code_blocks(sample_text)
    
    print(f"Found {len(code_blocks)} code blocks")
    
    for i, block in enumerate(code_blocks):
        print(f"\nCode Block {i+1}:")
        print(f"Code: {block['code'][:100]}...")
        print(f"Start: {block['start_pos']}, End: {block['end_pos']}")
    
    # Test formatting
    formatted_text = extractor.extract_and_format_code_blocks(sample_text)
    print(f"\n=== FORMATTED TEXT ===")
    print(formatted_text[:500] + "..." if len(formatted_text) > 500 else formatted_text)
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_code_detection()