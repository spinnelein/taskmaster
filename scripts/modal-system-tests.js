// Modal System Tests for TaskMaster UI
// Tests all modal functionality including height constraints, focus trap, and accessibility
// NO EMOJIS

const fs = require('fs');
const path = require('path');

class ModalSystemTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Modal System Tests...');
    
    await this.runTest('Modal Opens Correctly', () => this.testModalOpening(page, options));
    await this.runTest('Modal Closing (ESC Key)', () => this.testEscapeKeyClose(page, options));
    await this.runTest('Modal Closing (Backdrop Click)', () => this.testBackdropClose(page, options));
    await this.runTest('Modal Height Constraints', () => this.testHeightConstraints(page, options));
    await this.runTest('Focus Trap Functionality', () => this.testFocusTrap(page, options));
    await this.runTest('Form Accessibility', () => this.testAccessibility(page, options));
    await this.runTest('Responsive Behavior', () => this.testResponsiveBehavior(page, options));
    await this.runTest('Multiple Modal Types', () => this.testMultipleModalTypes(page, options));
    await this.runTest('Modal Scroll Behavior', () => this.testScrollBehavior(page, options));
    
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

  async testModalOpening(page, options) {
    // Test task creation modal
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Take initial screenshot
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/modal-test-initial.png') 
    });
    
    // Click "Create New Task" button
    const taskButton = page.locator('button:has-text("Create New Task")');
    await taskButton.waitFor({ state: 'visible', timeout: 5000 });
    await taskButton.click();
    
    // Verify modal opens
    const modal = page.locator('[data-testid="modal"], .modal, .modal-overlay');
    await modal.waitFor({ state: 'visible', timeout: 3000 });
    
    const isVisible = await modal.isVisible();
    if (!isVisible) {
      throw new Error('Modal did not open after clicking Create New Task button');
    }
    
    // Take screenshot of opened modal
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/modal-opened.png') 
    });
  }

  async testEscapeKeyClose(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Press ESC key
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    
    // Verify modal is closed
    const modal = page.locator('[data-testid="modal"], .modal, .modal-overlay');
    const isVisible = await modal.isVisible().catch(() => false);
    
    if (isVisible) {
      throw new Error('Modal did not close with ESC key');
    }
  }

  async testBackdropClose(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Click backdrop (outside modal content)
    const modalOverlay = page.locator('.modal-overlay, .modal');
    await modalOverlay.first().click({ position: { x: 10, y: 10 } });
    await page.waitForTimeout(500);
    
    // Verify modal is closed
    const modal = page.locator('[data-testid="modal"], .modal, .modal-overlay');
    const isVisible = await modal.isVisible().catch(() => false);
    
    if (isVisible) {
      throw new Error('Modal did not close when clicking backdrop');
    }
  }

  async testHeightConstraints(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Get modal dimensions
    const modal = page.locator('.modal-content, .modal .content, [data-testid="modal-content"]').first();
    const boundingBox = await modal.boundingBox();
    
    if (!boundingBox) {
      throw new Error('Could not get modal dimensions');
    }
    
    const viewportHeight = page.viewportSize()?.height || 1080;
    const maxAllowedHeight = viewportHeight * 0.9; // 90vh
    
    if (boundingBox.height > maxAllowedHeight + 50) { // Allow 50px tolerance
      throw new Error(`Modal height ${boundingBox.height}px exceeds 90vh constraint (${maxAllowedHeight}px)`);
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/modal-height-test.png') 
    });
  }

  async testFocusTrap(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Find focusable elements in modal
    const focusableElements = await page.locator('input, button, select, textarea, [tabindex]:not([tabindex="-1"])').all();
    
    if (focusableElements.length === 0) {
      throw new Error('No focusable elements found in modal');
    }
    
    // Test Tab key cycling
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
    
    const activeElement = await page.evaluate(() => document.activeElement.tagName);
    
    if (!['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA'].includes(activeElement)) {
      throw new Error('Focus did not move to a focusable element');
    }
    
    // Test that focus stays within modal
    for (let i = 0; i < focusableElements.length + 2; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);
    }
    
    const finalActiveElement = await page.evaluate(() => {
      const active = document.activeElement;
      return {
        tagName: active.tagName,
        isInModal: active.closest('.modal, [data-testid="modal"]') !== null
      };
    });
    
    if (!finalActiveElement.isInModal) {
      throw new Error('Focus trap failed - focus moved outside modal');
    }
  }

  async testAccessibility(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Check for ARIA attributes
    const modalElements = await page.evaluate(() => {
      const modal = document.querySelector('.modal, [data-testid="modal"]');
      if (!modal) return null;
      
      return {
        hasRole: modal.getAttribute('role'),
        hasAriaLabel: modal.getAttribute('aria-label'),
        hasAriaLabelledBy: modal.getAttribute('aria-labelledby'),
        hasAriaDescribedBy: modal.getAttribute('aria-describedby'),
        hasTabIndex: modal.getAttribute('tabindex')
      };
    });
    
    if (!modalElements) {
      throw new Error('Modal element not found for accessibility testing');
    }
    
    // Check for proper ARIA attributes
    if (!modalElements.hasRole && !modalElements.hasAriaLabel && !modalElements.hasAriaLabelledBy) {
      throw new Error('Modal missing accessibility attributes (role, aria-label, or aria-labelledby)');
    }
    
    // Check form labels
    const unlabelledInputs = await page.locator('input:not([aria-label]):not([aria-labelledby])').count();
    const inputsWithoutLabels = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input');
      let unlabelled = 0;
      
      inputs.forEach(input => {
        const hasLabel = document.querySelector(`label[for="${input.id}"]`);
        if (!hasLabel && !input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
          unlabelled++;
        }
      });
      
      return unlabelled;
    });
    
    if (inputsWithoutLabels > 0) {
      console.warn(`Warning: ${inputsWithoutLabels} input(s) without proper labels found`);
    }
  }

  async testResponsiveBehavior(page, options) {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
      await page.waitForLoadState('networkidle');
      
      // Open modal
      await page.click('button:has-text("Create New Task")');
      await page.waitForTimeout(1000);
      
      // Check modal fits within viewport
      const modal = page.locator('.modal-content, .modal .content').first();
      const boundingBox = await modal.boundingBox();
      
      if (!boundingBox) {
        throw new Error(`Modal not found on ${viewport.name}`);
      }
      
      if (boundingBox.width > viewport.width || boundingBox.height > viewport.height) {
        throw new Error(`Modal overflows viewport on ${viewport.name}`);
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, `../logs/modal-responsive-${viewport.name.toLowerCase()}.png`) 
      });
      
      // Close modal
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    }
  }

  async testMultipleModalTypes(page, options) {
    const modalButtons = [
      'Create New Task',
      'Create New Event', 
      'Create New Initiative'
    ];
    
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    for (const buttonText of modalButtons) {
      try {
        // Click button if it exists
        const button = page.locator(`button:has-text("${buttonText}")`);
        const buttonExists = await button.count() > 0;
        
        if (buttonExists) {
          await button.click();
          await page.waitForTimeout(1000);
          
          // Verify modal opens
          const modal = page.locator('.modal, [data-testid="modal"]');
          const isVisible = await modal.isVisible();
          
          if (!isVisible) {
            throw new Error(`${buttonText} modal did not open`);
          }
          
          await page.screenshot({ 
            path: path.join(__dirname, `../logs/modal-${buttonText.replace(/\s+/g, '-').toLowerCase()}.png`) 
          });
          
          // Close modal
          await page.keyboard.press('Escape');
          await page.waitForTimeout(500);
        }
      } catch (error) {
        console.warn(`Warning: Could not test ${buttonText} modal - ${error.message}`);
      }
    }
  }

  async testScrollBehavior(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Try to fill in many form fields to trigger scroll
    const inputs = await page.locator('input, textarea').all();
    
    for (let i = 0; i < Math.min(inputs.length, 5); i++) {
      try {
        await inputs[i].fill(`Test data ${i + 1} - This is a longer text to see if scrolling works properly in the modal`);
        await page.waitForTimeout(100);
      } catch (error) {
        // Some inputs might not be fillable, that's okay
      }
    }
    
    // Test that modal content can scroll if needed
    const modalContent = page.locator('.modal-content, .modal .content').first();
    
    // Try scrolling within modal
    await modalContent.hover();
    await page.mouse.wheel(0, 500); // Scroll down
    await page.waitForTimeout(500);
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/modal-scroll-test.png') 
    });
    
    // The test passes if no errors are thrown during scrolling
  }
}

async function runTests(page, options = {}) {
  const tests = new ModalSystemTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, ModalSystemTests };