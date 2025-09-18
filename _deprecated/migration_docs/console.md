Instructions for Claude Code: Browser Console Debugging Setup
Overview
You need to set up Playwright for browser debugging instead of using curl. This will allow you to see actual browser console logs, JavaScript errors, and interact with the running application as a real browser would.
Step 1: Install Playwright
bash# Add Playwright to the project
npm install --save-dev playwright

# Install browser binaries (this installs Chromium, Firefox, and WebKit)
npx playwright install

# Or install just Chromium to save space
npx playwright install chromium
Step 2: Create Browser Debug Script
Create a new file scripts/browser-debug.js:
javascript// scripts/browser-debug.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Ensure logs directory exists
const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const logFile = path.join(logsDir, `browser-console-${Date.now()}.log`);

async function debugBrowser(url = 'http://localhost:3000', options = {}) {
  const {
    headless = true,
    timeout = 30000,
    actions = [],
    waitFor = null
  } = options;

  console.log(`🌐 Starting browser debug session for ${url}`);
  console.log(`📝 Logs will be saved to: ${logFile}`);
  
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
    console.log(`\n📍 Navigating to ${url}...`);
    await page.goto(url, { waitUntil: 'networkidle' });
    console.log('✅ Page loaded\n');
    
    // Execute any custom actions
    for (const action of actions) {
      console.log(`🎯 Executing: ${action.description || action.type}`);
      await executeAction(page, action);
    }
    
    // Wait for specific condition or timeout
    if (waitFor) {
      console.log(`⏳ Waiting for: ${waitFor}`);
      await page.waitForSelector(waitFor, { timeout });
    } else {
      console.log(`⏳ Observing for ${timeout/1000} seconds...`);
      await page.waitForTimeout(timeout);
    }
    
  } catch (error) {
    console.error('❌ Error during browser session:', error.message);
    fs.appendFileSync(logFile, `\n[ERROR] ${error.message}\n${error.stack}\n`);
  }
  
  await browser.close();
  
  console.log('\n' + '='.repeat(50));
  console.log('📊 Session Summary:');
  console.log(`📁 Log file: ${logFile}`);
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
    case 'eval':
      await page.evaluate(action.code);
      break;
    default:
      console.log(`Unknown action type: ${action.type}`);
  }
}

// Make it runnable from command line
if (require.main === module) {
  const args = process.argv.slice(2);
  const url = args[0] || 'http://localhost:3000';
  
  debugBrowser(url).catch(console.error);
}

module.exports = { debugBrowser };
Step 3: Create Utility Script for Common Debugging Tasks
Create scripts/browser-test.js:
javascript// scripts/browser-test.js
const { chromium } = require('playwright');

/**
 * Quick test function that you can modify for different debugging scenarios
 */
async function testScenario(scenario = 'basic') {
  const browser = await chromium.launch({ headless: false }); // Set to false to see the browser
  const page = await browser.newPage();
  
  // Always capture console
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  page.on('pageerror', err => console.error('ERROR:', err.message));
  
  await page.goto('http://localhost:3000');
  
  switch(scenario) {
    case 'create-task':
      // Test task creation
      await page.click('button:has-text("New Task")');
      await page.fill('input[name="title"]', 'Test Task from Playwright');
      await page.fill('textarea[name="description"]', 'This is a test');
      await page.click('button:has-text("Save")');
      break;
      
    case 'navigate':
      // Test navigation
      await page.click('a:has-text("Calendar")');
      await page.waitForSelector('.calendar-view');
      await page.click('a:has-text("Tasks")');
      await page.waitForSelector('.task-list');
      break;
      
    case 'form-validation':
      // Test form validation
      await page.click('button:has-text("New Task")');
      await page.click('button:has-text("Save")'); // Try to save empty form
      // Check for validation errors in console
      break;
      
    case 'api-test':
      // Test API calls by triggering them
      const response = await page.evaluate(async () => {
        const res = await fetch('/api/tasks');
        return {
          status: res.status,
          data: await res.json()
        };
      });
      console.log('API Response:', response);
      break;
      
    default:
      // Just load and wait
      console.log('Page loaded, watching for 10 seconds...');
      await page.waitForTimeout(10000);
  }
  
  await browser.close();
}

// Run specific scenario from command line
const scenario = process.argv[2] || 'basic';
console.log(`Running scenario: ${scenario}`);
testScenario(scenario).catch(console.error);
Step 4: Add NPM Scripts
Update package.json:
json{
  "scripts": {
    "debug": "node scripts/browser-debug.js",
    "debug:watch": "nodemon --watch src --exec 'node scripts/browser-debug.js'",
    "test:browser": "node scripts/browser-test.js",
    "test:create-task": "node scripts/browser-test.js create-task",
    "test:navigation": "node scripts/browser-test.js navigate",
    "test:forms": "node scripts/browser-test.js form-validation",
    "test:api": "node scripts/browser-test.js api-test",
    "logs:clean": "rm -rf logs/*.log",
    "logs:view": "tail -f logs/*.log"
  }
}
Step 5: Create Your Debugging Workflow Commands
Create scripts/debug-commands.js to replace curl usage:
javascript// scripts/debug-commands.js
const { chromium } = require('playwright');

class BrowserDebugger {
  constructor() {
    this.browser = null;
    this.page = null;
  }

  async init(url = 'http://localhost:3000') {
    this.browser = await chromium.launch({ headless: true });
    this.page = await this.browser.newPage();
    
    // Capture all console logs
    this.page.on('console', msg => {
      console.log(`[${msg.type()}]`, msg.text());
    });
    
    await this.page.goto(url);
    return this;
  }

  // Replace curl GET requests
  async get(endpoint) {
    const response = await this.page.evaluate(async (endpoint) => {
      const res = await fetch(endpoint);
      return {
        status: res.status,
        headers: Object.fromEntries(res.headers.entries()),
        body: await res.text()
      };
    }, endpoint);
    
    console.log(`GET ${endpoint}`);
    console.log(`Status: ${response.status}`);
    console.log(`Response:`, response.body);
    return response;
  }

  // Replace curl POST requests
  async post(endpoint, data) {
    const response = await this.page.evaluate(async (endpoint, data) => {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return {
        status: res.status,
        body: await res.json()
      };
    }, endpoint, data);
    
    console.log(`POST ${endpoint}`);
    console.log(`Status: ${response.status}`);
    console.log(`Response:`, response.body);
    return response;
  }

  // Check React component state
  async getReactState(selector) {
    const state = await this.page.evaluate((selector) => {
      const element = document.querySelector(selector);
      if (!element) return null;
      
      // Find React fiber
      const key = Object.keys(element).find(key => key.startsWith('__reactFiber'));
      if (!key) return null;
      
      let fiber = element[key];
      while (fiber) {
        if (fiber.memoizedState) {
          return fiber.memoizedState;
        }
        fiber = fiber.return;
      }
      return null;
    }, selector);
    
    console.log(`React State for ${selector}:`, state);
    return state;
  }

  // Check all network requests
  async monitorNetwork(duration = 5000) {
    const requests = [];
    
    this.page.on('request', req => {
      requests.push({
        method: req.method(),
        url: req.url(),
        headers: req.headers()
      });
    });
    
    await this.page.waitForTimeout(duration);
    
    console.log('Network Requests:', requests);
    return requests;
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Usage examples
async function debugExamples() {
  const debugger = await new BrowserDebugger().init();
  
  // Instead of: curl http://localhost:3000/api/tasks
  await debugger.get('/api/tasks');
  
  // Instead of: curl -X POST -d '{"title":"Test"}' http://localhost:3000/api/tasks
  await debugger.post('/api/tasks', { title: 'Test Task' });
  
  // Check React component state
  await debugger.getReactState('.task-form');
  
  // Monitor network calls
  await debugger.monitorNetwork(3000);
  
  await debugger.close();
}

if (require.main === module) {
  debugExamples().catch(console.error);
}

module.exports = BrowserDebugger;
How to Use This Instead of Curl
Old Way (with curl):
bash# Check API
curl http://localhost:3000/api/tasks

# Post data
curl -X POST -H "Content-Type: application/json" -d '{"title":"Test"}' http://localhost:3000/api/tasks
New Way (with Playwright):
bash# Run debug session and see all console logs
npm run debug

# Test specific scenario
npm run test:create-task

# Use the debugger replacement
node -e "const BrowserDebugger = require('./scripts/debug-commands'); new BrowserDebugger().init().then(d => d.get('/api/tasks').then(() => d.close()))"
Quick Reference Card for Claude Code
bash# 🚀 Start debugging session (replaces curl completely)
npm run debug

# 🔍 See live console logs from the browser
npm run debug:watch

# 🧪 Test specific features
npm run test:browser create-task  # Test task creation
npm run test:browser navigate     # Test navigation
npm run test:browser api-test     # Test API calls

# 📊 View logs
cat logs/browser-console-*.log    # View saved logs
npm run logs:view                  # Tail logs in real-time

# 🧹 Clean up
npm run logs:clean                 # Remove old log files
Important Notes for Claude Code:

Always use npm run debug instead of curl when you need to:

Check if the app is working
Test API endpoints
Debug JavaScript errors
See what's happening in the browser


The browser debug script shows you:

All console.log() statements
JavaScript errors
Network failures
HTTP error responses
React component errors


You can modify the scripts to add specific test scenarios as needed
Log files are saved in the logs/ directory with timestamps
For API testing, the browser context is more accurate than curl because:

It includes cookies/session
It executes JavaScript
It shows CORS errors
It captures the full application state



Example Debugging Session:
bash# 1. Start the dev server in one terminal
npm run dev

# 2. In another terminal, run the debugger
npm run debug

# 3. You'll see output like:
# 🌐 Starting browser debug session for http://localhost:3000
# 📝 Logs will be saved to: logs/browser-console-1234567890.log
# [2024-01-15T10:30:00.000Z] LOG    | TaskForm mounted
# [2024-01-15T10:30:00.100Z] LOG    | Fetching tasks from API
# [2024-01-15T10:30:00.200Z] ERROR  | Cannot read property 'id' of undefined
#   at TaskList.render (bundle.js:1234:56)
# [2024-01-15T10:30:00.300Z] HTTP   | 404 /api/user/profile
This gives you MUCH more information than curl ever could, including the actual JavaScript errors and React component lifecycle logs that are crucial for debugging modern web applications.