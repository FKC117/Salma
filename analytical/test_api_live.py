#!/usr/bin/env python3
"""
Test the live API endpoint
"""

import os
import sys
import django
import requests
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
django.setup()

from analytics.models import User, AnalysisSession, SandboxResult

def test_live_api():
    """Test the live API endpoint"""
    print("=== TESTING LIVE API ENDPOINT ===")
    
    # Get the most recent result with images
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No sandbox results with images found")
        return False
        
    session_id = result.session.id
    print(f"Testing with Session ID: {session_id}")
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)
    
    # Test the API endpoint
    url = f"http://localhost:8000/enhanced-chat/sandbox-results/?session_id={session_id}"
    print(f"Testing URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API endpoint working!")
            print(f"Response structure:")
            print(f"  Success: {data.get('success')}")
            print(f"  Count: {data.get('count')}")
            print(f"  Results: {len(data.get('results', []))}")
            
            # Check the specific result
            target_result = None
            for r in data.get('results', []):
                if r['id'] == result.id:
                    target_result = r
                    break
            
            if target_result:
                print(f"\n✅ Found target result {result.id}:")
                print(f"  Has Images: {target_result['has_images']}")
                print(f"  Image Count: {target_result['image_count']}")
                print(f"  Images: {len(target_result['images'])}")
                
                if target_result['images']:
                    print(f"  ✅ Images available for frontend")
                    for img in target_result['images']:
                        print(f"    Image {img['id']}: {img['name']}")
                        print(f"      Data Length: {len(img['image_data']) if img['image_data'] else 0}")
                        print(f"      Format: {img['image_format']}")
                        print(f"      Dimensions: {img['width']}x{img['height']}")
                        
                        # Test if the image data would work in HTML
                        if img['image_data'] and img['image_data'].startswith('data:image/'):
                            print(f"      ✅ Valid base64 data URL")
                        else:
                            print(f"      ❌ Invalid base64 format")
                else:
                    print(f"  ❌ No images in API response")
            else:
                print(f"❌ Target result {result.id} not found in API response")
                
            return True
        else:
            print(f"❌ API failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def create_frontend_debug_html():
    """Create a debug HTML file to test frontend JavaScript"""
    print(f"\n=== CREATING FRONTEND DEBUG HTML ===")
    
    result = SandboxResult.objects.filter(has_images=True).order_by('-created_at').first()
    if not result:
        print("❌ No results found")
        return
        
    session_id = result.session.id
    print(f"Creating debug HTML for Session ID: {session_id}")
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Sandbox Image Debug</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #1a1a1a; color: #ffffff; }}
        .container {{ margin-top: 50px; }}
        .debug-section {{ margin: 20px 0; padding: 20px; border: 1px solid #444; border-radius: 8px; }}
        .image-container {{ margin: 20px 0; }}
        img {{ border: 2px solid #444; border-radius: 8px; }}
        .log {{ background: #000; padding: 10px; border-radius: 4px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Sandbox Image Debug</h1>
        <p>Session ID: {session_id}</p>
        <p>SandboxResult ID: {result.id}</p>
        
        <div class="debug-section">
            <h3>API Test</h3>
            <button onclick="testAPI()" class="btn btn-primary">Test API Call</button>
            <div id="apiResult" class="log mt-3"></div>
        </div>
        
        <div class="debug-section">
            <h3>Image Loading Test</h3>
            <div class="sandbox-images" data-sandbox-result-id="{result.id}">
                <strong>Images:</strong>
                <div class="text-muted">Images are processed inline...</div>
            </div>
        </div>
        
        <div class="debug-section">
            <h3>Console Log</h3>
            <div id="consoleLog" class="log"></div>
        </div>
    </div>

    <script>
        // Override console.log to show in the page
        const originalLog = console.log;
        const originalError = console.error;
        
        function addToLog(message, type = 'log') {{
            const logDiv = document.getElementById('consoleLog');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `[${{timestamp}}] ${{message}}`;
            logEntry.style.color = type === 'error' ? '#ff6b6b' : '#ffffff';
            logDiv.appendChild(logEntry);
            logDiv.scrollTop = logDiv.scrollHeight;
        }}
        
        console.log = function(...args) {{
            originalLog.apply(console, args);
            addToLog(args.join(' '), 'log');
        }};
        
        console.error = function(...args) {{
            originalError.apply(console, args);
            addToLog(args.join(' '), 'error');
        }};
        
        // Test API function
        async function testAPI() {{
            const resultDiv = document.getElementById('apiResult');
            resultDiv.innerHTML = 'Testing API...';
            
            try {{
                console.log('Testing API endpoint...');
                const response = await fetch('/enhanced-chat/sandbox-results/?session_id={session_id}');
                console.log(`API response status: ${{response.status}}`);
                
                const data = await response.json();
                console.log('API response data:', data);
                
                resultDiv.innerHTML = `<pre>${{JSON.stringify(data, null, 2)}}</pre>`;
                
                if (data.success && data.results) {{
                    const targetResult = data.results.find(r => r.id === {result.id});
                    if (targetResult && targetResult.images) {{
                        console.log(`Found ${{targetResult.images.length}} images for result {result.id}`);
                    }} else {{
                        console.error('No images found in API response');
                    }}
                }}
                
            }} catch (error) {{
                console.error('API test failed:', error);
                resultDiv.innerHTML = `Error: ${{error.message}}`;
            }}
        }}
        
        // Function to get current session ID (from the original code)
        function getCurrentSessionId() {{
            // Try to get from various sources
            const sessionElement = document.querySelector('[data-session-id]');
            if (sessionElement) {{
                const sessionId = sessionElement.getAttribute('data-session-id');
                console.log(`Found session ID from data attribute: ${{sessionId}}`);
                return sessionId;
            }}
            
            // Try to get from URL parameters
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('session_id');
            if (sessionId) {{
                console.log(`Found session ID from URL: ${{sessionId}}`);
                return sessionId;
            }}
            
            // Try to get from global variable
            if (window.currentSessionId) {{
                console.log(`Found session ID from global variable: ${{window.currentSessionId}}`);
                return window.currentSessionId;
            }}
            
            console.error('No session ID found from any source');
            return null;
        }}
        
        // Function to load sandbox images (from the original code)
        async function loadSandboxImages(sandboxResultId, container) {{
            try {{
                console.log(`Loading images for SandboxResult ${{sandboxResultId}}`);
                
                // Get current session ID from the page
                const sessionId = getCurrentSessionId();
                if (!sessionId) {{
                    console.error('No session ID found');
                    return;
                }}
                
                // Fetch sandbox results
                console.log(`Making API call to: /enhanced-chat/sandbox-results/?session_id=${{sessionId}}`);
                const response = await fetch(`/enhanced-chat/sandbox-results/?session_id=${{sessionId}}`);
                console.log(`API response status: ${{response.status}}`);
                const data = await response.json();
                console.log(`API response data:`, data);
                
                if (data.success && data.results) {{
                    // Find the specific sandbox result
                    const result = data.results.find(r => r.id === sandboxResultId);
                    if (result && result.images && result.images.length > 0) {{
                        console.log(`Found ${{result.images.length}} images for SandboxResult ${{sandboxResultId}}`);
                        
                        // Clear the loading message
                        container.innerHTML = '<strong>Images:</strong>';
                        
                        // Add each image
                        result.images.forEach((image, index) => {{
                            const img = document.createElement('img');
                            img.src = image.image_data;
                            img.alt = image.name || `Chart ${{index + 1}}`;
                            img.className = 'img-fluid rounded mt-2';
                            img.style.maxWidth = '100%';
                            img.style.height = 'auto';
                            img.style.border = '1px solid #444';
                            
                            // Add image info
                            const imageInfo = document.createElement('div');
                            imageInfo.className = 'text-muted small mt-1';
                            imageInfo.textContent = `${{image.name}} (${{image.width}}x${{image.height}})`;
                            
                            container.appendChild(img);
                            container.appendChild(imageInfo);
                        }});
                    }} else {{
                        container.innerHTML = '<strong>Images:</strong> <span class="text-muted">No images found</span>';
                    }}
                }} else {{
                    console.error('Failed to fetch sandbox results:', data.error);
                    container.innerHTML = '<strong>Images:</strong> <span class="text-danger">Failed to load images</span>';
                }}
            }} catch (error) {{
                console.error('Error loading sandbox images:', error);
                container.innerHTML = '<strong>Images:</strong> <span class="text-danger">Error loading images</span>';
            }}
        }}
        
        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Page loaded, initializing image loading...');
            
            // Set the session ID for testing
            window.currentSessionId = '{session_id}';
            
            // Find image containers and load images
            const imageContainers = document.querySelectorAll('.sandbox-images[data-sandbox-result-id]');
            console.log(`Found ${{imageContainers.length}} sandbox image containers`);
            
            imageContainers.forEach((container, index) => {{
                const sandboxResultId = parseInt(container.getAttribute('data-sandbox-result-id'));
                console.log(`Container ${{index}}: SandboxResult ID = ${{sandboxResultId}}`);
                if (sandboxResultId) {{
                    loadSandboxImages(sandboxResultId, container);
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    # Write the debug HTML file
    debug_file = Path("analytical/debug_frontend.html")
    debug_file.write_text(html_content)
    print(f"✅ Debug HTML created: {debug_file}")
    print(f"  Open this file in a browser to test frontend JavaScript")

if __name__ == "__main__":
    success = test_live_api()
    if success:
        create_frontend_debug_html()
        print(f"\n🎉 API is working! Frontend issue needs investigation.")
    else:
        print(f"\n❌ API issue found!")

