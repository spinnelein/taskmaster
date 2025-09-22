// Test Task Completion Button in Flask App
// NO EMOJIS
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Ensure logs directory exists
const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const timestamp = Date.now();
const logFile = path.join(logsDir, `task-completion-test-${timestamp}.log`);

async function testTaskCompletion() {
  console.log('Starting task completion test...');
  console.log(`Logs will be saved to: ${logFile}`);
  
  const browser = await chromium.launch({ 
    headless: false, // Run with visible browser for better debugging
    slowMo: 100 // Slow down actions to observe them
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const logs = [];
  const networkRequests = [];
  
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
    logs.push(logEntry);
    fs.appendFileSync(logFile, logEntry + '\n');
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    const timestamp = new Date().toISOString();
    const errorEntry = `[${timestamp}] PAGE ERROR | ${error.message}\n${error.stack || ''}`;
    console.error(errorEntry);
    logs.push(errorEntry);
    fs.appendFileSync(logFile, errorEntry + '\n');
  });
  
  // Capture network activity
  page.on('request', request => {
    const url = request.url();
    if (url.includes('/api/') || url.includes('/tasks')) {
      const entry = {
        timestamp: new Date().toISOString(),
        method: request.method(),
        url: url,
        headers: request.headers(),
        postData: request.postData()
      };
      networkRequests.push(entry);
      console.log(`[REQUEST] ${entry.method} ${entry.url}`);
      if (entry.postData) {
        console.log(`  Body: ${entry.postData}`);
      }
    }
  });
  
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/') || url.includes('/tasks')) {
      const entry = {
        timestamp: new Date().toISOString(),
        url: url,
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers()
      };
      
      try {
        const body = await response.text();
        entry.body = body;
        console.log(`[RESPONSE] ${entry.status} ${entry.url}`);
        console.log(`  Body: ${body}`);
      } catch (e) {
        console.log(`[RESPONSE] ${entry.status} ${entry.url} (couldn't read body)`);
      }
      
      networkRequests.push(entry);
    }
  });
  
  try {
    // Navigate to tasks page
    console.log('\n=== NAVIGATING TO TASKS PAGE ===');
    await page.goto('http://localhost:5000/tasks', { waitUntil: 'networkidle' });
    
    // Take initial screenshot
    await page.screenshot({ path: path.join(logsDir, `tasks-initial-${timestamp}.png`) });
    
    // Wait for tasks to load
    await page.waitForTimeout(2000);
    
    // Find task containers
    console.log('\n=== LOOKING FOR TASKS ===');
    const taskContainers = await page.$$('.task-item, .bg-white.rounded-lg, [data-task-id]');
    console.log(`Found ${taskContainers.length} task containers`);
    
    // Look for a task with "YOLO" or any active task
    let targetTask = null;
    let taskTitle = '';
    let taskId = '';
    
    for (const container of taskContainers) {
      const titleText = await container.$eval('h3, .font-semibold, .task-title', el => el.textContent).catch(() => null);
      const status = await container.$eval('.badge, .text-sm, [class*="status"]', el => el.textContent).catch(() => null);
      
      console.log(`Task found: "${titleText}" - Status: "${status}"`);
      
      if (titleText && (titleText.includes('YOLO') || status?.toLowerCase().includes('active'))) {
        targetTask = container;
        taskTitle = titleText;
        // Try to get task ID from data attribute or button
        taskId = await container.getAttribute('data-task-id').catch(() => null) ||
                 await container.$eval('button[onclick*="completeTask"]', el => {
                   const onclick = el.getAttribute('onclick');
                   const match = onclick.match(/completeTask\('([^']+)'\)/);
                   return match ? match[1] : null;
                 }).catch(() => null);
        break;
      }
    }
    
    if (!targetTask) {
      console.log('No suitable task found, creating a test task...');
      // This would require implementing task creation
      throw new Error('No active tasks found to test');
    }
    
    console.log(`\n=== TESTING TASK: "${taskTitle}" (ID: ${taskId}) ===`);
    
    // Find the complete button
    const completeButton = await targetTask.$('button:has-text("Complete"), button:has-text("Mark Complete"), button[onclick*="completeTask"]');
    
    if (!completeButton) {
      throw new Error('Complete button not found for the task');
    }
    
    // Check button properties
    const buttonText = await completeButton.textContent();
    const buttonOnclick = await completeButton.getAttribute('onclick');
    console.log(`Button text: "${buttonText}"`);
    console.log(`Button onclick: "${buttonOnclick}"`);
    
    // Take screenshot before clicking
    await page.screenshot({ path: path.join(logsDir, `before-complete-${timestamp}.png`) });
    
    // Clear network requests before the click
    networkRequests.length = 0;
    
    console.log('\n=== CLICKING COMPLETE BUTTON ===');
    await completeButton.click();
    
    // Wait for any network activity
    await page.waitForTimeout(3000);
    
    // Take screenshot after clicking
    await page.screenshot({ path: path.join(logsDir, `after-complete-${timestamp}.png`) });
    
    // Check if task is still visible and its new status
    const taskStillVisible = await targetTask.isVisible().catch(() => false);
    console.log(`Task still visible: ${taskStillVisible}`);
    
    if (taskStillVisible) {
      const newStatus = await targetTask.$eval('.badge, .text-sm, [class*="status"]', el => el.textContent).catch(() => 'unknown');
      console.log(`Task new status: "${newStatus}"`);
    }
    
    // Log all network activity
    console.log('\n=== NETWORK ACTIVITY SUMMARY ===');
    for (const req of networkRequests) {
      if (req.method) {
        console.log(`${req.method} ${req.url}`);
        if (req.postData) console.log(`  Request Body: ${req.postData}`);
        if (req.body) console.log(`  Response: ${req.status} - ${req.body}`);
      }
    }
    
    // Check for any error messages on the page
    const errorMessages = await page.$$eval('.error, .alert-danger, [class*="error"]', elements => 
      elements.map(el => el.textContent)
    ).catch(() => []);
    
    if (errorMessages.length > 0) {
      console.log('\n=== ERROR MESSAGES ON PAGE ===');
      errorMessages.forEach(msg => console.log(`Error: ${msg}`));
    }
    
  } catch (error) {
    console.error('\n=== TEST ERROR ===');
    console.error(error.message);
    console.error(error.stack);
    
    // Take error screenshot
    await page.screenshot({ path: path.join(logsDir, `error-${timestamp}.png`) }).catch(() => {});
  }
  
  // Keep browser open for 5 seconds to observe
  console.log('\n=== KEEPING BROWSER OPEN FOR OBSERVATION ===');
  await page.waitForTimeout(5000);
  
  await browser.close();
  
  // Generate summary report
  const report = `
TASK COMPLETION TEST REPORT
===========================
Timestamp: ${new Date().toISOString()}
Log File: ${logFile}

Console Errors: ${logs.filter(log => log.includes('ERROR')).length}
Network Requests: ${networkRequests.filter(r => r.method).length}
API Errors: ${networkRequests.filter(r => r.status && r.status >= 400).length}

Screenshots:
- Initial: tasks-initial-${timestamp}.png
- Before Click: before-complete-${timestamp}.png
- After Click: after-complete-${timestamp}.png

Full logs available in: ${logFile}
`;
  
  console.log(report);
  fs.appendFileSync(logFile, report);
  
  return {
    success: networkRequests.some(r => r.status && r.status < 400),
    errors: logs.filter(log => log.includes('ERROR')),
    apiCalls: networkRequests.filter(r => r.method)
  };
}

// Run the test
testTaskCompletion().catch(console.error);