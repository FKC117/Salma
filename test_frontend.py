#!/usr/bin/env python3
"""
Test script for frontend implementation
"""
import requests
import time

def test_frontend():
    """Test the frontend implementation"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Frontend Implementation...")
    print("=" * 50)
    
    # Test 1: Dashboard page accessibility
    print("\n1. Testing Dashboard Page...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard page loads successfully")
            if "Data Analysis System" in response.text:
                print("✅ Page title found")
            if "dashboard-container" in response.text:
                print("✅ Three-panel layout found")
            if "tools-panel" in response.text:
                print("✅ Tools panel found")
            if "dashboard-panel" in response.text:
                print("✅ Dashboard panel found")
            if "chat-panel" in response.text:
                print("✅ Chat panel found")
        else:
            print(f"❌ Dashboard page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard page error: {e}")
    
    # Test 2: Upload form accessibility
    print("\n2. Testing Upload Form...")
    try:
        response = requests.get(f"{base_url}/upload-form/", timeout=10)
        if response.status_code == 200:
            print("✅ Upload form loads successfully")
            if "uploadModal" in response.text:
                print("✅ Upload modal found")
            if "file" in response.text and "dataset_name" in response.text:
                print("✅ Form fields found")
        else:
            print(f"❌ Upload form failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Upload form error: {e}")
    
    # Test 3: Static files accessibility
    print("\n3. Testing Static Files...")
    try:
        response = requests.get(f"{base_url}/static/analytics/css/style.css", timeout=10)
        if response.status_code == 200:
            print("✅ CSS file accessible")
        else:
            print(f"❌ CSS file failed: {response.status_code}")
    except Exception as e:
        print(f"❌ CSS file error: {e}")
    
    try:
        response = requests.get(f"{base_url}/static/analytics/js/main.js", timeout=10)
        if response.status_code == 200:
            print("✅ JavaScript file accessible")
        else:
            print(f"❌ JavaScript file failed: {response.status_code}")
    except Exception as e:
        print(f"❌ JavaScript file error: {e}")
    
    # Test 4: HTMX integration
    print("\n4. Testing HTMX Integration...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            if "htmx.org" in response.text:
                print("✅ HTMX library loaded")
            if "htmx-indicator" in response.text:
                print("✅ HTMX indicators found")
            if "hx-post" in response.text:
                print("✅ HTMX attributes found")
        else:
            print(f"❌ HTMX test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ HTMX test error: {e}")
    
    # Test 5: Bootstrap integration
    print("\n5. Testing Bootstrap Integration...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            if "bootstrap" in response.text.lower():
                print("✅ Bootstrap library loaded")
            if "bootstrap-icons" in response.text:
                print("✅ Bootstrap Icons loaded")
            if "navbar" in response.text:
                print("✅ Bootstrap components found")
        else:
            print(f"❌ Bootstrap test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Bootstrap test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Frontend Testing Complete!")
    print("\nNext steps:")
    print("- Open http://localhost:8000 in your browser")
    print("- Test the three-panel layout")
    print("- Try uploading a dataset")
    print("- Test the AI chat functionality")

if __name__ == "__main__":
    test_frontend()
