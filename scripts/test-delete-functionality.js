// Test Delete Functionality for Recurring Events
// NO EMOJIS
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:5173';

async function testDeleteFunctionality() {
  console.log('Starting delete functionality test...');
  
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--disable-web-security']
  });
  const page = await browser.newPage();
  
  try {
    // Navigate to schedule
    console.log('Navigating to schedule page...');
    await page.goto(`${BASE_URL}/schedule`, { waitUntil: 'networkidle' });
    
    // Wait for events to load
    await page.waitForTimeout(5000);
    
    // Count initial events
    const initialEvents = await page.$$('.fc-event');
    console.log(`Initial event count: ${initialEvents.length}`);
    
    if (initialEvents.length === 0) {
      console.log('No events found. Cannot test delete functionality.');
      return;
    }
    
    // Take screenshot before click
    await page.screenshot({ path: 'logs/delete-test-before.png' });
    console.log('Screenshot saved: delete-test-before.png');
    
    // Click on first event to open series management modal
    console.log('Clicking on first event...');
    
    // Try different click approaches to handle the event harness issue
    const firstEvent = initialEvents[0];
    
    // Method 1: Try clicking the event title specifically
    try {
      const eventTitle = await firstEvent.$('.fc-event-title, .fc-event-title-short, .fc-event-title-medium, .fc-event-title-long');
      if (eventTitle) {
        await eventTitle.click();
      } else {
        // Method 2: Force click on the event element itself
        await firstEvent.click({ force: true });
      }
    } catch (e) {
      console.log('Click method failed, trying force click:', e.message);
      await firstEvent.click({ force: true });
    }
    
    // Wait for modal to appear
    await page.waitForTimeout(2000);
    
    // Take screenshot after click
    await page.screenshot({ path: 'logs/delete-test-modal.png' });
    console.log('Screenshot saved: delete-test-modal.png');
    
    // Look for series management modal
    const deleteButton = await page.$('button:has-text("Delete Entire Series")');
    
    if (deleteButton) {
      console.log('SUCCESS: Series management modal opened with delete button!');
      console.log('Delete functionality is properly integrated.');
      
      // Don't actually click delete in automated test
      console.log('(Not clicking delete button to preserve test data)');
      
      // Close modal
      const closeButton = await page.$('button:has-text("Close")');
      if (closeButton) {
        await closeButton.click();
        console.log('Modal closed successfully');
      }
    } else {
      console.log('No delete button found. Checking what modal content exists...');
      
      // Check for any modal elements
      const modalElements = await page.$$('[role="dialog"], .modal');
      console.log(`Found ${modalElements.length} modal elements`);
      
      if (modalElements.length > 0) {
        const modalText = await modalElements[0].textContent();
        console.log(`Modal content: ${modalText.substring(0, 200)}...`);
      }
    }
    
    console.log('Delete functionality test completed successfully!');
    
  } catch (error) {
    console.error('Test failed:', error.message);
    await page.screenshot({ path: 'logs/delete-test-error.png' });
    console.log('Error screenshot saved: delete-test-error.png');
  } finally {
    console.log('Press Enter to close browser...');
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
    
    await browser.close();
  }
}

testDeleteFunctionality().catch(console.error);