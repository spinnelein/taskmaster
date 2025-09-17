const { chromium } = require('playwright');

async function debugConsoleOutput() {
    console.log('Debug Console Output for Time Pool Task Display');
    console.log('=' + '='.repeat(50));
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000
    });
    
    try {
        const page = await browser.newPage();
        
        // Capture console messages
        const consoleMessages = [];
        page.on('console', msg => {
            const text = msg.text();
            consoleMessages.push(`[${msg.type().toUpperCase()}] ${text}`);
            console.log(`Browser Console: [${msg.type().toUpperCase()}] ${text}`);
        });
        
        // Navigate to schedule
        console.log('\n1. Loading schedule page...');
        await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
        
        // Wait for FullCalendar
        console.log('2. Waiting for FullCalendar to initialize...');
        await page.waitForTimeout(3000); // Give time for all loading
        
        // Check current time pool events and their properties
        const timePoolInfo = await page.evaluate(() => {
            const results = [];
            
            // Look for all fc-event elements
            const events = document.querySelectorAll('.fc-event');
            console.log(`Found ${events.length} total events on calendar`);
            
            events.forEach((event, index) => {
                const title = event.querySelector('.fc-event-title')?.textContent || '';
                const id = event.id || '';
                const classList = event.className || '';
                
                // Check if it's a time pool
                if (title.includes('Time Pool') || id.includes('timepool')) {
                    console.log(`Time Pool ${index}: ID="${id}", Title="${title}"`);
                    
                    // Check for extendedProps in the DOM
                    const fcEvent = event.fcEvent;
                    if (fcEvent) {
                        console.log(`  Has fcEvent object:`, !!fcEvent);
                        console.log(`  ExtendedProps:`, fcEvent.extendedProps);
                        if (fcEvent.extendedProps) {
                            console.log(`  isTimePool:`, fcEvent.extendedProps.isTimePool);
                            console.log(`  taskList:`, fcEvent.extendedProps.taskList);
                        }
                    } else {
                        console.log(`  No fcEvent object found`);
                    }
                    
                    results.push({
                        index,
                        id,
                        title,
                        classList,
                        hasFcEvent: !!fcEvent
                    });
                }
            });
            
            return results;
        });
        
        console.log(`\n3. Found ${timePoolInfo.length} time pool events:`);
        timePoolInfo.forEach(pool => {
            console.log(`   ${pool.index}: ${pool.title} (ID: ${pool.id})`);
            console.log(`      Has fcEvent: ${pool.hasFcEvent}`);
        });
        
        // Check if eventDidMount was called at all
        const didMountCalled = await page.evaluate(() => {
            return window.eventDidMountCalled || false;
        });
        console.log(`\n4. eventDidMount callback called: ${didMountCalled}`);
        
        // Wait and take screenshot
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'logs/debug-time-pools.png' });
        console.log('\n5. Debug screenshot saved to logs/debug-time-pools.png');
        
        console.log('\n6. Console Messages Summary:');
        consoleMessages.forEach(msg => console.log(`   ${msg}`));
        
        // Keep browser open for inspection
        console.log('\nKeeping browser open for 10 seconds...');
        await page.waitForTimeout(10000);
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

debugConsoleOutput().catch(console.error);