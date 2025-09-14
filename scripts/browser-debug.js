// Browser debugging script using Playwright
// NO EMOJIS
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Ensure logs directory exists
const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const logFile = path.join(logsDir, `browser-console-${Date.now()}.log`);

async function debugBrowser(url = 'http://localhost:5175', options = {}) {
  const {
    headless = true,
    timeout = 30000,
    actions = [],
    waitFor = null
  } = options;

  console.log(`Starting browser debug session for ${url}`);
  console.log(`Logs will be saved to: ${logFile}`);
  
  const browser = await chromium.launch({ 
    headless,
    devtools: !headless
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture console logs
  page.on('console', async msg => {
    const timestamp = new Date().toISOString();
    const type = msg.type().toUpperCase().padEnd(7);
    const text = msg.text();
    
    // Get more details for objects
    let details = '';
    try {
      for (const arg of msg.args()) {
        const jsonValue = await arg.jsonValue().catch(() => null);
        if (jsonValue && typeof jsonValue === 'object') {
          details += '\n  ' + JSON.stringify(jsonValue, null, 2).replace(/\n/g, '\n  ');
        }
      }
    } catch (e) {
      // Ignore errors in getting details
    }
    
    const logEntry = `[${timestamp}] ${type} | ${text}${details}`;
    console.log(logEntry);
    fs.appendFileSync(logFile, logEntry + '\n');
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    const timestamp = new Date().toISOString();
    const errorEntry = `[${timestamp}] ERROR  | ${error.message}\n${error.stack || ''}`;
    console.error(errorEntry);
    fs.appendFileSync(logFile, errorEntry + '\n');
  });
  
  // Capture network errors
  page.on('requestfailed', request => {
    const timestamp = new Date().toISOString();
    const errorEntry = `[${timestamp}] NETWORK| Failed: ${request.method()} ${request.url()} - ${request.failure().errorText}`;
    console.error(errorEntry);
    fs.appendFileSync(logFile, errorEntry + '\n');
  });
  
  // Capture responses
  page.on('response', response => {
    if (response.status() >= 400) {
      const timestamp = new Date().toISOString();
      const entry = `[${timestamp}] HTTP   | ${response.status()} ${response.url()}`;
      console.log(entry);
      fs.appendFileSync(logFile, entry + '\n');
    }
  });
  
  try {
    // Navigate to the page
    console.log(`\nNavigating to ${url}...`);
    await page.goto(url, { waitUntil: 'networkidle' });
    console.log('Page loaded\n');
    
    // Execute any custom actions
    for (const action of actions) {
      console.log(`Executing: ${action.description || action.type}`);
      await executeAction(page, action);
    }
    
    // Wait for specific condition or timeout
    if (waitFor) {
      console.log(`Waiting for: ${waitFor}`);
      await page.waitForSelector(waitFor, { timeout });
    } else {
      console.log(`Observing for ${timeout/1000} seconds...`);
      await page.waitForTimeout(timeout);
    }
    
  } catch (error) {
    console.error('Error during browser session:', error.message);
    fs.appendFileSync(logFile, `\n[ERROR] ${error.message}\n${error.stack}\n`);
  }
  
  await browser.close();
  
  console.log('\n' + '='.repeat(50));
  console.log('Session Summary:');
  console.log(`Log file: ${logFile}`);
  console.log('='.repeat(50));
  
  // Return the log file path for further processing
  return logFile;
}

async function executeAction(page, action) {
  switch (action.type) {
    case 'click':
      await page.click(action.selector);
      break;
    case 'fill':
      await page.fill(action.selector, action.value);
      break;
    case 'select':
      await page.selectOption(action.selector, action.value);
      break;
    case 'wait':
      await page.waitForTimeout(action.duration || 1000);
      break;
    case 'screenshot':
      await page.screenshot({ path: action.path || 'screenshot.png' });
      break;
    case 'evaluate':
      return await page.evaluate(action.script);
    default:
      console.log(`Unknown action type: ${action.type}`);
  }
}

// Export for use as module
module.exports = { debugBrowser };

// If run directly, execute with default options
if (require.main === module) {
  const args = process.argv.slice(2);
  const url = args[0] || 'http://localhost:5175';
  const headless = !args.includes('--head');
  
  debugBrowser(url, { headless }).catch(console.error);
}