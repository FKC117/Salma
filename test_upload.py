import requests

# First, let's login to get a session
session = requests.Session()

# Get the login page to retrieve CSRF token
login_page = session.get('http://127.0.0.1:8000/accounts/login/')
print(f"Login page status: {login_page.status_code}")

# Parse CSRF token from login page (simplified approach)
import re
csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
if csrf_match:
    csrf_token = csrf_match.group(1)
    print(f"CSRF token found: {csrf_token[:10]}...")
else:
    print("CSRF token not found")
    exit(1)

# Login with CSRF token
login_data = {
    'username': 'testuser',
    'password': 'testpass123',
    'csrfmiddlewaretoken': csrf_token
}

# Set headers
headers = {
    'Referer': 'http://127.0.0.1:8000/accounts/login/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Try to login
login_response = session.post('http://127.0.0.1:8000/accounts/login/', data=login_data, headers=headers)
print(f"Login status: {login_response.status_code}")

# Check if we're logged in by accessing the dashboard
dashboard_response = session.get('http://127.0.0.1:8000/dashboard/')
print(f"Dashboard access: {dashboard_response.status_code}")

# Get CSRF token for upload
csrf_response = session.get('http://127.0.0.1:8000/api/csrf-token/')
if csrf_response.status_code == 200:
    csrf_data = csrf_response.json()
    upload_csrf = csrf_data.get('csrf_token')
    print(f"Upload CSRF token: {upload_csrf[:10]}...")
else:
    print("Failed to get CSRF token for upload")
    exit(1)

# Now try to upload the test file
with open('test_data.csv', 'rb') as f:
    files = {'file': ('test_data.csv', f, 'text/csv')}
    data = {
        'name': 'Test Dataset',
        'csrfmiddlewaretoken': upload_csrf
    }
    
    upload_headers = {
        'Referer': 'http://127.0.0.1:8000/dashboard/',
        'X-CSRFToken': upload_csrf
    }
    
    upload_response = session.post('http://127.0.0.1:8000/upload/', files=files, data=data, headers=upload_headers)
    print(f"Upload status: {upload_response.status_code}")
    print(f"Upload response: {upload_response.text[:500]}")