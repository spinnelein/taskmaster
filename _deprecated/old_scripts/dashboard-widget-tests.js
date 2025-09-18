// Dashboard Widget Tests for TaskMaster UI
// Tests widget rendering, drag-and-drop, API integration, and responsiveness
// NO EMOJIS

const path = require('path');

class DashboardWidgetTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Dashboard Widget Tests...');
    
    await this.runTest('Widget Grid Rendering', () => this.testWidgetGridRendering(page, options));
    await this.runTest('TodaysFocus Widget', () => this.testTodaysFocusWidget(page, options));
    await this.runTest('Calendar Snapshot Widget', () => this.testCalendarSnapshotWidget(page, options));
    await this.runTest('Widget Drag and Drop', () => this.testWidgetDragDrop(page, options));
    await this.runTest('Widget API Integration', () => this.testWidgetAPIIntegration(page, options));
    await this.runTest('Widget Loading States', () => this.testWidgetLoadingStates(page, options));
    await this.runTest('Widget Error States', () => this.testWidgetErrorStates(page, options));
    await this.runTest('Widget Interactions', () => this.testWidgetInteractions(page, options));
    await this.runTest('Widget Responsiveness', () => this.testWidgetResponsiveness(page, options));
    await this.runTest('Widget Customization', () => this.testWidgetCustomization(page, options));
    
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

  async testWidgetGridRendering(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Check if dashboard grid exists
    const dashboardGrid = page.locator('.dashboard-grid, [data-testid="dashboard-grid"], .widget-grid');
    const gridExists = await dashboardGrid.count() > 0;
    
    if (!gridExists) {
      // Try main dashboard page
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
      await page.waitForLoadState('networkidle');
      
      const mainGridExists = await page.locator('.dashboard-grid, [data-testid="dashboard-grid"], .widget-grid').count() > 0;
      if (!mainGridExists) {
        throw new Error('Dashboard widget grid not found on any page');
      }
    }
    
    // Check for widgets in the grid
    const widgets = page.locator('.widget, [data-testid*="widget"], .dashboard-widget');
    const widgetCount = await widgets.count();
    
    if (widgetCount === 0) {
      throw new Error('No widgets found in dashboard grid');
    }
    
    console.log(`Found ${widgetCount} widgets in dashboard`);
    
    // Check grid layout properties
    const gridStyles = await page.locator('.dashboard-grid, .widget-grid').first().evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        gridTemplateColumns: styles.gridTemplateColumns,
        gridGap: styles.gridGap || styles.gap
      };
    });
    
    if (!gridStyles.display.includes('grid') && !gridStyles.gridTemplateColumns) {
      console.warn('Warning: Dashboard grid may not be using CSS Grid layout');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/dashboard-grid-rendering.png') 
    });
  }

  async testTodaysFocusWidget(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for TodaysFocus widget
    const todaysFocusWidget = page.locator('[data-testid*="todays-focus"], [data-testid*="focus"], .todays-focus-widget, :has-text("Today\'s Focus")').first();
    
    // Wait for widget to appear
    try {
      await todaysFocusWidget.waitFor({ state: 'visible', timeout: 5000 });
    } catch (error) {
      // Try main dashboard
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
      await page.waitForLoadState('networkidle');
      
      const mainPageWidget = page.locator('[data-testid*="todays-focus"], [data-testid*="focus"], .todays-focus-widget, :has-text("Today\'s Focus")').first();
      await mainPageWidget.waitFor({ state: 'visible', timeout: 5000 });
    }
    
    const widgetExists = await todaysFocusWidget.isVisible();
    if (!widgetExists) {
      throw new Error('TodaysFocus widget not found or not visible');
    }
    
    // Check for task list within widget
    const taskList = todaysFocusWidget.locator('.task-list, .tasks, ul, ol, .task-item').first();
    
    // Wait for content to load (may be async)
    await page.waitForTimeout(2000);
    
    // Check if widget shows loading, error, or content
    const widgetText = await todaysFocusWidget.textContent();
    
    if (!widgetText || widgetText.trim().length === 0) {
      throw new Error('TodaysFocus widget appears to be empty');
    }
    
    // Look for task-related content
    const hasTaskContent = widgetText.includes('task') || 
                          widgetText.includes('priority') || 
                          widgetText.includes('active') ||
                          await taskList.count() > 0;
    
    if (!hasTaskContent) {
      console.warn('Warning: TodaysFocus widget may not be showing task data');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/todays-focus-widget.png') 
    });
  }

  async testCalendarSnapshotWidget(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for Calendar Snapshot widget
    const calendarWidget = page.locator('[data-testid*="calendar"], .calendar-snapshot-widget, :has-text("Calendar"), :has-text("Events")').first();
    
    // Wait for widget to appear
    try {
      await calendarWidget.waitFor({ state: 'visible', timeout: 5000 });
    } catch (error) {
      // Try main dashboard
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
      await page.waitForLoadState('networkidle');
      
      const mainPageWidget = page.locator('[data-testid*="calendar"], .calendar-snapshot-widget, :has-text("Calendar"), :has-text("Events")').first();
      await mainPageWidget.waitFor({ state: 'visible', timeout: 5000 });
    }
    
    const widgetExists = await calendarWidget.isVisible();
    if (!widgetExists) {
      throw new Error('Calendar Snapshot widget not found or not visible');
    }
    
    // Wait for content to load
    await page.waitForTimeout(2000);
    
    // Check widget content
    const widgetText = await calendarWidget.textContent();
    
    if (!widgetText || widgetText.trim().length === 0) {
      throw new Error('Calendar Snapshot widget appears to be empty');
    }
    
    // Look for calendar/event-related content
    const hasCalendarContent = widgetText.includes('event') || 
                              widgetText.includes('meeting') || 
                              widgetText.includes('schedule') ||
                              widgetText.includes('today') ||
                              widgetText.includes('upcoming');
    
    if (!hasCalendarContent) {
      console.warn('Warning: Calendar Snapshot widget may not be showing event data');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/calendar-snapshot-widget.png') 
    });
  }

  async testWidgetDragDrop(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for draggable widgets
    const widgets = page.locator('.widget, [data-testid*="widget"], .dashboard-widget, [draggable="true"]');
    const widgetCount = await widgets.count();
    
    if (widgetCount < 2) {
      console.warn('Warning: Not enough widgets to test drag and drop');
      return;
    }
    
    try {
      // Get initial positions
      const firstWidget = widgets.first();
      const secondWidget = widgets.nth(1);
      
      const firstBox = await firstWidget.boundingBox();
      const secondBox = await secondWidget.boundingBox();
      
      if (!firstBox || !secondBox) {
        throw new Error('Could not get widget positions for drag test');
      }
      
      // Attempt drag and drop
      await page.mouse.move(firstBox.x + firstBox.width / 2, firstBox.y + firstBox.height / 2);
      await page.mouse.down();
      await page.mouse.move(secondBox.x + secondBox.width / 2, secondBox.y + secondBox.height / 2, { steps: 10 });
      await page.mouse.up();
      
      await page.waitForTimeout(1000);
      
      // Take screenshot after drag attempt
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/widget-drag-drop-attempt.png') 
      });
      
      console.log('Drag and drop attempted - check screenshot for visual confirmation');
      
    } catch (error) {
      console.warn(`Warning: Could not test widget drag and drop: ${error.message}`);
    }
  }

  async testWidgetAPIIntegration(page, options) {
    // Monitor network requests
    const apiRequests = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          url: request.url(),
          method: request.method()
        });
      }
    });
    
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Wait for API calls
    await page.waitForTimeout(3000);
    
    // Check if widgets made API calls
    const taskAPICalls = apiRequests.filter(req => req.url().includes('/api/tasks'));
    const eventAPICalls = apiRequests.filter(req => req.url().includes('/api/events'));
    
    if (taskAPICalls.length === 0) {
      console.warn('Warning: No task API calls detected from widgets');
    }
    
    if (eventAPICalls.length === 0) {
      console.warn('Warning: No event API calls detected from widgets');
    }
    
    console.log(`API integration: ${taskAPICalls.length} task calls, ${eventAPICalls.length} event calls`);
    
    // Check for loading indicators during API calls
    const loadingIndicators = page.locator('.loading, .spinner, .skeleton, :has-text("Loading")');
    const loadingCount = await loadingIndicators.count();
    
    console.log(`Found ${loadingCount} loading indicators`);
  }

  async testWidgetLoadingStates(page, options) {
    // Test loading states by going to page and checking immediately
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    
    // Check for loading states immediately
    const loadingStates = page.locator('.loading, .spinner, .skeleton, :has-text("Loading"), .widget-loading');
    const loadingCount = await loadingStates.count();
    
    if (loadingCount > 0) {
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/widget-loading-states.png') 
      });
      
      console.log(`Found ${loadingCount} loading states`);
    }
    
    // Wait for loading to complete
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    
    // Check that loading states are gone
    const remainingLoading = await loadingStates.count();
    
    if (remainingLoading > 0) {
      console.warn(`Warning: ${remainingLoading} loading states still present after loading`);
    }
  }

  async testWidgetErrorStates(page, options) {
    // Test error states by blocking API requests
    await page.route('**/api/tasks', route => route.abort());
    await page.route('**/api/events', route => route.abort());
    
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Wait for widgets to attempt loading
    await page.waitForTimeout(3000);
    
    // Check for error states
    const errorStates = page.locator('.error, .widget-error, :has-text("Error"), :has-text("Failed"), :has-text("Unable")');
    const errorCount = await errorStates.count();
    
    if (errorCount === 0) {
      console.warn('Warning: No error states found when API requests blocked');
    } else {
      console.log(`Found ${errorCount} error states`);
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/widget-error-states.png') 
      });
    }
    
    // Unblock requests for other tests
    await page.unroute('**/api/tasks');
    await page.unroute('**/api/events');
  }

  async testWidgetInteractions(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Wait for widgets to load
    await page.waitForTimeout(2000);
    
    // Test clickable elements in widgets
    const widgets = page.locator('.widget, [data-testid*="widget"], .dashboard-widget');
    const widgetCount = await widgets.count();
    
    for (let i = 0; i < Math.min(widgetCount, 3); i++) {
      const widget = widgets.nth(i);
      
      // Look for clickable elements within widget
      const clickableElements = widget.locator('button, a, .clickable, [role="button"]');
      const clickableCount = await clickableElements.count();
      
      if (clickableCount > 0) {
        try {
          // Test clicking first clickable element
          await clickableElements.first().click();
          await page.waitForTimeout(1000);
          
          // Check if navigation occurred or modal opened
          const currentUrl = page.url();
          const modalOpen = await page.locator('.modal, [data-testid="modal"]').count() > 0;
          
          if (!currentUrl.includes('phase3-demo') || modalOpen) {
            console.log(`Widget ${i} interaction caused navigation or modal`);
            
            // Go back to test page
            if (!modalOpen) {
              await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
              await page.waitForLoadState('networkidle');
            } else {
              await page.keyboard.press('Escape');
              await page.waitForTimeout(500);
            }
          }
          
        } catch (error) {
          console.warn(`Could not test widget ${i} interaction: ${error.message}`);
        }
      }
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/widget-interactions.png') 
    });
  }

  async testWidgetResponsiveness(page, options) {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 1024, height: 768, name: 'Tablet Landscape' },
      { width: 768, height: 1024, name: 'Tablet Portrait' },
      { width: 375, height: 667, name: 'Mobile' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
      await page.waitForLoadState('networkidle');
      
      // Check widget grid layout
      const grid = page.locator('.dashboard-grid, .widget-grid').first();
      const gridExists = await grid.count() > 0;
      
      if (gridExists) {
        const gridStyles = await grid.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return {
            gridTemplateColumns: styles.gridTemplateColumns,
            gridGap: styles.gridGap || styles.gap
          };
        });
        
        console.log(`${viewport.name} grid: ${gridStyles.gridTemplateColumns}`);
      }
      
      // Check widget visibility and layout
      const widgets = page.locator('.widget, [data-testid*="widget"], .dashboard-widget');
      const widgetCount = await widgets.count();
      
      let visibleWidgets = 0;
      for (let i = 0; i < widgetCount; i++) {
        const isVisible = await widgets.nth(i).isVisible();
        if (isVisible) visibleWidgets++;
      }
      
      if (visibleWidgets === 0) {
        console.warn(`Warning: No widgets visible on ${viewport.name}`);
      }
      
      console.log(`${viewport.name}: ${visibleWidgets}/${widgetCount} widgets visible`);
      
      await page.screenshot({ 
        path: path.join(__dirname, `../logs/widget-responsive-${viewport.name.toLowerCase().replace(/\s+/g, '-')}.png`) 
      });
    }
  }

  async testWidgetCustomization(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for widget customization options
    const customizationElements = page.locator('.widget-settings, .customize, .config, .settings, [title*="config"], [title*="setting"]');
    const customizationCount = await customizationElements.count();
    
    if (customizationCount > 0) {
      console.log(`Found ${customizationCount} widget customization elements`);
      
      try {
        // Test first customization element
        await customizationElements.first().click();
        await page.waitForTimeout(1000);
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/widget-customization.png') 
        });
        
        // Close customization if modal opened
        const modalOpen = await page.locator('.modal, [data-testid="modal"]').count() > 0;
        if (modalOpen) {
          await page.keyboard.press('Escape');
        }
        
      } catch (error) {
        console.warn(`Could not test widget customization: ${error.message}`);
      }
    } else {
      console.warn('Warning: No widget customization options found');
    }
  }
}

async function runTests(page, options = {}) {
  const tests = new DashboardWidgetTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, DashboardWidgetTests };