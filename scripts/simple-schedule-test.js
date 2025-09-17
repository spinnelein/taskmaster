// Simple Schedule Test - Test if frontend can load events
// NO EMOJIS
const { chromium } = require('playwright');

async function simpleTest() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Testing schedule page...');
  console.log('Navigate to: http://localhost:5173/schedule');
  
  await page.goto('http://localhost:5173/schedule');
  
  console.log('Waiting 10 seconds for events to load...');
  await page.waitForTimeout(10000);
  
  // Check for events
  const events = await page.$$('.fc-event');
  console.log(`Found ${events.length} events on the calendar`);
  
  // Take screenshot
  await page.screenshot({ path: 'logs/simple-schedule-test.png', fullPage: true });
  console.log('Screenshot saved: logs/simple-schedule-test.png');
  
  if (events.length > 0) {
    console.log('SUCCESS: Events are loading on the schedule!');
    console.log('Now testing series management click...');
    
    // Click first event
    await events[0].click();
    await page.waitForTimeout(2000);
    
    // Take screenshot after click
    await page.screenshot({ path: 'logs/simple-after-click.png', fullPage: true });
    console.log('Screenshot after click saved');
    
    // Check for modal
    const modals = await page.$$('[role="dialog"], .modal, .fixed.inset-0');
    console.log(`Found ${modals.length} modal elements after click`);
    
    if (modals.length > 0) {
      console.log('SUCCESS: Modal opened after clicking event!');
    }
  }
  
  console.log('Press Enter to close browser...');
  await new Promise(resolve => {
    process.stdin.once('data', resolve);
  });
  
  await browser.close();
}

simpleTest().catch(console.error);