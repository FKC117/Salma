#!/usr/bin/env python3
"""
Test admin login
"""
import requests
import json

def test_admin_login():
    """Test admin login functionality"""
    base_url = "http://localhost:8000"
    
    print("🔐 Testing Admin Login...")
    print("=" * 40)
    
    # Test admin page
    try:
        response = requests.get(f"{base_url}/admin/", timeout=5)
        print(f"Admin page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Admin page accessible")
            if "Django administration" in response.text:
                print("✅ Django admin interface found")
        elif response.status_code == 302:
            print("✅ Admin page redirects to login (normal)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Admin page error: {e}")
    
    # Test login page
    try:
        response = requests.get(f"{base_url}/admin/login/", timeout=5)
        print(f"Login page status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login page accessible")
            if "username" in response.text and "password" in response.text:
                print("✅ Login form found")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Login page error: {e}")
    
    print("\n📋 Admin Credentials:")
    print("Username: admin")
    print("Password: admin123")
    print("\n🌐 Access URLs:")
    print(f"Admin: {base_url}/admin/")
    print(f"Dashboard: {base_url}/")

if __name__ == "__main__":
    test_admin_login()
