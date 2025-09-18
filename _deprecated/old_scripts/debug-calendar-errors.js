const { chromium } = require('playwright');

(async () => {
  let browser, context, page;
  
  try {
    console.log('Debugging calendar loading errors...');
    
    browser = await chromium.launch({ 
      headless: false,
      slowMo: 1000 
    });
    
    context = await browser.newContext({
      viewport: { width: 1400, height: 900 }
    });
    
    page = await context.newPage();
    
    // Log all console messages
    page.on('console', (msg) => {
      console.log(`CONSOLE [${msg.type()}]: ${msg.text()}`);
    });
    
    // Log all errors
    page.on('pageerror', (error) => {
      console.log(`PAGE ERROR: ${error.message}`);
    });
    
    // Log network failures
    page.on('requestfailed', (request) => {
      console.log(`NETWORK FAILED: ${request.method()} ${request.url()} - ${request.failure().errorText}`);
    });
    
    // Navigate to schedule page
    await page.goto('http://localhost:5175/schedule');
    console.log('Page navigation complete');
    
    await page.waitForTimeout(5000);
    
    // Check if FullCalendar components are in DOM
    const fcToolbar = await page.locator('.fc-toolbar').count();
    const fcEvent = await page.locator('.fc-event').count();
    const fullCalendarDiv = await page.locator('.fullcalendar-container').count();
    
    console.log(`FullCalendar elements found:`);
    console.log(`  - .fullcalendar-container: ${fullCalendarDiv}`);
    console.log(`  - .fc-toolbar: ${fcToolbar}`);
    console.log(`  - .fc-event: ${fcEvent}`);
    
    // Check for loading indicator
    const loading = await page.locator('text=Loading events').count();
    console.log(`  - Loading indicator: ${loading}`);
    
    // Get page title and check if it loaded correctly
    const title = await page.title();
    console.log(`Page title: ${title}`);
    
    await page.waitForTimeout(5000);
    
  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();