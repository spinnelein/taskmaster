#!/usr/bin/env python3
"""
Test website pages to verify API integration
NO EMOJIS
"""
import requests
import time

def test_website_pages():
    frontend_url = "http://localhost:5173"
    backend_url = "http://localhost:8000"
    
    # Test pages to check
    pages = [
        ("/", "Home/Dashboard"),
        ("/schedule", "Schedule"),
        ("/events", "Events"),
        ("/tasks", "Tasks"),
        ("/initiatives", "Initiatives"),
        ("/projects", "Projects")
    ]
    
    print("=== TESTING WEBSITE PAGES ===")
    print(f"Frontend: {frontend_url}")
    print(f"Backend: {backend_url}")
    print()
    
    # First verify backend is responding
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("OK Backend is healthy")
        else:
            print("ERROR Backend health check failed")
            return
    except Exception as e:
        print(f"ERROR Backend not responding: {e}")
        return
    
    # Test each frontend page
    for path, name in pages:
        try:
            print(f"Testing {name} ({path})...")
            response = requests.get(f"{frontend_url}{path}", timeout=10)
            
            if response.status_code == 200:
                # Check if page contains expected content
                content = response.text.lower()
                
                # Look for common error indicators
                has_errors = any(error in content for error in [
                    "failed to load", "error loading", "500", "internal server error",
                    "cannot read", "undefined", "null", "error:"
                ])
                
                if has_errors:
                    print(f"  ERROR Page loads but may have errors")
                else:
                    print(f"  OK Page loads successfully")
                    
            else:
                print(f"  ERROR HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ERROR Timeout (page may be loading slowly)")
        except Exception as e:
            print(f"  ERROR Error: {e}")
        
        time.sleep(1)  # Brief pause between requests
    
    print()
    print("=== API ENDPOINT TEST ===")
    
    # Test API endpoints that the frontend uses
    api_endpoints = [
        "/api/events",
        "/api/tasks", 
        "/api/initiatives",
        "/api/projects"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 'N/A')
                print(f"  OK {endpoint} - {total} items")
            else:
                print(f"  ERROR {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            print(f"  ERROR {endpoint} - Error: {e}")

if __name__ == "__main__":
    test_website_pages()