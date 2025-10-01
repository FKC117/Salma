"""
Debug script to check dashboard rendering
"""
import requests

def debug_dashboard():
    # Test the analytics dashboard URL directly
    print("Testing direct dashboard access...")
    response = requests.get('http://127.0.0.1:8000/analytics/dashboard/')
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    # Check if it's HTML content
    content_type = response.headers.get('content-type', '')
    print(f"Content type: {content_type}")
    
    # Show first 500 characters of response
    print(f"Response preview: {response.text[:500]}")
    
    # Test the analytics home URL
    print("\nTesting analytics home URL...")
    response = requests.get('http://127.0.0.1:8000/analytics/')
    print(f"Status code: {response.status_code}")
    print(f"Redirect location: {response.headers.get('location', 'No redirect')}")
    
    print("\nDebug test completed!")

if __name__ == "__main__":
    debug_dashboard()