// Detailed Test for Task Complete Button
// NO EMOJIS
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const timestamp = Date.now();
const logFile = path.join(logsDir, `complete-button-test-${timestamp}.log`);

async function testCompleteButton() {
  console.log('=== TASK COMPLETION BUTTON TEST ===');
  console.log(`Log file: ${logFile}`);
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 // Slow down actions to see what's happening
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enhanced logging
  const log = (message) => {
    const timestamp = new Date().toISOString();
    const entry = `[${timestamp}] ${message}`;
    console.log(entry);
    fs.appendFileSync(logFile, entry + '\n');
  };
  
  // Capture console
  page.on('console', msg => {
    log(`CONSOLE [${msg.type()}]: ${msg.text()}`);
  });
  
  // Capture errors
  page.on('pageerror', error => {
    log(`PAGE ERROR: ${error.message}`);
  });
  
  // Capture network
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/api/tasks') || url.includes('complete')) {
      log(`REQUEST: ${request.method()} ${url}`);
      if (request.postData()) {
        log(`  Body: ${request.postData()}`);
      }
    }
  });
  
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/tasks') || url.includes('complete')) {
      try {
        const body = await response.text();
        log(`RESPONSE: ${response.status()} ${url}`);
        log(`  Body: ${body}`);
      } catch (e) {
        log(`RESPONSE: ${response.status()} ${url} (couldn't read body)`);
      }
    }
  });
  
  try {
    // Navigate to tasks page
    log('\n=== NAVIGATING TO TASKS PAGE ===');
    await page.goto('http://localhost:5000/tasks', { waitUntil: 'networkidle' });
    
    // Wait for tasks to load
    await page.waitForTimeout(2000);
    
    // Take initial screenshot
    await page.screenshot({ path: path.join(logsDir, `initial-${timestamp}.png`) });
    
    // Find the completeTask function in the page
    log('\n=== CHECKING JAVASCRIPT FUNCTIONS ===');
    const hasCompleteFunction = await page.evaluate(() => {
      return typeof window.completeTask === 'function';
    });
    log(`completeTask function exists: ${hasCompleteFunction}`);
    
    // Get the completeTask function code
    if (hasCompleteFunction) {
      const functionCode = await page.evaluate(() => {
        return window.completeTask.toString();
      });
      log('completeTask function code:');
      log(functionCode);
    }
    
    // Find all complete buttons
    log('\n=== FINDING COMPLETE BUTTONS ===');
    const completeButtons = await page.$$('button:has-text("Complete")');
    log(`Found ${completeButtons.length} complete buttons`);
    
    if (completeButtons.length === 0) {
      throw new Error('No complete buttons found');
    }
    
    // Get details about first button
    const buttonDetails = await completeButtons[0].evaluate(button => {
      return {
        text: button.textContent,
        onclick: button.getAttribute('onclick'),
        disabled: button.disabled,
        className: button.className,
        parentHTML: button.parentElement.outerHTML
      };
    });
    log('\nFirst button details:');
    log(JSON.stringify(buttonDetails, null, 2));
    
    // Extract task ID from onclick
    const onclickMatch = buttonDetails.onclick?.match(/completeTask\('([^']+)'\)/);
    const taskId = onclickMatch ? onclickMatch[1] : null;
    log(`\nExtracted task ID: ${taskId}`);
    
    // Take before screenshot
    await page.screenshot({ path: path.join(logsDir, `before-click-${timestamp}.png`) });
    
    // Clear console and network logs
    log('\n=== CLICKING COMPLETE BUTTON ===');
    
    // Click the button
    await completeButtons[0].click();
    
    // Wait for network activity
    await page.waitForTimeout(3000);
    
    // Take after screenshot
    await page.screenshot({ path: path.join(logsDir, `after-click-${timestamp}.png`) });
    
    // Check if button still exists
    const buttonStillExists = await completeButtons[0].isVisible().catch(() => false);
    log(`\nButton still visible: ${buttonStillExists}`);
    
    // Check for any alerts
    page.on('dialog', async dialog => {
      log(`ALERT: ${dialog.message()}`);
      await dialog.accept();
    });
    
    // Get current task count
    const activeTaskCount = await page.$$eval('.task-item', items => {
      return items.filter(item => !item.classList.contains('completed-task')).length;
    });
    log(`\nActive tasks remaining: ${activeTaskCount}`);
    
    // Check for any error messages
    const errors = await page.$$eval('.error, .alert, [class*="error"]', elements => 
      elements.map(el => el.textContent)
    );
    if (errors.length > 0) {
      log('\n=== ERROR MESSAGES ===');
      errors.forEach(err => log(`ERROR: ${err}`));
    }
    
  } catch (error) {
    log(`\n=== TEST ERROR ===`);
    log(error.message);
    log(error.stack);
  }
  
  // Keep browser open for observation
  await page.waitForTimeout(5000);
  
  await browser.close();
  
  console.log(`\n=== TEST COMPLETE ===`);
  console.log(`Check log file: ${logFile}`);
}

testCompleteButton().catch(console.error);