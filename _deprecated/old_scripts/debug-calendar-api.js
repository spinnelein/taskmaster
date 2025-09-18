const { chromium } = require('playwright');

(async () => {
  let browser, context, page;
  
  try {
    console.log('Debugging calendar API calls...');
    
    browser = await chromium.launch({ 
      headless: false,
      slowMo: 1000 
    });
    
    context = await browser.newContext({
      viewport: { width: 1400, height: 900 }
    });
    
    page = await context.newPage();
    
    // Intercept network requests
    const apiCalls = [];
    page.on('response', async (response) => {
      if (response.url().includes('/api/events')) {
        console.log(`API Call: ${response.request().method()} ${response.url()}`);
        console.log(`Status: ${response.status()}`);
        
        try {
          const data = await response.json();
          console.log(`Response: ${JSON.stringify(data, null, 2)}`);
          
          if (data.events) {
            console.log(`\nEvents received: ${data.events.length}`);
            data.events.forEach((event, index) => {
              console.log(`  ${index + 1}. ${event.title} - ${event.start_time} to ${event.end_time}`);
            });
          }
        } catch (e) {
          console.log('Failed to parse response as JSON');
        }
      }
    });
    
    // Navigate to schedule page
    await page.goto('http://localhost:5175/schedule');
    await page.waitForLoadState('networkidle');
    
    // Wait for calendar to load
    await page.waitForTimeout(5000);
    
    // Check FullCalendar events in DOM
    const events = await page.locator('.fc-event').all();
    console.log(`\nDOM Events found: ${events.length}`);
    
    for (let i = 0; i < events.length; i++) {
      const event = events[i];
      const title = await event.locator('.fc-event-title').textContent().catch(() => 'No title');
      const time = await event.locator('.fc-event-time').textContent().catch(() => 'No time');
      console.log(`  DOM Event ${i + 1}: "${title}" at "${time}"`);
    }
    
    await page.waitForTimeout(3000);
    
  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();