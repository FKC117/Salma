"""
Test script to verify prescription app routing
"""
import requests

def test_prescription_routing():
    # Test the root URL (should show prescription app)
    response = requests.get('http://127.0.0.1:8000/')
    print(f"Root URL status code: {response.status_code}")
    
    # Test the analytics URL
    response = requests.get('http://127.0.0.1:8000/analytics/')
    print(f"Analytics URL status code: {response.status_code}")
    
    print("Routing test completed!")

if __name__ == "__main__":
    test_prescription_routing()