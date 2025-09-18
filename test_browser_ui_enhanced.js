// Test browser UI with enhanced task queue endpoints
const { chromium } = require('playwright');

async function testTaskQueueUI() {
    console.log('Testing Enhanced Task Queue UI...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        // Navigate to tasks page
        console.log('Navigating to tasks page...');
        await page.goto('http://localhost:5000/tasks');
        await page.waitForLoadState('networkidle');
        
        // Take screenshot of initial state
        await page.screenshot({ path: 'logs/enhanced-tasks-initial.png' });
        console.log('✓ Tasks page loaded');
        
        // Check if we can load enhanced queue via console
        console.log('Testing enhanced queue API calls...');
        
        const enhancedQueueData = await page.evaluate(async () => {
            try {
                // Test regular enhanced queue
                const response = await fetch('/api/task-queue/enhanced?limit=10');
                const data = await response.json();
                console.log('Enhanced queue response:', data);
                
                return {
                    success: true,
                    taskCount: data.enhanced_task_queue ? data.enhanced_task_queue.length : 0,
                    scoringMethod: data.scoring_method,
                    topTask: data.enhanced_task_queue && data.enhanced_task_queue[0] ? {
                        title: data.enhanced_task_queue[0].title,
                        score: data.enhanced_task_queue[0].enhanced_priority_score
                    } : null
                };
            } catch (error) {
                console.error('Enhanced queue error:', error);
                return { success: false, error: error.message };
            }
        });
        
        console.log('Enhanced Queue Results:', enhancedQueueData);
        
        // Test available enhanced queue
        const availableQueueData = await page.evaluate(async () => {
            try {
                const response = await fetch('/api/task-queue/enhanced/available?limit=10');
                const data = await response.json();
                console.log('Available enhanced queue response:', data);
                
                return {
                    success: true,
                    taskCount: data.enhanced_available_tasks ? data.enhanced_available_tasks.length : 0,
                    scoringMethod: data.scoring_method
                };
            } catch (error) {
                console.error('Available enhanced queue error:', error);
                return { success: false, error: error.message };
            }
        });
        
        console.log('Available Enhanced Queue Results:', availableQueueData);
        
        // Test task context analysis
        if (enhancedQueueData.success && enhancedQueueData.topTask) {
            const contextData = await page.evaluate(async (taskTitle) => {
                try {
                    // Find task ID by title (simplified)
                    const allTasksResponse = await fetch('/api/task-queue/all?limit=50');
                    const allTasksData = await allTasksResponse.json();
                    
                    const task = allTasksData.task_queue.find(t => t.title === taskTitle);
                    if (!task) {
                        return { success: false, error: 'Task not found' };
                    }
                    
                    const contextResponse = await fetch(`/api/task-queue/enhanced/context/${task.id}`);
                    const contextData = await contextResponse.json();
                    console.log('Task context response:', contextData);
                    
                    return {
                        success: true,
                        hasAnalysis: contextData.has_analysis,
                        totalScore: contextData.task_context?.priority_analysis?.total_score,
                        topFactors: contextData.task_context?.priority_analysis?.top_factors
                    };
                } catch (error) {
                    console.error('Context analysis error:', error);
                    return { success: false, error: error.message };
                }
            }, enhancedQueueData.topTask.title);
            
            console.log('Context Analysis Results:', contextData);
        }
        
        // Try to inject enhanced queue into page
        console.log('Injecting enhanced queue display...');
        
        await page.evaluate(async () => {
            try {
                // Create enhanced queue display
                const container = document.createElement('div');
                container.id = 'enhanced-queue-display';
                container.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    width: 400px;
                    max-height: 500px;
                    background: white;
                    border: 2px solid #007bff;
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    overflow-y: auto;
                    z-index: 1000;
                    font-family: Arial, sans-serif;
                `;
                
                // Add title
                const title = document.createElement('h3');
                title.textContent = 'Enhanced Task Queue';
                title.style.cssText = 'margin: 0 0 10px 0; color: #007bff;';
                container.appendChild(title);
                
                // Fetch and display enhanced queue
                const response = await fetch('/api/task-queue/enhanced?limit=8');
                const data = await response.json();
                
                if (data.enhanced_task_queue) {
                    const list = document.createElement('ul');
                    list.style.cssText = 'margin: 0; padding: 0; list-style: none;';
                    
                    data.enhanced_task_queue.forEach((task, index) => {
                        const item = document.createElement('li');
                        item.style.cssText = `
                            padding: 8px;
                            margin: 5px 0;
                            border-left: 4px solid ${index === 0 ? '#dc3545' : index === 1 ? '#fd7e14' : '#28a745'};
                            background: #f8f9fa;
                            font-size: 14px;
                        `;
                        
                        const score = task.enhanced_priority_score || 0;
                        const title = task.title || 'Unknown Task';
                        
                        item.innerHTML = `
                            <strong>${title.substring(0, 30)}${title.length > 30 ? '...' : ''}</strong><br>
                            <small>Score: ${score.toFixed(1)} | Due: ${task.due_date || 'None'}</small>
                        `;
                        
                        list.appendChild(item);
                    });
                    
                    container.appendChild(list);
                    
                    // Add info
                    const info = document.createElement('div');
                    info.style.cssText = 'margin-top: 10px; font-size: 12px; color: #666;';
                    info.textContent = `Total: ${data.count} tasks | Scoring: ${data.scoring_method}`;
                    container.appendChild(info);
                }
                
                document.body.appendChild(container);
                
                return { success: true, message: 'Enhanced queue display added' };
            } catch (error) {
                console.error('Display injection error:', error);
                return { success: false, error: error.message };
            }
        });
        
        // Take screenshot with enhanced display
        await page.waitForTimeout(1000);
        await page.screenshot({ path: 'logs/enhanced-tasks-with-display.png' });
        console.log('✓ Enhanced queue display injected');
        
        // Test comparison functionality
        console.log('Testing task comparison...');
        
        const comparisonData = await page.evaluate(async () => {
            try {
                // Get first 3 task IDs
                const allTasksResponse = await fetch('/api/task-queue/all?limit=3');
                const allTasksData = await allTasksResponse.json();
                
                const taskIds = allTasksData.task_queue.slice(0, 3).map(t => t.id);
                
                const compareResponse = await fetch('/api/task-queue/enhanced/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_ids: taskIds })
                });
                
                const compareData = await compareResponse.json();
                console.log('Comparison response:', compareData);
                
                return {
                    success: true,
                    comparisons: compareData.task_comparisons || []
                };
            } catch (error) {
                console.error('Comparison test error:', error);
                return { success: false, error: error.message };
            }
        });
        
        console.log('Comparison Results:', comparisonData);
        
        // Wait a bit to see the results
        await page.waitForTimeout(3000);
        
        // Final screenshot
        await page.screenshot({ path: 'logs/enhanced-tasks-final.png' });
        
        return {
            enhancedQueue: enhancedQueueData,
            availableQueue: availableQueueData,
            comparison: comparisonData
        };
        
    } catch (error) {
        console.error('Browser test error:', error);
        await page.screenshot({ path: 'logs/enhanced-tasks-error.png' });
        return { error: error.message };
    } finally {
        await browser.close();
    }
}

async function testSchedulePageIntegration() {
    console.log('Testing Schedule Page Integration...');
    
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    try {
        // Navigate to schedule page
        console.log('Navigating to schedule page...');
        await page.goto('http://localhost:5000/schedule');
        await page.waitForLoadState('networkidle');
        
        // Take screenshot
        await page.screenshot({ path: 'logs/enhanced-schedule-initial.png' });
        console.log('✓ Schedule page loaded');
        
        // Test enhanced queue integration on schedule page
        const scheduleData = await page.evaluate(async () => {
            try {
                // Test if enhanced queue can be loaded on schedule page
                const response = await fetch('/api/task-queue/enhanced?limit=5');
                const data = await response.json();
                
                // Try to add enhanced queue info to schedule page
                const sidebar = document.querySelector('.sidebar') || document.querySelector('#sidebar');
                if (sidebar) {
                    const enhancedSection = document.createElement('div');
                    enhancedSection.style.cssText = `
                        margin: 15px 0;
                        padding: 10px;
                        background: #e7f3ff;
                        border-radius: 5px;
                        border: 1px solid #007bff;
                    `;
                    
                    enhancedSection.innerHTML = `
                        <h4 style="margin: 0 0 8px 0; color: #007bff;">Enhanced Queue</h4>
                        <div style="font-size: 12px;">
                            ${data.enhanced_task_queue ? data.enhanced_task_queue.slice(0, 3).map(task => 
                                `<div style="margin: 3px 0;">${task.title}: ${(task.enhanced_priority_score || 0).toFixed(0)}pts</div>`
                            ).join('') : 'No tasks'}
                        </div>
                    `;
                    
                    sidebar.appendChild(enhancedSection);
                    
                    return { success: true, taskCount: data.enhanced_task_queue?.length || 0 };
                }
                
                return { success: false, error: 'Sidebar not found' };
            } catch (error) {
                console.error('Schedule integration error:', error);
                return { success: false, error: error.message };
            }
        });
        
        console.log('Schedule Integration Results:', scheduleData);
        
        // Take final screenshot
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'logs/enhanced-schedule-with-queue.png' });
        
        return scheduleData;
        
    } catch (error) {
        console.error('Schedule test error:', error);
        await page.screenshot({ path: 'logs/enhanced-schedule-error.png' });
        return { error: error.message };
    } finally {
        await browser.close();
    }
}

async function main() {
    console.log('Enhanced Task Queue Browser UI Testing');
    console.log('=====================================');
    
    try {
        // Test 1: Task Queue UI
        console.log('\n1. Testing Task Queue UI...');
        const taskResults = await testTaskQueueUI();
        
        // Test 2: Schedule Page Integration
        console.log('\n2. Testing Schedule Page Integration...');
        const scheduleResults = await testSchedulePageIntegration();
        
        // Summary
        console.log('\n=====================================');
        console.log('BROWSER UI TEST SUMMARY');
        console.log('=====================================');
        
        console.log('\nTask Queue UI Tests:');
        if (taskResults.enhancedQueue?.success) {
            console.log(`✓ Enhanced queue: ${taskResults.enhancedQueue.taskCount} tasks`);
            if (taskResults.enhancedQueue.topTask) {
                console.log(`  Top task: "${taskResults.enhancedQueue.topTask.title}" (${taskResults.enhancedQueue.topTask.score.toFixed(1)} pts)`);
            }
        } else {
            console.log('✗ Enhanced queue failed');
        }
        
        if (taskResults.availableQueue?.success) {
            console.log(`✓ Available queue: ${taskResults.availableQueue.taskCount} tasks`);
        } else {
            console.log('✗ Available queue failed');
        }
        
        if (taskResults.comparison?.success) {
            console.log(`✓ Task comparison: ${taskResults.comparison.comparisons.length} tasks compared`);
        } else {
            console.log('✗ Task comparison failed');
        }
        
        console.log('\nSchedule Page Integration:');
        if (scheduleResults.success) {
            console.log(`✓ Schedule integration: ${scheduleResults.taskCount} tasks displayed`);
        } else {
            console.log('✗ Schedule integration failed');
        }
        
        console.log('\nScreenshots saved in logs/ directory:');
        console.log('- enhanced-tasks-initial.png');
        console.log('- enhanced-tasks-with-display.png');
        console.log('- enhanced-tasks-final.png');
        console.log('- enhanced-schedule-initial.png');
        console.log('- enhanced-schedule-with-queue.png');
        
        const overallSuccess = (
            taskResults.enhancedQueue?.success &&
            taskResults.availableQueue?.success &&
            taskResults.comparison?.success &&
            scheduleResults.success
        );
        
        if (overallSuccess) {
            console.log('\n✓ All browser UI tests passed!');
        } else {
            console.log('\n⚠ Some browser UI tests had issues (see details above)');
        }
        
    } catch (error) {
        console.error('Browser testing failed:', error);
    }
}

main().catch(console.error);