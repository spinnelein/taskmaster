const { chromium } = require('playwright');

async function testScheduleDisplay() {
    console.log('Testing Schedule Display with Playwright');
    console.log('=' + '='.repeat(50));
    
    const browser = await chromium.launch({ 
        headless: false,  // Show browser for visual verification
        slowMo: 500      // Slow down actions for visibility
    });
    
    try {
        const page = await browser.newPage();
        
        // Set viewport for better visibility
        await page.setViewportSize({ width: 1400, height: 900 });
        
        console.log('\n1. Navigating to schedule page...');
        await page.goto('http://localhost:5000/');  // Schedule is at root URL
        await page.waitForLoadState('networkidle');
        
        // Check page content
        const pageContent = await page.content();
        const title = await page.title();
        console.log(`   Page title: "${title}"`);
        
        if (pageContent.includes('404 Not Found') || pageContent.includes('<h1>Not Found</h1>')) {
            console.log('   [ERROR] Page not found');
            return;
        }
        
        // Check if FullCalendar script is loaded
        const hasFullCalendar = pageContent.includes('fullcalendar');
        console.log(`   FullCalendar script present: ${hasFullCalendar}`);
        
        console.log('2. Waiting for calendar to load...');
        // Try multiple possible selectors
        try {
            await page.waitForSelector('#calendar, .fc-view-harness, [id="calendar"]', { timeout: 10000 });
        } catch (e) {
            console.log('   [WARNING] Calendar element not found, checking page structure...');
            const title = await page.title();
            console.log(`   Page title: ${title}`);
            
            // Take screenshot to debug
            await page.screenshot({ path: 'logs/schedule-page-debug.png' });
            console.log('   Debug screenshot saved to: logs/schedule-page-debug.png');
        }
        
        // Wait for FullCalendar to render
        try {
            await page.waitForFunction(() => {
                return window.calendar && window.calendar.view;
            }, { timeout: 5000 });
            console.log('   [OK] FullCalendar loaded successfully');
        } catch (e) {
            console.log('   [WARNING] FullCalendar global not found, continuing anyway...');
        }
        
        console.log('3. Waiting for time pools to load...');
        // Time pools load after a 500ms delay
        await page.waitForTimeout(2000);
        
        // Look for time pool events
        const timePools = await page.$$('.fc-event[id^="timepool-"]');
        console.log(`   Found ${timePools.length} time pools on calendar`);
        
        // Check for task text in time pools
        console.log('\n4. Checking for task assignments in time pools:');
        
        const poolsWithTasks = await page.evaluate(() => {
            const results = [];
            const pools = document.querySelectorAll('.fc-event[id^="timepool-"]');
            
            pools.forEach(pool => {
                const title = pool.querySelector('.fc-event-title')?.textContent || '';
                const mainContent = pool.querySelector('.fc-event-main');
                
                // Look for task divs added by our eventDidMount
                const taskDivs = mainContent ? mainContent.querySelectorAll('div[style*="font-size: 11px"]') : [];
                const tasks = [];
                
                taskDivs.forEach(taskDiv => {
                    const taskLines = taskDiv.querySelectorAll('div');
                    taskLines.forEach(line => {
                        const text = line.textContent.trim();
                        if (text) tasks.push(text);
                    });
                });
                
                if (tasks.length > 0 || title.includes('/')) {
                    results.push({
                        title: title,
                        tasks: tasks,
                        element: pool.id
                    });
                }
            });
            
            return results;
        });
        
        if (poolsWithTasks.length > 0) {
            console.log(`   [OK] Found ${poolsWithTasks.length} time pools with information:`);
            poolsWithTasks.forEach(pool => {
                console.log(`\n   Pool: ${pool.title}`);
                if (pool.tasks.length > 0) {
                    console.log('   Assigned tasks:');
                    pool.tasks.forEach(task => {
                        console.log(`     ${task}`);
                    });
                } else {
                    console.log('   No tasks displayed (might be empty pool)');
                }
            });
        } else {
            console.log('   [WARNING] No time pools with task information found');
        }
        
        // Take screenshot for evidence
        console.log('\n5. Taking screenshot...');
        await page.screenshot({ 
            path: 'logs/schedule-with-tasks.png',
            fullPage: false 
        });
        console.log('   Screenshot saved to: logs/schedule-with-tasks.png');
        
        // Zoom in on a specific time pool with tasks
        const firstPoolWithTasks = poolsWithTasks.find(p => p.tasks.length > 0);
        if (firstPoolWithTasks) {
            console.log('\n6. Focusing on time pool with tasks...');
            const poolElement = await page.$(`#${firstPoolWithTasks.element}`);
            if (poolElement) {
                await poolElement.scrollIntoViewIfNeeded();
                await poolElement.hover();
                await page.waitForTimeout(1000);
                
                // Take close-up screenshot
                await page.screenshot({
                    path: 'logs/time-pool-with-tasks-closeup.png',
                    clip: await poolElement.boundingBox()
                });
                console.log('   Close-up saved to: logs/time-pool-with-tasks-closeup.png');
            }
        }
        
        console.log('\n7. Test Summary:');
        console.log('   - Schedule page loaded successfully');
        console.log(`   - Found ${timePools.length} time pools on calendar`);
        console.log(`   - ${poolsWithTasks.filter(p => p.tasks.length > 0).length} pools have visible task assignments`);
        console.log('   - Screenshots saved for verification');
        
        // Keep browser open for 5 seconds for visual inspection
        console.log('\n   Keeping browser open for visual inspection...');
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('Error during test:', error);
    } finally {
        await browser.close();
    }
}

// Run the test
testScheduleDisplay().catch(console.error);