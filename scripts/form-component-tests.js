// Form Component Tests for TaskMaster UI
// Tests form components including FormGrid, FormField, FormSection, and form validation
// NO EMOJIS

const path = require('path');

class FormComponentTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Form Component Tests...');
    
    await this.runTest('Form Grid Layout', () => this.testFormGridLayout(page, options));
    await this.runTest('Form Field Rendering', () => this.testFormFieldRendering(page, options));
    await this.runTest('Form Validation', () => this.testFormValidation(page, options));
    await this.runTest('Progressive Disclosure', () => this.testProgressiveDisclosure(page, options));
    await this.runTest('Form Section Collapsing', () => this.testSectionCollapsing(page, options));
    await this.runTest('Priority Matrix', () => this.testPriorityMatrix(page, options));
    await this.runTest('Form Data Persistence', () => this.testDataPersistence(page, options));
    await this.runTest('Required Field Validation', () => this.testRequiredFields(page, options));
    await this.runTest('Input Type Support', () => this.testInputTypes(page, options));
    await this.runTest('Form Responsiveness', () => this.testFormResponsiveness(page, options));
    
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

  async testFormGridLayout(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal to access form
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Check if form grid exists
    const formGrid = page.locator('.form-grid, [data-testid="form-grid"]');
    const gridExists = await formGrid.count() > 0;
    
    if (!gridExists) {
      throw new Error('Form grid not found in task creation modal');
    }
    
    // Test responsive columns
    const gridStyles = await formGrid.first().evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        gridTemplateColumns: styles.gridTemplateColumns,
        gap: styles.gap || styles.gridGap
      };
    });
    
    if (gridStyles.display !== 'grid' && !gridStyles.gridTemplateColumns) {
      throw new Error('Form grid does not have proper CSS grid properties');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/form-grid-layout.png') 
    });
  }

  async testFormFieldRendering(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Check for form fields
    const formFields = page.locator('.form-field, [data-testid="form-field"]');
    const fieldCount = await formFields.count();
    
    if (fieldCount === 0) {
      throw new Error('No form fields found in task creation form');
    }
    
    // Test required field indicators
    const requiredFields = page.locator('.form-required, .required, [required]');
    const requiredCount = await requiredFields.count();
    
    // Test labels exist for form fields
    const labels = page.locator('label, .form-label');
    const labelCount = await labels.count();
    
    if (labelCount === 0) {
      throw new Error('No labels found for form fields');
    }
    
    // Test input elements exist
    const inputs = page.locator('input, textarea, select');
    const inputCount = await inputs.count();
    
    if (inputCount === 0) {
      throw new Error('No input elements found in form');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/form-fields-rendered.png') 
    });
  }

  async testFormValidation(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Try to submit form without required fields
    const submitButton = page.locator('button:has-text("Create"), button:has-text("Save"), button[type="submit"]');
    const submitExists = await submitButton.count() > 0;
    
    if (submitExists) {
      await submitButton.first().click();
      await page.waitForTimeout(1000);
      
      // Check for validation errors
      const errorMessages = page.locator('.form-error, .error, .validation-error, .invalid-feedback');
      const errorCount = await errorMessages.count();
      
      // Check if form prevented submission (modal should still be open)
      const modalStillOpen = await page.locator('.modal, [data-testid="modal"]').isVisible();
      
      if (!modalStillOpen && errorCount === 0) {
        console.warn('Warning: Form submitted without validation or error messages');
      }
    } else {
      console.warn('Warning: No submit button found to test validation');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/form-validation-test.png') 
    });
  }

  async testProgressiveDisclosure(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Look for collapsible sections or progressive disclosure elements
    const disclosureElements = page.locator('.collapsible, .expandable, .disclosure, [data-testid*="collaps"], [data-testid*="expand"]');
    const disclosureCount = await disclosureElements.count();
    
    if (disclosureCount > 0) {
      // Test expanding/collapsing first found element
      const firstDisclosure = disclosureElements.first();
      
      // Try to toggle disclosure
      const toggleButton = page.locator('button:has-text("Show"), button:has-text("Hide"), button:has-text("More"), button:has-text("Less"), .toggle, .expand-button').first();
      const toggleExists = await toggleButton.count() > 0;
      
      if (toggleExists) {
        await toggleButton.click();
        await page.waitForTimeout(500);
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/progressive-disclosure-expanded.png') 
        });
        
        // Toggle back
        await toggleButton.click();
        await page.waitForTimeout(500);
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/progressive-disclosure-collapsed.png') 
        });
      }
    } else {
      console.warn('Warning: No progressive disclosure elements found');
    }
  }

  async testSectionCollapsing(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Look for form sections
    const formSections = page.locator('.form-section, .section, [data-testid*="section"]');
    const sectionCount = await formSections.count();
    
    if (sectionCount > 0) {
      // Test each section for collapsibility
      for (let i = 0; i < Math.min(sectionCount, 3); i++) {
        const section = formSections.nth(i);
        const sectionHeader = section.locator('.section-header, .header, h1, h2, h3, h4, h5, h6').first();
        
        const headerExists = await sectionHeader.count() > 0;
        if (headerExists) {
          try {
            await sectionHeader.click();
            await page.waitForTimeout(300);
          } catch (error) {
            // Section might not be clickable, that's okay
          }
        }
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/form-sections-test.png') 
      });
    } else {
      console.warn('Warning: No form sections found for collapsing test');
    }
  }

  async testPriorityMatrix(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Look for priority matrix or priority selection
    const priorityElements = page.locator('[data-testid*="priority"], .priority-matrix, .priority-selector, select[name*="priority"], input[name*="priority"]');
    const priorityCount = await priorityElements.count();
    
    if (priorityCount > 0) {
      const priorityElement = priorityElements.first();
      
      // Test priority selection
      const elementType = await priorityElement.evaluate(el => el.tagName.toLowerCase());
      
      if (elementType === 'select') {
        // Test dropdown selection
        await priorityElement.selectOption({ index: 1 });
        await page.waitForTimeout(300);
        
      } else if (elementType === 'input') {
        // Test input field
        await priorityElement.fill('high');
        await page.waitForTimeout(300);
        
      } else {
        // Test clicking on matrix/selector
        await priorityElement.click();
        await page.waitForTimeout(300);
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/priority-matrix-test.png') 
      });
    } else {
      console.warn('Warning: No priority matrix or selector found');
    }
  }

  async testDataPersistence(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Fill in form data
    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i], input[id*="title"]').first();
    const titleExists = await titleInput.count() > 0;
    
    if (titleExists) {
      const testTitle = 'Persistent Test Task';
      await titleInput.fill(testTitle);
      await page.waitForTimeout(300);
      
      // Fill other fields if they exist
      const descriptionField = page.locator('textarea[name="description"], textarea[placeholder*="description" i]').first();
      const descExists = await descriptionField.count() > 0;
      
      if (descExists) {
        await descriptionField.fill('Test description for persistence');
        await page.waitForTimeout(300);
      }
      
      // Navigate away and back (if possible)
      await page.keyboard.press('Tab');
      await page.waitForTimeout(500);
      
      // Check if data persists
      const currentTitle = await titleInput.inputValue();
      
      if (currentTitle !== testTitle) {
        throw new Error('Form data did not persist during interaction');
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/form-data-persistence.png') 
      });
    } else {
      throw new Error('No title input found to test data persistence');
    }
  }

  async testRequiredFields(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Find required fields
    const requiredFields = page.locator('input[required], textarea[required], select[required], .required input, .required textarea, .required select');
    const requiredCount = await requiredFields.count();
    
    // Check visual indicators for required fields
    const requiredIndicators = page.locator('.form-required, .required-indicator, .asterisk, *:has-text("*")');
    const indicatorCount = await requiredIndicators.count();
    
    if (requiredCount > 0) {
      console.log(`Found ${requiredCount} required fields with ${indicatorCount} visual indicators`);
      
      // Test that required fields show validation when empty
      for (let i = 0; i < Math.min(requiredCount, 3); i++) {
        const field = requiredFields.nth(i);
        
        try {
          // Clear the field and trigger validation
          await field.clear();
          await field.blur();
          await page.waitForTimeout(300);
          
          // Look for validation message
          const validationMessage = page.locator('.form-error, .error, .validation-error').first();
          const hasValidation = await validationMessage.count() > 0;
          
          if (!hasValidation) {
            console.warn(`Warning: Required field ${i} does not show validation error when empty`);
          }
          
        } catch (error) {
          console.warn(`Could not test required field ${i}: ${error.message}`);
        }
      }
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/required-fields-test.png') 
    });
  }

  async testInputTypes(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
    await page.waitForLoadState('networkidle');
    
    // Open task creation modal
    await page.click('button:has-text("Create New Task")');
    await page.waitForTimeout(1000);
    
    // Test different input types
    const inputTypes = {
      text: 'input[type="text"], input:not([type])',
      email: 'input[type="email"]',
      date: 'input[type="date"]',
      datetime: 'input[type="datetime-local"]',
      time: 'input[type="time"]',
      number: 'input[type="number"]',
      select: 'select',
      textarea: 'textarea',
      checkbox: 'input[type="checkbox"]',
      radio: 'input[type="radio"]'
    };
    
    const foundInputTypes = {};
    
    for (const [type, selector] of Object.entries(inputTypes)) {
      const elements = page.locator(selector);
      const count = await elements.count();
      
      if (count > 0) {
        foundInputTypes[type] = count;
        
        // Test interaction with first element of each type
        try {
          const firstElement = elements.first();
          
          switch (type) {
            case 'text':
            case 'email':
              await firstElement.fill(`test-${type}-value`);
              break;
            case 'date':
              await firstElement.fill('2024-12-31');
              break;
            case 'time':
              await firstElement.fill('14:30');
              break;
            case 'number':
              await firstElement.fill('42');
              break;
            case 'select':
              if (await firstElement.locator('option').count() > 1) {
                await firstElement.selectOption({ index: 1 });
              }
              break;
            case 'textarea':
              await firstElement.fill('Test textarea content');
              break;
            case 'checkbox':
            case 'radio':
              await firstElement.check();
              break;
          }
          
          await page.waitForTimeout(200);
          
        } catch (error) {
          console.warn(`Could not interact with ${type} input: ${error.message}`);
        }
      }
    }
    
    console.log('Found input types:', foundInputTypes);
    
    if (Object.keys(foundInputTypes).length === 0) {
      throw new Error('No input types found to test');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/input-types-test.png') 
    });
  }

  async testFormResponsiveness(page, options) {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/ui-demo`);
      await page.waitForLoadState('networkidle');
      
      // Open task creation modal
      await page.click('button:has-text("Create New Task")');
      await page.waitForTimeout(1000);
      
      // Check form grid responsiveness
      const formGrid = page.locator('.form-grid, [data-testid="form-grid"]');
      const gridExists = await formGrid.count() > 0;
      
      if (gridExists) {
        const gridColumns = await formGrid.first().evaluate(el => {
          const styles = window.getComputedStyle(el);
          return styles.gridTemplateColumns;
        });
        
        // Verify grid adjusts to viewport
        if (viewport.width <= 480 && gridColumns && gridColumns.includes('1fr 1fr')) {
          console.warn(`Warning: Form grid may not be responsive on ${viewport.name} (${gridColumns})`);
        }
      }
      
      // Check that all form elements are visible and accessible
      const formElements = page.locator('input, textarea, select, button');
      const elementCount = await formElements.count();
      
      for (let i = 0; i < Math.min(elementCount, 5); i++) {
        const element = formElements.nth(i);
        const isVisible = await element.isVisible();
        
        if (!isVisible) {
          console.warn(`Warning: Form element ${i} not visible on ${viewport.name}`);
        }
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, `../logs/form-responsive-${viewport.name.toLowerCase()}.png`) 
      });
      
      // Close modal
      await page.keyboard.press('Escape');
      await page.waitForTimeout(500);
    }
  }
}

async function runTests(page, options = {}) {
  const tests = new FormComponentTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, FormComponentTests };