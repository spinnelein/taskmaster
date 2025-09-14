// UI Demo testing script with Playwright
// NO EMOJIS
const { debugBrowser } = require('./browser-debug');

async function testUIDemo() {
  console.log('Starting UI Demo test...');
  
  const actions = [
    {
      type: 'screenshot',
      path: 'logs/ui-demo-initial.png',
      description: 'Take initial screenshot'
    },
    {
      type: 'wait',
      duration: 2000,
      description: 'Wait for page to fully load'
    },
    {
      type: 'click',
      selector: 'button:has-text("Create New Task")',
      description: 'Click Create New Task button'
    },
    {
      type: 'wait',
      duration: 1000,
      description: 'Wait for modal to open'
    },
    {
      type: 'screenshot',
      path: 'logs/task-modal-open.png',
      description: 'Screenshot of task modal'
    },
    {
      type: 'fill',
      selector: 'input[name="title"]',
      value: 'Test Task from Playwright',
      description: 'Fill in task title'
    },
    {
      type: 'screenshot',
      path: 'logs/task-form-filled.png',
      description: 'Screenshot with form filled'
    },
    {
      type: 'click',
      selector: 'button:has-text("Cancel")',
      description: 'Click Cancel to close modal'
    },
    {
      type: 'wait',
      duration: 1000,
      description: 'Wait for modal to close'
    },
    {
      type: 'click',
      selector: 'button:has-text("Create New Event")',
      description: 'Click Create New Event button'
    },
    {
      type: 'wait',
      duration: 1000,
      description: 'Wait for event modal to open'
    },
    {
      type: 'screenshot',
      path: 'logs/event-modal-open.png',
      description: 'Screenshot of event modal'
    },
    {
      type: 'fill',
      selector: 'input[name="title"]',
      value: 'Test Event from Playwright',
      description: 'Fill in event title'
    },
    {
      type: 'click',
      selector: 'button:has-text("Cancel")',
      description: 'Click Cancel to close event modal'
    }
  ];

  try {
    const logFile = await debugBrowser('http://localhost:5175/ui-demo', {
      headless: process.argv.includes('--headless'),
      timeout: 15000,
      actions: actions
    });
    
    console.log('\nUI Demo test completed successfully!');
    console.log(`Check the log file: ${logFile}`);
    console.log('Screenshots saved in logs/ directory');
    
  } catch (error) {
    console.error('UI Demo test failed:', error);
  }
}

// Run the test
if (require.main === module) {
  testUIDemo().catch(console.error);
}

module.exports = { testUIDemo };