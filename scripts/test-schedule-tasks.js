const { chromium } = require('playwright');

async function testScheduleTasks() {
    console.log('Starting browser test for schedule page tasks...');
    
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();
    
    try {
        // Navigate to schedule page
        console.log('Navigating to schedule page...');
        await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
        
        // Wait for page to load
        await page.waitForTimeout(3000);
        
        // Check for tasks list
        const tasksListExists = await page.locator('#tasks-list').isVisible();
        console.log('Tasks list element exists:', tasksListExists);
        
        // Get the tasks list content
        const tasksContent = await page.locator('#tasks-list').textContent();
        console.log('Tasks list content:', tasksContent.trim());
        
        // Check for specific task items
        const taskItems = await page.locator('.task-item').count();
        console.log('Number of task items found:', taskItems);
        
        // If we have task items, get their details
        if (taskItems > 0) {
            console.log('\nTask details:');
            for (let i = 0; i < taskItems; i++) {
                const taskTitle = await page.locator('.task-item .task-title').nth(i).textContent();
                const taskMeta = await page.locator('.task-item .task-meta').nth(i).textContent();
                console.log(`  ${i + 1}. ${taskTitle} - ${taskMeta}`);
            }
        } else {
            console.log('No task items found - checking for error or loading messages...');
            
            // Check for loading message
            const loadingMessage = await page.getByText('Loading tasks...').isVisible();
            console.log('Loading message visible:', loadingMessage);
            
            // Check for no tasks message
            const noTasksMessage = await page.getByText('No active tasks available').isVisible();
            console.log('No tasks message visible:', noTasksMessage);
            
            // Check for error message
            const errorMessage = await page.getByText('Failed to load tasks').isVisible();
            console.log('Error message visible:', errorMessage);
        }
        
        // Check console for any JavaScript errors
        const consoleMessages = [];
        page.on('console', msg => consoleMessages.push(msg.text()));
        
        // Wait a bit more to catch any console messages
        await page.waitForTimeout(2000);
        
        if (consoleMessages.length > 0) {
            console.log('\nConsole messages:');
            consoleMessages.forEach(msg => console.log('  ', msg));
        }
        
        // Take a screenshot
        await page.screenshot({ path: 'logs/schedule-tasks-test.png', fullPage: true });
        console.log('Screenshot saved to logs/schedule-tasks-test.png');
        
    } catch (error) {
        console.error('Error during test:', error);
    } finally {
        await browser.close();
    }
}

testScheduleTasks().catch(console.error);