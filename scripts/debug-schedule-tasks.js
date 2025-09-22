const { chromium } = require('playwright');

async function debugScheduleTasks() {
    console.log('Starting debug test for schedule page tasks...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    // Listen to console messages
    const consoleMessages = [];
    page.on('console', msg => {
        const message = `[${msg.type()}] ${msg.text()}`;
        console.log('Console:', message);
        consoleMessages.push(message);
    });
    
    // Listen to network responses
    page.on('response', response => {
        if (response.url().includes('/api/tasks')) {
            console.log(`API Response: ${response.status()} ${response.url()}`);
        }
    });
    
    try {
        console.log('Navigating to schedule page...');
        await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
        
        // Wait for page to fully load
        await page.waitForTimeout(5000);
        
        // Execute JavaScript to check the task loading
        const debugInfo = await page.evaluate(async () => {
            // Test the API call directly in the browser
            try {
                const response = await fetch('/api/tasks');
                const tasks = await response.json();
                
                return {
                    apiWorking: true,
                    taskCount: tasks.length,
                    tasks: tasks.map(t => ({
                        title: t.title,
                        status: t.status,
                        is_completed: t.is_completed,
                        is_snoozed: t.is_snoozed,
                        snoozed_until: t.snoozed_until
                    }))
                };
            } catch (error) {
                return {
                    apiWorking: false,
                    error: error.message
                };
            }
        });
        
        console.log('Debug info from browser:', JSON.stringify(debugInfo, null, 2));
        
        // Check if loadActiveTasks function exists and call it manually
        const manualLoad = await page.evaluate(() => {
            if (typeof loadActiveTasks === 'function') {
                loadActiveTasks();
                return { functionExists: true };
            } else {
                return { functionExists: false };
            }
        });
        
        console.log('Manual load result:', manualLoad);
        
        // Wait a bit more after manual load
        await page.waitForTimeout(3000);
        
        // Check final state
        const finalState = await page.evaluate(() => {
            const tasksList = document.getElementById('tasks-list');
            return {
                tasksListContent: tasksList ? tasksList.innerHTML : 'Element not found',
                taskItemCount: document.querySelectorAll('.task-item').length
            };
        });
        
        console.log('Final state:', finalState);
        
        // Take screenshot
        await page.screenshot({ path: 'logs/debug-schedule-tasks.png', fullPage: true });
        console.log('Debug screenshot saved');
        
    } catch (error) {
        console.error('Error during debug:', error);
    } finally {
        await browser.close();
    }
}

debugScheduleTasks().catch(console.error);