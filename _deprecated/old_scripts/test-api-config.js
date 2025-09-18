// Test API Configuration After Fix
// NO EMOJIS
const { chromium } = require('playwright');

async function testAPIConfig() {
  console.log('Testing API configuration...');
  
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Capture console logs to see the debug output
  page.on('console', msg => {
    console.log(`Browser Console: ${msg.text()}`);
  });
  
  try {
    console.log('Navigating to http://localhost:5174/schedule...');
    await page.goto('http://localhost:5174/schedule');
    
    // Wait for the API configuration logs to appear
    await page.waitForTimeout(3000);
    
    console.log('Check the browser console output above for API configuration.');
    
  } catch (error) {
    console.error('Test failed:', error.message);
  } finally {
    console.log('Press Enter to close browser...');
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
    await browser.close();
  }
}

testAPIConfig().catch(console.error);