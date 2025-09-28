"""
Verification script to check if the implementation files exist
"""
import os

def verify_files():
    """Verify that all implementation files exist"""
    files_to_check = [
        'analytics/templates/analytics/my_datasets.html',
        'analytics/views.py',
        'analytics/urls.py',
        'analytics/templates/analytics/partials/navbar.html',
        'analytics/templates/analytics/dashboard.html'
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} does not exist")
            all_exist = False
    
    return all_exist

def verify_view_function():
    """Verify that the my_datasets_view function is defined in views.py"""
    views_file = 'analytics/views.py'
    if not os.path.exists(views_file):
        print(f"❌ {views_file} does not exist")
        return False
    
    try:
        with open(views_file, 'r') as f:
            content = f.read()
            if 'def my_datasets_view(' in content:
                print("✅ my_datasets_view function is defined in views.py")
                return True
            else:
                print("❌ my_datasets_view function is not defined in views.py")
                return False
    except Exception as e:
        print(f"❌ Error reading {views_file}: {e}")
        return False

def verify_url_pattern():
    """Verify that the URL pattern is defined in urls.py"""
    urls_file = 'analytics/urls.py'
    if not os.path.exists(urls_file):
        print(f"❌ {urls_file} does not exist")
        return False
    
    try:
        with open(urls_file, 'r') as f:
            content = f.read()
            if 'my_datasets_view' in content:
                print("✅ my_datasets URL pattern is defined in urls.py")
                return True
            else:
                print("❌ my_datasets URL pattern is not defined in urls.py")
                return False
    except Exception as e:
        print(f"❌ Error reading {urls_file}: {e}")
        return False

if __name__ == "__main__":
    print("Verifying implementation...")
    print("=" * 50)
    
    files_ok = verify_files()
    print()
    
    view_ok = verify_view_function()
    print()
    
    url_ok = verify_url_pattern()
    print()
    
    if files_ok and view_ok and url_ok:
        print("✅ All implementation checks passed!")
    else:
        print("❌ Some implementation checks failed!")