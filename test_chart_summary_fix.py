"""
Test script to verify the chart_summary parameter fix
"""

import sys
import os

# Add the analytics tools path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))

def test_chart_summary_fix():
    """Test that the chart_summary parameter is properly handled"""
    try:
        # Setup Django environment
        import django
        from django.conf import settings
        
        # Configure Django settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=[
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                    'analytics',
                ],
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                },
                SECRET_KEY='test-secret-key',
                USE_TZ=True,
            )
        
        django.setup()
        
        # Import the analysis result manager
        from analytics.services.analysis_result_manager import analysis_result_manager
        
        # Test data
        chart_summary_data = {
            'type': 'Correlation Heatmap',
            'data_points': 100,
            'variables': 3,
            'insights_count': 3
        }
        
        # Test calling create_chart_analysis_result with chart_summary parameter
        result_html = analysis_result_manager.create_chart_analysis_result(
            analysis_id="test_001",
            title="Test Chart Analysis",
            description="Test chart analysis with chart_summary parameter",
            chart_type="heatmap",
            data=None,  # No data for this test
            chart_summary=chart_summary_data  # This should now work without error
        )
        
        print("✓ Chart analysis result created successfully with chart_summary parameter")
        print(f"Result contains chart summary: {'chart_summary' in result_html if result_html else False}")
        return True
        
    except Exception as e:
        print(f"✗ Error testing chart_summary parameter: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing chart_summary parameter fix...")
    success = test_chart_summary_fix()
    if success:
        print("\n🎉 Fix verified successfully!")
        print("The chart_summary parameter is now properly handled.")
    else:
        print("\n❌ Fix verification failed.")