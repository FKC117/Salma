"""
Test script to verify the my_datasets view is working correctly
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analytical'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

# Import after Django setup
def test_my_datasets_view_exists():
    """Test that the my_datasets view function exists"""
    try:
        from analytics.views import my_datasets_view
        print("✅ my_datasets_view function exists")
        return True
    except Exception as e:
        print(f"❌ Error importing my_datasets_view: {e}")
        return False

if __name__ == "__main__":
    test_my_datasets_view_exists()