// Simple test for task completion button
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const logsDir = path.join(__dirname, '../logs');
const timestamp = Date.now();
const logFile = path.join(logsDir, `simple-complete-test-${timestamp}.log`);

function log(message) {
  const entry = `[${new Date().toISOString()}] ${message}`;
  console.log(entry);
  fs.appendFileSync(logFile, entry + '\n');
}

async function testComplete() {
  log('=== STARTING SIMPLE COMPLETE BUTTON TEST ===');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 // Very slow to see what's happening
  });
  
  const page = await browser.newPage();
  
  // Log console messages
  page.on('console', msg => {
    log(`CONSOLE [${msg.type()}]: ${msg.text()}`);
  });
  
  // Log network activity
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/complete')) {
      log(`REQUEST: ${request.method()} ${url}`);
    }
  });
  
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/complete')) {
      const body = await response.text().catch(() => 'no body');
      log(`RESPONSE: ${response.status()} ${url} - Body: ${body}`);
    }
  });
  
  try {
    // Go to tasks page
    log('Navigating to tasks page...');
    await page.goto('http://localhost:5000/tasks', { waitUntil: 'networkidle' });
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Check if completeTask function exists
    const hasFunction = await page.evaluate(() => typeof completeTask === 'function');
    log(`completeTask function exists: ${hasFunction}`);
    
    // Get function code
    if (hasFunction) {
      const code = await page.evaluate(() => completeTask.toString());
      log(`completeTask function:\n${code}`);
    }
    
    // Find first complete button
    const button = await page.$('button:has-text("Complete")').catch(() => null);
    
    if (!button) {
      log('ERROR: No complete button found!');
      await browser.close();
      return;
    }
    
    // Get button info
    const info = await button.evaluate(btn => ({
      text: btn.textContent,
      onclick: btn.getAttribute('onclick'),
      disabled: btn.disabled,
      taskTitle: btn.closest('.task-item')?.querySelector('.task-title')?.textContent
    }));
    
    log(`Found button for task: "${info.taskTitle}"`);
    log(`Button onclick: ${info.onclick}`);
    
    // Take screenshot before
    await page.screenshot({ path: path.join(logsDir, `before-${timestamp}.png`) });
    
    log('\n=== CLICKING COMPLETE BUTTON ===');
    
    // Click it
    await button.click();
    
    // Wait for any response
    await page.waitForTimeout(5000);
    
    // Take screenshot after
    await page.screenshot({ path: path.join(logsDir, `after-${timestamp}.png`) });
    
    // Check if task is still visible
    const taskStillVisible = await page.$eval('.task-item', (item) => {
      const title = item.querySelector('.task-title');
      return title ? title.textContent : null;
    }).catch(() => null);
    
    log(`First task after click: "${taskStillVisible}"`);
    
  } catch (error) {
    log(`ERROR: ${error.message}`);
    log(error.stack);
  }
  
  await page.waitForTimeout(3000);
  await browser.close();
  
  log('\n=== TEST COMPLETE ===');
  log(`Log saved to: ${logFile}`);
}

testComplete().catch(console.error);