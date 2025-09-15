const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  let browser, context, page;
  
  try {
    console.log('Testing FullCalendar display and text visibility...');
    
    browser = await chromium.launch({ 
      headless: false,
      slowMo: 1000 
    });
    
    context = await browser.newContext({
      viewport: { width: 1400, height: 900 }
    });
    
    page = await context.newPage();
    
    // Navigate to schedule page
    await page.goto('http://localhost:5175/schedule');
    await page.waitForLoadState('networkidle');
    
    // Wait for calendar to render
    await page.waitForSelector('.fc-toolbar', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    // Take screenshot of full calendar
    await page.screenshot({
      path: path.join(__dirname, '..', 'logs', 'fullcalendar-overview.png'),
      fullPage: true
    });
    
    console.log('✅ Full calendar screenshot taken');
    
    // Switch to week view if not already
    const weekButton = page.locator('button:has-text("Week")');
    if (await weekButton.isVisible()) {
      await weekButton.click();
      await page.waitForTimeout(1000);
    }
    
    // Take focused screenshot of time slots
    const timeGrid = page.locator('.fc-timegrid-body');
    if (await timeGrid.isVisible()) {
      await timeGrid.screenshot({
        path: path.join(__dirname, '..', 'logs', 'fullcalendar-timegrid.png')
      });
      console.log('✅ Time grid screenshot taken');
    }
    
    // Check for events and their text visibility
    const events = await page.locator('.fc-event').count();
    console.log(`📅 Found ${events} events on calendar`);
    
    if (events > 0) {
      // Take screenshot of first few events
      const firstEvent = page.locator('.fc-event').first();
      if (await firstEvent.isVisible()) {
        await firstEvent.screenshot({
          path: path.join(__dirname, '..', 'logs', 'fullcalendar-event-detail.png')
        });
        console.log('✅ Event detail screenshot taken');
        
        // Get event text content
        const eventTitle = await firstEvent.locator('.fc-event-title').textContent().catch(() => 'No title');
        const eventTime = await firstEvent.locator('.fc-event-time').textContent().catch(() => 'No time');
        console.log(`📝 Sample event - Title: "${eventTitle}", Time: "${eventTime}"`);
      }
    }
    
    // Test slot height
    const slot = page.locator('.fc-timegrid-slot').first();
    if (await slot.isVisible()) {
      const slotBox = await slot.boundingBox();
      console.log(`📏 Time slot height: ${slotBox.height}px`);
    }
    
    console.log('\n🎯 Calendar display test completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();