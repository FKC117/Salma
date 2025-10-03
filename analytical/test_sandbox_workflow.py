#!/usr/bin/env python3
"""
Comprehensive Sandbox Workflow Test

This script tests the complete sandbox execution flow from LLM code generation
to result presentation, identifying issues and recommending fixes.
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

from analytics.models import User, AnalysisSession, Dataset, SandboxExecution, SandboxResult, GeneratedImage
from analytics.services.sandbox_executor import SandboxExecutor
from analytics.services.sandbox_result_processor import SandboxResultProcessor
from analytics.services.code_extraction_service import CodeExtractionService
from analytics.services.text_formatter import TextFormatter
from django.utils import timezone
import json

def test_sandbox_workflow():
    """Test the complete sandbox workflow"""
    print("=== COMPREHENSIVE SANDBOX WORKFLOW TEST ===")
    print()
    
    # Test 1: Code Extraction
    print("1. Testing Code Extraction Service")
    print("-" * 40)
    
    code_extractor = CodeExtractionService()
    
    # Sample LLM response with Python code
    sample_llm_response = """
    Here's a Python analysis of your data:

    ```python
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Load and analyze data
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [2, 4, 6, 8, 10]
    })
    
    # Create visualization
    plt.figure(figsize=(10, 6))
    plt.scatter(df['x'], df['y'])
    plt.title('Sample Data Visualization')
    plt.xlabel('X Values')
    plt.ylabel('Y Values')
    plt.show()
    
    # Print summary statistics
    print("Summary Statistics:")
    print(df.describe())
    ```
    
    The analysis shows a strong linear relationship between x and y values.
    """
    
    code_blocks = code_extractor.extract_python_code_blocks(sample_llm_response)
    print(f"✅ Extracted {len(code_blocks)} code blocks")
    
    if code_blocks:
        print(f"First code block length: {len(code_blocks[0]['code'])} characters")
        print(f"Code preview: {code_blocks[0]['code'][:100]}...")
    
    print()
    
    # Test 2: Sandbox Execution
    print("2. Testing Sandbox Execution")
    print("-" * 40)
    
    sandbox_executor = SandboxExecutor()
    
    # Get or create a test user
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("❌ Admin user not found. Please create an admin user first.")
        return
    
    # Get or create a test session
    try:
        session = AnalysisSession.objects.filter(user=user).first()
        if not session:
            # Create a test dataset and session
            dataset = Dataset.objects.create(
                user=user,
                name="Test Dataset",
                description="Test dataset for sandbox workflow",
                original_filename="test_data.csv",
                file_size_bytes=1024,
                file_hash="test_hash_123",
                original_format="csv",
                parquet_path="datasets/test_data.parquet",
                row_count=100,
                column_count=5,
                processing_status="completed"
            )
            session = AnalysisSession.objects.create(
                user=user,
                primary_dataset=dataset,
                name="Test Session"
            )
            print(f"✅ Created test session: {session.id}")
        else:
            print(f"✅ Using existing session: {session.id}")
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return
    
    # Test code execution
    if code_blocks:
        test_code = code_blocks[0]['code']
        print(f"Executing code ({len(test_code)} characters)...")
        
        try:
            execution_result = sandbox_executor.execute_code(
                code=test_code,
                language='python',
                user_id=user.id,
                session_id=session.id,
                timeout=30
            )
            
            print(f"✅ Execution completed")
            print(f"Success: {execution_result.get('success', False)}")
            print(f"Status: {execution_result.get('status', 'unknown')}")
            print(f"Output length: {len(execution_result.get('output', ''))}")
            print(f"Error: {execution_result.get('error', 'None')}")
            print(f"Execution ID: {execution_result.get('execution_id', 'None')}")
            
            if execution_result.get('output'):
                print(f"Output preview: {execution_result['output'][:200]}...")
                
        except Exception as e:
            print(f"❌ Execution failed: {e}")
            return
    
    print()
    
    # Test 3: Result Processing
    print("3. Testing Result Processing")
    print("-" * 40)
    
    result_processor = SandboxResultProcessor()
    
    # Get the latest execution
    try:
        latest_execution = SandboxExecution.objects.filter(
            user=user,
            session=session
        ).order_by('-created_at').first()
        
        if latest_execution:
            print(f"✅ Found execution: {latest_execution.id}")
            print(f"Status: {latest_execution.status}")
            print(f"Output length: {len(latest_execution.output or '')}")
            
            # Process the result
            sandbox_result = result_processor.create_sandbox_result(latest_execution)
            
            if sandbox_result:
                print(f"✅ Created SandboxResult: {sandbox_result.id}")
                print(f"Has images: {sandbox_result.has_images}")
                print(f"Image count: {sandbox_result.image_count}")
                print(f"Text output length: {len(sandbox_result.text_output or '')}")
                
                # Check for images
                images = sandbox_result.get_images()
                print(f"Images found: {len(images)}")
                
                for i, image in enumerate(images):
                    print(f"  Image {i+1}: {image.name} ({image.width}x{image.height})")
                    print(f"    File size: {image.file_size_bytes} bytes")
                    print(f"    Has base64 data: {bool(image.image_data)}")
            else:
                print("❌ Failed to create SandboxResult")
        else:
            print("❌ No executions found")
            
    except Exception as e:
        print(f"❌ Result processing failed: {e}")
    
    print()
    
    # Test 4: Text Formatting
    print("4. Testing Text Formatting")
    print("-" * 40)
    
    text_formatter = TextFormatter()
    
    # Sample analysis text
    sample_text = """
    ### 1. Data Analysis Results
    
    The analysis reveals several key insights:
    
    ```python
    import pandas as pd
    df.describe()
    ```
    
    ### 2. Key Findings
    
    * Strong correlation between variables
    * Significant patterns in the data
    * Recommendations for further analysis
    
    ### 3. Interpretation
    
    The results suggest that the data shows clear patterns that warrant further investigation.
    """
    
    formatted_text = text_formatter.format_analysis_text(sample_text)
    print(f"✅ Text formatting completed")
    print(f"Original length: {len(sample_text)}")
    print(f"Formatted length: {len(formatted_text)}")
    print(f"Formatted preview: {formatted_text[:200]}...")
    
    print()
    
    # Test 5: Data Flow Analysis
    print("5. Data Flow Analysis")
    print("-" * 40)
    
    # Check database records
    executions_count = SandboxExecution.objects.filter(user=user).count()
    results_count = SandboxResult.objects.filter(user=user).count()
    images_count = GeneratedImage.objects.filter(user=user).count()
    
    print(f"✅ Database Records:")
    print(f"  SandboxExecutions: {executions_count}")
    print(f"  SandboxResults: {results_count}")
    print(f"  GeneratedImages: {images_count}")
    
    # Check file system
    media_root = Path("media/sandbox")
    if media_root.exists():
        image_files = list(media_root.glob("*.png"))
        print(f"  Image files on disk: {len(image_files)}")
        
        for img_file in image_files[:3]:  # Show first 3
            print(f"    {img_file.name} ({img_file.stat().st_size} bytes)")
    else:
        print(f"  Sandbox media directory: Not found")
    
    print()
    
    # Test 6: Issue Identification
    print("6. Issue Identification")
    print("-" * 40)
    
    issues = []
    
    # Check for common issues
    if executions_count > 0:
        failed_executions = SandboxExecution.objects.filter(
            user=user,
            status='failed'
        ).count()
        
        if failed_executions > 0:
            issues.append(f"❌ {failed_executions} failed executions found")
        
        # Check for executions without results
        executions_without_results = SandboxExecution.objects.filter(
            user=user
        ).exclude(
            structured_result__isnull=False
        ).count()
        
        if executions_without_results > 0:
            issues.append(f"❌ {executions_without_results} executions without SandboxResult")
    
    # Check for image issues
    if images_count > 0:
        images_without_data = GeneratedImage.objects.filter(
            user=user,
            image_data__isnull=True
        ).count()
        
        if images_without_data > 0:
            issues.append(f"❌ {images_without_data} images without base64 data")
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No major issues detected")
    
    print()
    
    # Test 7: Recommendations
    print("7. Recommendations")
    print("-" * 40)
    
    recommendations = [
        "✅ Implement proper error handling for failed executions",
        "✅ Add retry mechanism for transient failures",
        "✅ Improve image processing and storage",
        "✅ Add better validation for code extraction",
        "✅ Implement caching for frequently used results",
        "✅ Add progress indicators for long-running executions",
        "✅ Improve UI formatting for better readability",
        "✅ Add export functionality for results"
    ]
    
    print("Recommended improvements:")
    for rec in recommendations:
        print(f"  {rec}")
    
    print()
    print("=== SANDBOX WORKFLOW TEST COMPLETE ===")

if __name__ == "__main__":
    test_sandbox_workflow()
