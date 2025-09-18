#!/usr/bin/env python3
"""
Test website with browser automation to verify data display
NO EMOJIS
"""
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def test_website_data():
    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not available, testing with requests only")
        return
    
    print("=== TESTING WEBSITE DATA DISPLAY ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Test Events page
            print("Testing Events page...")
            page.goto("http://localhost:5173/events", wait_until="networkidle")
            
            # Look for event data
            event_count_text = page.locator("[data-testid='event-count'], .event-count, h1, h2").first.text_content()
            if event_count_text:
                print(f"  Events page content: {event_count_text[:100]}...")
            
            # Check for any error messages
            error_elements = page.locator("text=error").all()
            if error_elements:
                print(f"  Found {len(error_elements)} error indicators")
            else:
                print("  No error indicators found")
            
            # Test Tasks page  
            print("Testing Tasks page...")
            page.goto("http://localhost:5173/tasks", wait_until="networkidle")
            
            # Look for task data
            task_content = page.locator("body").text_content()[:200]
            print(f"  Tasks page content: {task_content}...")
            
            # Test Schedule page
            print("Testing Schedule page...")
            page.goto("http://localhost:5173/schedule", wait_until="networkidle")
            
            schedule_content = page.locator("body").text_content()[:200]
            print(f"  Schedule page content: {schedule_content}...")
            
            print("Browser testing completed successfully")
            
        except Exception as e:
            print(f"Browser test error: {e}")
        finally:
            browser.close()

def simple_content_test():
    """Fallback test using requests"""
    import requests
    
    print("=== SIMPLE CONTENT TEST ===")
    
    pages = [
        ("http://localhost:5173/events", "Events"),
        ("http://localhost:5173/tasks", "Tasks"),
        ("http://localhost:5173/schedule", "Schedule")
    ]
    
    for url, name in pages:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Look for signs of successful React app loading
                react_indicators = [
                    'id="root"',
                    'react',
                    'vite',
                    name.lower()
                ]
                
                found_indicators = [ind for ind in react_indicators if ind.lower() in content.lower()]
                
                if found_indicators:
                    print(f"  {name}: React app detected (indicators: {found_indicators})")
                else:
                    print(f"  {name}: Page loaded but may not be React app")
                    
            else:
                print(f"  {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  {name}: Error - {e}")

if __name__ == "__main__":
    if PLAYWRIGHT_AVAILABLE:
        test_website_data()
    else:
        simple_content_test()