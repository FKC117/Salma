#!/usr/bin/env python3
"""
Simple test to check Django server status
"""
import requests
import json

def test_server():
    """Test basic server functionality"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Django Server...")
    print("=" * 40)
    
    # Test 1: Admin page (should work)
    try:
        response = requests.get(f"{base_url}/admin/", timeout=5)
        print(f"Admin page: {response.status_code}")
        if response.status_code == 200:
            print("✅ Admin page accessible")
        elif response.status_code == 302:
            print("✅ Admin page redirects (normal)")
    except Exception as e:
        print(f"❌ Admin page error: {e}")
    
    # Test 2: API endpoint (should work)
    try:
        response = requests.get(f"{base_url}/api/tools/list_tools/", timeout=5)
        print(f"API endpoint: {response.status_code}")
        if response.status_code in [200, 403, 401]:
            print("✅ API endpoint accessible")
        else:
            print(f"❌ API endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API endpoint error: {e}")
    
    # Test 3: Dashboard with detailed error
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"Dashboard: {response.status_code}")
        if response.status_code == 200:
            print("✅ Dashboard accessible")
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    test_server()
