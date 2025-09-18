const { chromium } = require('playwright');

async function debugTaskVisibility() {
    console.log('Debug Task Visibility in Time Pool Blocks');
    console.log('=' + '='.repeat(50));
    
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000
    });
    
    try {
        const page = await browser.newPage();
        
        // Capture console messages
        page.on('console', msg => {
            console.log(`Browser Console: [${msg.type().toUpperCase()}] ${msg.text()}`);
        });
        
        // Navigate to schedule
        console.log('\n1. Loading schedule page...');
        await page.goto('http://localhost:5000/', { waitUntil: 'networkidle' });
        
        // Wait for FullCalendar and time pools
        await page.waitForTimeout(3000);
        
        // Inspect the DOM structure of time pools with tasks
        console.log('\n2. Inspecting DOM structure of time pools...');
        const timePoolStructure = await page.evaluate(() => {
            const results = [];
            const pools = document.querySelectorAll('.fc-event[id^="timepool-"], .fc-event');
            
            pools.forEach((pool, index) => {
                const title = pool.querySelector('.fc-event-title')?.textContent || '';
                
                // Only look at time pools
                if (title.includes('Time Pool')) {
                    const id = pool.id || 'no-id';
                    const poolInfo = {
                        index,
                        id,
                        title,
                        outerHTML: pool.outerHTML.substring(0, 500) + '...',
                        children: []
                    };
                    
                    // Look for the main content area
                    const mainContent = pool.querySelector('.fc-event-main');
                    if (mainContent) {
                        poolInfo.hasMainContent = true;
                        poolInfo.mainContentHTML = mainContent.innerHTML;
                        
                        // Look for our added task divs
                        const taskDivs = mainContent.querySelectorAll('div[style*="font-size: 10px"], div[style*="background: rgba(255, 255, 255, 0.8)"]');
                        poolInfo.taskDivCount = taskDivs.length;
                        
                        taskDivs.forEach((taskDiv, tdIndex) => {
                            poolInfo.children.push({
                                index: tdIndex,
                                innerHTML: taskDiv.innerHTML,
                                textContent: taskDiv.textContent,
                                style: taskDiv.style.cssText,
                                visible: getComputedStyle(taskDiv).display !== 'none' && 
                                        getComputedStyle(taskDiv).visibility !== 'hidden' &&
                                        getComputedStyle(taskDiv).opacity !== '0',
                                computedStyle: {
                                    display: getComputedStyle(taskDiv).display,
                                    visibility: getComputedStyle(taskDiv).visibility,
                                    opacity: getComputedStyle(taskDiv).opacity,
                                    height: getComputedStyle(taskDiv).height,
                                    overflow: getComputedStyle(taskDiv).overflow
                                }
                            });
                        });
                    } else {
                        poolInfo.hasMainContent = false;
                    }
                    
                    results.push(poolInfo);
                }
            });
            
            return results;
        });
        
        console.log(`\n3. Found ${timePoolStructure.length} time pool events:`);
        timePoolStructure.forEach(pool => {
            console.log(`\n   Pool ${pool.index}: ${pool.title}`);
            console.log(`      ID: ${pool.id}`);
            console.log(`      Has main content: ${pool.hasMainContent}`);
            if (pool.hasMainContent) {
                console.log(`      Main content HTML: ${pool.mainContentHTML}`);
                console.log(`      Task div count: ${pool.taskDivCount}`);
                
                pool.children.forEach(child => {
                    console.log(`\n      Task Div ${child.index}:`);
                    console.log(`         Text: "${child.textContent}"`);
                    console.log(`         Visible: ${child.visible}`);
                    console.log(`         Style: ${child.style}`);
                    console.log(`         Computed display: ${child.computedStyle.display}`);
                    console.log(`         Computed visibility: ${child.computedStyle.visibility}`);
                    console.log(`         Computed opacity: ${child.computedStyle.opacity}`);
                    console.log(`         Computed height: ${child.computedStyle.height}`);
                });
            }
        });
        
        // Take screenshot
        await page.screenshot({ path: 'logs/task-visibility-debug.png' });
        console.log('\n4. Debug screenshot saved to logs/task-visibility-debug.png');
        
        // Keep browser open for inspection
        console.log('\nKeeping browser open for 15 seconds...');
        await page.waitForTimeout(15000);
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

debugTaskVisibility().catch(console.error);