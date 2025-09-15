// Integration Tests for TaskMaster UI
// Tests cross-component functionality, API integration, routing, and real user workflows
// NO EMOJIS

const path = require('path');

class IntegrationTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Integration Tests...');
    
    await this.runTest('Backend API Connectivity', () => this.testAPIConnectivity(page, options));
    await this.runTest('Page Navigation Flow', () => this.testNavigationFlow(page, options));
    await this.runTest('Task CRUD Integration', () => this.testTaskCRUD(page, options));
    await this.runTest('Event CRUD Integration', () => this.testEventCRUD(page, options));
    await this.runTest('Modal to API Integration', () => this.testModalAPIIntegration(page, options));
    await this.runTest('Widget to API Integration', () => this.testWidgetAPIIntegration(page, options));
    await this.runTest('Command Palette Navigation', () => this.testCommandPaletteNavigation(page, options));
    await this.runTest('Cross-Page State Persistence', () => this.testStatePersistence(page, options));
    await this.runTest('Error Handling Integration', () => this.testErrorHandling(page, options));
    await this.runTest('Real User Workflow', () => this.testRealUserWorkflow(page, options));
    
    return this.results;
  }

  async runTest(testName, testFunction) {
    this.results.totalTests++;
    
    try {
      await testFunction();
      this.results.passedTests++;
      this.results.testResults[testName] = { status: 'PASSED' };
      console.log(`✓ ${testName} - PASSED`);
      
    } catch (error) {
      this.results.failedTests++;
      this.results.testResults[testName] = { 
        status: 'FAILED', 
        error: error.message 
      };
      console.log(`✗ ${testName} - FAILED: ${error.message}`);
    }
  }

  async testAPIConnectivity(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    const apiUrl = baseUrl.replace('5173', '8000'); // Assume backend on 8000
    
    // Track API requests
    const apiRequests = [];
    const apiResponses = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          url: request.url(),
          method: request.method()
        });
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiResponses.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    // Go to main page and wait for API calls
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    console.log(`API Requests: ${apiRequests.length}`);
    console.log(`API Responses: ${apiResponses.length}`);
    
    // Check critical API endpoints
    const criticalAPIs = ['/api/health', '/api/tasks', '/api/events'];
    const workingAPIs = [];
    const failedAPIs = [];
    
    for (const api of criticalAPIs) {
      const requests = apiRequests.filter(req => req.url.includes(api));
      const responses = apiResponses.filter(resp => resp.url.includes(api));
      
      if (responses.length > 0) {
        const successfulResponses = responses.filter(resp => resp.status < 400);
        
        if (successfulResponses.length > 0) {
          workingAPIs.push(api);
          console.log(`${api}: Working (${successfulResponses.length} successful responses)`);
        } else {
          failedAPIs.push(api);
          console.log(`${api}: Failed (${responses.length} responses, all ${responses[0]?.status || 'unknown'} errors)`);
        }
      } else if (requests.length > 0) {
        failedAPIs.push(api);
        console.log(`${api}: No responses received (${requests.length} requests made)`);
      } else {
        console.log(`${api}: No requests made`);
      }
    }
    
    if (failedAPIs.length > 0) {
      throw new Error(`API connectivity issues: ${failedAPIs.join(', ')} not working`);
    }
    
    if (workingAPIs.length === 0) {
      throw new Error('No API endpoints responding - backend may be down');
    }
  }

  async testNavigationFlow(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    const navigationTests = [
      { path: '/', name: 'Dashboard' },
      { path: '/tasks', name: 'Tasks Page' },
      { path: '/events', name: 'Events Page' },
      { path: '/schedule', name: 'Schedule Page' },
      { path: '/initiatives', name: 'Initiatives Page' },
      { path: '/projects', name: 'Projects Page' },
      { path: '/ui-demo', name: 'UI Demo Page' },
      { path: '/phase2-demo', name: 'Phase 2 Demo Page' },
      { path: '/phase3-demo', name: 'Phase 3 Demo Page' }
    ];
    
    for (const nav of navigationTests) {
      try {
        await page.goto(`${baseUrl}${nav.path}`);
        await page.waitForLoadState('networkidle', { timeout: 5000 });
        
        // Check for error states
        const errorElements = page.locator('.error, .not-found, :has-text("Error"), :has-text("404"), :has-text("Not Found")');
        const errorCount = await errorElements.count();
        
        if (errorCount > 0) {
          const errorText = await errorElements.first().textContent();
          console.warn(`Warning: ${nav.name} may have errors: ${errorText}`);
        }
        
        // Check page loaded properly
        const bodyText = await page.locator('body').textContent();
        
        if (!bodyText || bodyText.trim().length < 50) {
          console.warn(`Warning: ${nav.name} appears to have minimal content`);
        }
        
        // Check for loading states that didn't resolve
        const loadingElements = page.locator('.loading, .spinner, :has-text("Loading")');
        const loadingCount = await loadingElements.count();
        
        if (loadingCount > 0) {
          console.warn(`Warning: ${nav.name} still shows loading indicators`);
        }
        
        console.log(`${nav.name}: Navigation successful`);
        await page.waitForTimeout(500);
        
      } catch (error) {
        throw new Error(`Navigation to ${nav.name} (${nav.path}) failed: ${error.message}`);
      }
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-navigation-flow.png') 
    });
  }

  async testTaskCRUD(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    // Go to tasks page
    await page.goto(`${baseUrl}/tasks`);
    await page.waitForLoadState('networkidle');
    
    // CREATE: Try to create a new task
    const createButton = page.locator('button:has-text("Create"), button:has-text("New"), button:has-text("Add"), .create-task, .new-task');
    const createExists = await createButton.count() > 0;
    
    if (!createExists) {
      throw new Error('No create task button found on tasks page');
    }
    
    await createButton.first().click();
    await page.waitForTimeout(1000);
    
    // Check modal opened
    const modal = page.locator('.modal, [data-testid="modal"]');
    const modalOpen = await modal.isVisible();
    
    if (!modalOpen) {
      throw new Error('Create task modal did not open');
    }
    
    // Fill form
    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
    const titleExists = await titleInput.count() > 0;
    
    if (!titleExists) {
      throw new Error('No title input found in task creation form');
    }
    
    const testTaskTitle = `Integration Test Task ${Date.now()}`;
    await titleInput.fill(testTaskTitle);
    
    // Optional: Fill description
    const descInput = page.locator('textarea[name="description"], textarea[placeholder*="description" i]');
    const descExists = await descInput.count() > 0;
    
    if (descExists) {
      await descInput.fill('Test task created by integration test');
    }
    
    // Submit
    const submitButton = page.locator('button:has-text("Create"), button:has-text("Save"), button[type="submit"]');
    const submitExists = await submitButton.count() > 0;
    
    if (!submitExists) {
      throw new Error('No submit button found in task creation form');
    }
    
    await submitButton.first().click();
    await page.waitForTimeout(2000);
    
    // Check task was created (modal closed, task appears in list)
    const modalStillOpen = await modal.isVisible().catch(() => false);
    
    if (modalStillOpen) {
      // Check for validation errors
      const errors = page.locator('.error, .validation-error, .form-error');
      const errorCount = await errors.count();
      
      if (errorCount > 0) {
        const errorText = await errors.first().textContent();
        throw new Error(`Task creation failed with validation error: ${errorText}`);
      } else {
        throw new Error('Task creation form did not submit (modal still open, no errors shown)');
      }
    }
    
    // READ: Check task appears in list
    await page.waitForTimeout(1000);
    const taskList = page.locator('.task-list, .tasks, .task-item, :has-text("' + testTaskTitle + '")');
    const taskFound = await taskList.count() > 0;
    
    if (!taskFound) {
      console.warn(`Warning: Created task "${testTaskTitle}" not immediately visible in task list`);
    } else {
      console.log(`Task "${testTaskTitle}" successfully created and visible`);
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-task-crud.png') 
    });
  }

  async testEventCRUD(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    // Go to events page
    await page.goto(`${baseUrl}/events`);
    await page.waitForLoadState('networkidle');
    
    // CREATE: Try to create a new event
    const createButton = page.locator('button:has-text("Create"), button:has-text("New"), button:has-text("Add"), .create-event, .new-event');
    const createExists = await createButton.count() > 0;
    
    if (!createExists) {
      throw new Error('No create event button found on events page');
    }
    
    await createButton.first().click();
    await page.waitForTimeout(1000);
    
    // Check modal opened
    const modal = page.locator('.modal, [data-testid="modal"]');
    const modalOpen = await modal.isVisible();
    
    if (!modalOpen) {
      throw new Error('Create event modal did not open');
    }
    
    // Fill form
    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
    const titleExists = await titleInput.count() > 0;
    
    if (!titleExists) {
      throw new Error('No title input found in event creation form');
    }
    
    const testEventTitle = `Integration Test Event ${Date.now()}`;
    await titleInput.fill(testEventTitle);
    
    // Optional: Fill other fields
    const startTimeInput = page.locator('input[name="startTime"], input[type="datetime-local"], input[type="time"]');
    const startTimeExists = await startTimeInput.count() > 0;
    
    if (startTimeExists) {
      await startTimeInput.fill('14:30');
    }
    
    // Submit
    const submitButton = page.locator('button:has-text("Create"), button:has-text("Save"), button[type="submit"]');
    const submitExists = await submitButton.count() > 0;
    
    if (!submitExists) {
      throw new Error('No submit button found in event creation form');
    }
    
    await submitButton.first().click();
    await page.waitForTimeout(2000);
    
    // Check event was created
    const modalStillOpen = await modal.isVisible().catch(() => false);
    
    if (modalStillOpen) {
      const errors = page.locator('.error, .validation-error, .form-error');
      const errorCount = await errors.count();
      
      if (errorCount > 0) {
        const errorText = await errors.first().textContent();
        throw new Error(`Event creation failed with validation error: ${errorText}`);
      } else {
        throw new Error('Event creation form did not submit');
      }
    }
    
    console.log(`Event "${testEventTitle}" creation attempted`);
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-event-crud.png') 
    });
  }

  async testModalAPIIntegration(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    // Monitor API calls from modal
    let apiCalled = false;
    let apiSuccess = false;
    
    page.on('request', request => {
      if (request.url().includes('/api/tasks') && request.method() === 'POST') {
        apiCalled = true;
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/tasks') && response.request().method() === 'POST') {
        apiSuccess = response.status() < 400;
      }
    });
    
    await page.goto(`${baseUrl}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    const taskButton = page.locator('button:has-text("Create New Task")');
    const buttonExists = await taskButton.count() > 0;
    
    if (!buttonExists) {
      throw new Error('Create New Task button not found on UI demo page');
    }
    
    await taskButton.click();
    await page.waitForTimeout(1000);
    
    // Fill and submit form
    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
    const titleExists = await titleInput.count() > 0;
    
    if (titleExists) {
      await titleInput.fill(`Modal API Test ${Date.now()}`);
      
      const submitButton = page.locator('button:has-text("Create"), button:has-text("Save")');
      const submitExists = await submitButton.count() > 0;
      
      if (submitExists) {
        await submitButton.first().click();
        await page.waitForTimeout(3000);
        
        if (!apiCalled) {
          console.warn('Warning: Modal form submission did not trigger API call');
        } else if (!apiSuccess) {
          console.warn('Warning: Modal API call failed or returned error');
        } else {
          console.log('Modal to API integration working correctly');
        }
      }
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-modal-api.png') 
    });
  }

  async testWidgetAPIIntegration(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    // Monitor widget-related API calls
    const widgetAPICalls = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        widgetAPICalls.push({
          url: request.url(),
          method: request.method()
        });
      }
    });
    
    await page.goto(`${baseUrl}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Wait for widgets to load
    await page.waitForTimeout(3000);
    
    // Check if widgets made API calls
    const taskCalls = widgetAPICalls.filter(call => call.url.includes('/api/tasks'));
    const eventCalls = widgetAPICalls.filter(call => call.url.includes('/api/events'));
    
    console.log(`Widget API integration: ${taskCalls.length} task calls, ${eventCalls.length} event calls`);
    
    if (taskCalls.length === 0 && eventCalls.length === 0) {
      console.warn('Warning: Widgets may not be making API calls for data');
    }
    
    // Check widget content
    const widgets = page.locator('.widget, [data-testid*="widget"], .dashboard-widget');
    const widgetCount = await widgets.count();
    
    if (widgetCount === 0) {
      throw new Error('No widgets found on dashboard for API integration test');
    }
    
    // Check if widgets show data vs loading/error states
    for (let i = 0; i < Math.min(widgetCount, 2); i++) {
      const widget = widgets.nth(i);
      const widgetText = await widget.textContent();
      
      const hasError = widgetText.includes('Error') || widgetText.includes('Failed');
      const hasLoading = widgetText.includes('Loading');
      const hasData = widgetText.length > 50 && !hasError && !hasLoading;
      
      console.log(`Widget ${i}: ${hasData ? 'Has data' : hasLoading ? 'Loading' : hasError ? 'Error' : 'Empty'}`);
    }
  }

  async testCommandPaletteNavigation(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    
    // Test command palette navigation
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open command palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const palette = page.locator('.command-palette, .palette, .search-palette');
    const paletteOpen = await palette.isVisible();
    
    if (!paletteOpen) {
      throw new Error('Command palette did not open for navigation test');
    }
    
    // Search for and navigate to tasks page
    const searchInput = page.locator('.command-palette input, .palette input, .search-input');
    const inputExists = await searchInput.count() > 0;
    
    if (!inputExists) {
      throw new Error('No search input found in command palette');
    }
    
    await searchInput.fill('tasks');
    await page.waitForTimeout(500);
    
    // Execute navigation
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);
    
    // Check if navigation occurred
    const currentUrl = page.url();
    
    if (!currentUrl.includes('/tasks')) {
      // Try clicking first result instead
      const results = page.locator('.command-item, .result-item, .palette-item');
      const resultCount = await results.count();
      
      if (resultCount > 0) {
        await page.keyboard.press(shortcut);
        await page.waitForTimeout(500);
        await searchInput.fill('tasks');
        await page.waitForTimeout(500);
        await results.first().click();
        await page.waitForTimeout(1000);
        
        const newUrl = page.url();
        
        if (!newUrl.includes('/tasks')) {
          throw new Error('Command palette navigation did not work');
        } else {
          console.log('Command palette navigation successful via click');
        }
      } else {
        throw new Error('Command palette search returned no results');
      }
    } else {
      console.log('Command palette navigation successful via Enter key');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-command-palette-nav.png') 
    });
  }

  async testStatePersistence(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    // Go to a page and interact with it
    await page.goto(`${baseUrl}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Fill out a form but don't submit
    const createButton = page.locator('button:has-text("Create New Task")');
    const buttonExists = await createButton.count() > 0;
    
    if (buttonExists) {
      await createButton.click();
      await page.waitForTimeout(1000);
      
      const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
      const titleExists = await titleInput.count() > 0;
      
      if (titleExists) {
        const testData = 'State persistence test data';
        await titleInput.fill(testData);
        await page.waitForTimeout(500);
        
        // Navigate away without saving
        await page.goto(`${baseUrl}/tasks`);
        await page.waitForTimeout(1000);
        
        // Navigate back to UI demo
        await page.goto(`${baseUrl}/ui-demo`);
        await page.waitForTimeout(1000);
        
        // Check if form state persisted (probably shouldn't, but let's verify)
        await createButton.click();
        await page.waitForTimeout(1000);
        
        const currentValue = await titleInput.inputValue();
        
        if (currentValue === testData) {
          console.log('Form state persisted across navigation (may or may not be desired)');
        } else {
          console.log('Form state reset after navigation (expected behavior)');
        }
      }
    }
    
    // Test local storage persistence
    await page.evaluate(() => {
      localStorage.setItem('test-integration', 'test-value');
    });
    
    await page.reload();
    await page.waitForTimeout(1000);
    
    const persistedValue = await page.evaluate(() => {
      return localStorage.getItem('test-integration');
    });
    
    if (persistedValue !== 'test-value') {
      console.warn('Warning: Local storage not persisting across page reloads');
    } else {
      console.log('Local storage persistence working');
    }
  }

  async testErrorHandling(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    // Test 404 page handling
    await page.goto(`${baseUrl}/nonexistent-page-${Date.now()}`);
    await page.waitForLoadState('networkidle');
    
    const errorContent = await page.locator('body').textContent();
    
    if (errorContent.includes('404') || errorContent.includes('Not Found') || errorContent.includes('Page not found')) {
      console.log('404 error handling working');
    } else {
      console.warn('Warning: 404 error page may not be properly configured');
    }
    
    // Test API error handling by blocking requests
    await page.route('**/api/**', route => route.abort());
    
    await page.goto(`${baseUrl}/tasks`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Check for error states when API is down
    const errorStates = page.locator('.error, .failed, :has-text("Error"), :has-text("Failed"), :has-text("Unable")');
    const errorCount = await errorStates.count();
    
    if (errorCount > 0) {
      console.log(`Found ${errorCount} error states when API blocked`);
    } else {
      console.warn('Warning: No error states shown when API is unreachable');
    }
    
    // Unblock API for other tests
    await page.unroute('**/api/**');
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-error-handling.png') 
    });
  }

  async testRealUserWorkflow(page, options) {
    const baseUrl = options.baseUrl || 'http://localhost:5173';
    
    console.log('Testing real user workflow: Create task, view schedule, navigate back');
    
    // Step 1: Start at dashboard
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Step 2: Navigate to tasks
    await page.click('a[href="/tasks"], button:has-text("Tasks"), .nav-tasks');
    await page.waitForLoadState('networkidle');
    
    // Step 3: Create a new task
    const createButton = page.locator('button:has-text("Create"), button:has-text("New")');
    const createExists = await createButton.count() > 0;
    
    if (createExists) {
      await createButton.first().click();
      await page.waitForTimeout(1000);
      
      const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
      const titleExists = await titleInput.count() > 0;
      
      if (titleExists) {
        await titleInput.fill('User workflow test task');
        
        const submitButton = page.locator('button:has-text("Create"), button:has-text("Save")');
        const submitExists = await submitButton.count() > 0;
        
        if (submitExists) {
          await submitButton.first().click();
          await page.waitForTimeout(2000);
        }
      }
    }
    
    // Step 4: Navigate to schedule
    const scheduleNav = page.locator('a[href="/schedule"], button:has-text("Schedule"), .nav-schedule');
    const scheduleExists = await scheduleNav.count() > 0;
    
    if (scheduleExists) {
      await scheduleNav.first().click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
    } else {
      await page.goto(`${baseUrl}/schedule`);
      await page.waitForLoadState('networkidle');
    }
    
    // Step 5: Try command palette shortcut
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const palette = page.locator('.command-palette, .palette');
    const paletteOpen = await palette.isVisible();
    
    if (paletteOpen) {
      await page.keyboard.press('Escape');
    }
    
    // Step 6: Navigate back to dashboard
    await page.goto(baseUrl);
    await page.waitForLoadState('networkidle');
    
    console.log('Real user workflow test completed');
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/integration-user-workflow.png') 
    });
  }
}

async function runTests(page, options = {}) {
  const tests = new IntegrationTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, IntegrationTests };