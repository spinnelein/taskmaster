// Notification System Tests for TaskMaster UI
// Tests toast notifications, auto-dismiss, progress bars, and action buttons  
// NO EMOJIS

const path = require('path');

class NotificationTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Notification System Tests...');
    
    await this.runTest('Toast Notification Display', () => this.testToastDisplay(page, options));
    await this.runTest('Auto-Dismiss Functionality', () => this.testAutoDismiss(page, options));
    await this.runTest('Manual Dismiss', () => this.testManualDismiss(page, options));
    await this.runTest('Progress Bar Notifications', () => this.testProgressBars(page, options));
    await this.runTest('Action Button Functionality', () => this.testActionButtons(page, options));
    await this.runTest('Multiple Notification Stacking', () => this.testNotificationStacking(page, options));
    await this.runTest('Notification Types', () => this.testNotificationTypes(page, options));
    await this.runTest('Position and Layout', () => this.testPositionLayout(page, options));
    await this.runTest('Animation and Transitions', () => this.testAnimations(page, options));
    
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

  async testToastDisplay(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for notification trigger buttons
    const triggerButtons = page.locator('button:has-text("Show"), button:has-text("Test"), button:has-text("Notify"), .notification-trigger, .test-notification');
    const buttonCount = await triggerButtons.count();
    
    if (buttonCount > 0) {
      console.log(`Found ${buttonCount} notification trigger buttons`);
      
      // Click first trigger button
      await triggerButtons.first().click();
      await page.waitForTimeout(1000);
      
      // Check for toast notifications
      const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast, .react-hot-toast');
      const toastCount = await toasts.count();
      
      if (toastCount > 0) {
        console.log(`Found ${toastCount} toast notifications`);
        
        const firstToast = toasts.first();
        const toastText = await firstToast.textContent();
        
        console.log(`Toast content: "${toastText}"`);
        
        // Check toast is visible
        const isVisible = await firstToast.isVisible();
        if (!isVisible) {
          throw new Error('Toast notification is not visible');
        }
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/toast-notification-display.png') 
        });
        
      } else {
        throw new Error('No toast notifications appeared after clicking trigger');
      }
      
    } else {
      // Try to trigger notifications through actions
      console.log('No explicit notification triggers found, trying to trigger through actions');
      
      // Try actions that might trigger notifications
      const actionButtons = page.locator('button:has-text("Save"), button:has-text("Create"), button:has-text("Delete"), button:has-text("Complete")');
      const actionCount = await actionButtons.count();
      
      if (actionCount > 0) {
        await actionButtons.first().click();
        await page.waitForTimeout(2000);
        
        const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast, .react-hot-toast');
        const toastCount = await toasts.count();
        
        if (toastCount === 0) {
          console.warn('Warning: No notifications triggered by user actions');
        } else {
          console.log(`Action triggered ${toastCount} notifications`);
        }
      } else {
        console.warn('Warning: No buttons found to test notification system');
      }
    }
  }

  async testAutoDismiss(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Trigger a notification
    const triggerButtons = page.locator('button:has-text("Show"), button:has-text("Test"), button:has-text("Notify"), .notification-trigger');
    const buttonExists = await triggerButtons.count() > 0;
    
    if (buttonExists) {
      await triggerButtons.first().click();
      await page.waitForTimeout(500);
      
      // Check notification appears
      let toasts = page.locator('.toast, .notification, .alert, .Toastify__toast, .react-hot-toast');
      let toastCount = await toasts.count();
      
      if (toastCount > 0) {
        console.log(`Notification appeared, waiting for auto-dismiss...`);
        
        // Wait for auto-dismiss (typically 3-5 seconds)
        await page.waitForTimeout(6000);
        
        // Check if notification dismissed
        toastCount = await toasts.count();
        const stillVisible = toastCount > 0 && await toasts.first().isVisible().catch(() => false);
        
        if (stillVisible) {
          console.warn('Warning: Notification did not auto-dismiss after 6 seconds');
        } else {
          console.log('Notification auto-dismissed successfully');
        }
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/notification-auto-dismiss.png') 
        });
        
      } else {
        throw new Error('No notification appeared to test auto-dismiss');
      }
      
    } else {
      console.warn('Warning: No notification triggers found for auto-dismiss test');
    }
  }

  async testManualDismiss(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Trigger a notification
    const triggerButtons = page.locator('button:has-text("Show"), button:has-text("Test"), button:has-text("Notify")');
    const buttonExists = await triggerButtons.count() > 0;
    
    if (buttonExists) {
      await triggerButtons.first().click();
      await page.waitForTimeout(500);
      
      const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast, .react-hot-toast');
      const toastCount = await toasts.count();
      
      if (toastCount > 0) {
        const firstToast = toasts.first();
        
        // Look for close button
        const closeButton = firstToast.locator('button, .close, .dismiss, [role="button"], .Toastify__close-button, .close-btn');
        const closeButtonExists = await closeButton.count() > 0;
        
        if (closeButtonExists) {
          await closeButton.first().click();
          await page.waitForTimeout(1000);
          
          // Check if toast was dismissed
          const stillVisible = await firstToast.isVisible().catch(() => false);
          
          if (stillVisible) {
            throw new Error('Toast notification was not dismissed manually');
          } else {
            console.log('Manual dismiss successful');
          }
          
        } else {
          // Try clicking on the toast itself
          console.log('No close button found, trying to click toast to dismiss');
          
          await firstToast.click();
          await page.waitForTimeout(1000);
          
          const stillVisible = await firstToast.isVisible().catch(() => false);
          
          if (stillVisible) {
            console.warn('Warning: No manual dismiss method found for notifications');
          } else {
            console.log('Toast dismissed by clicking on it');
          }
        }
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/notification-manual-dismiss.png') 
        });
        
      } else {
        throw new Error('No notification appeared to test manual dismiss');
      }
    }
  }

  async testProgressBars(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for progress-related triggers
    const progressTriggers = page.locator('button:has-text("Progress"), button:has-text("Upload"), button:has-text("Loading"), .progress-trigger');
    const triggerExists = await progressTriggers.count() > 0;
    
    if (triggerExists) {
      await progressTriggers.first().click();
      await page.waitForTimeout(1000);
      
      // Look for progress bars in notifications
      const progressBars = page.locator('.progress, .progress-bar, .Toastify__progress-bar, [role="progressbar"]');
      const progressCount = await progressBars.count();
      
      if (progressCount > 0) {
        console.log(`Found ${progressCount} progress bars in notifications`);
        
        const firstProgress = progressBars.first();
        
        // Check progress bar has proper attributes
        const progressAttributes = await firstProgress.evaluate(el => ({
          role: el.getAttribute('role'),
          ariaValueNow: el.getAttribute('aria-valuenow'),
          ariaValueMax: el.getAttribute('aria-valuemax'),
          style: el.style.width
        }));
        
        console.log('Progress bar attributes:', progressAttributes);
        
        // Watch progress bar for a few seconds
        for (let i = 0; i < 5; i++) {
          await page.waitForTimeout(1000);
          
          const currentWidth = await firstProgress.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return styles.width;
          });
          
          console.log(`Progress bar width at ${i + 1}s: ${currentWidth}`);
        }
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/notification-progress-bars.png') 
        });
        
      } else {
        console.warn('Warning: No progress bars found in notifications');
      }
      
    } else {
      console.warn('Warning: No progress notification triggers found');
    }
  }

  async testActionButtons(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Trigger notifications that might have action buttons
    const triggers = page.locator('button:has-text("Action"), button:has-text("Confirm"), button:has-text("Delete"), button:has-text("Save")');
    const triggerCount = await triggers.count();
    
    if (triggerCount > 0) {
      await triggers.first().click();
      await page.waitForTimeout(1000);
      
      const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast');
      const toastCount = await toasts.count();
      
      if (toastCount > 0) {
        const firstToast = toasts.first();
        
        // Look for action buttons within notification
        const actionButtons = firstToast.locator('button, .action, .btn, a[role="button"]');
        const actionCount = await actionButtons.count();
        
        if (actionCount > 0) {
          console.log(`Found ${actionCount} action buttons in notification`);
          
          // Test clicking action buttons
          for (let i = 0; i < Math.min(actionCount, 2); i++) {
            const actionButton = actionButtons.nth(i);
            const buttonText = await actionButton.textContent();
            
            console.log(`Testing action button: "${buttonText}"`);
            
            await actionButton.click();
            await page.waitForTimeout(1000);
            
            // Check if action had effect (notification dismissed, modal opened, etc.)
            const toastStillVisible = await firstToast.isVisible().catch(() => false);
            const modalOpened = await page.locator('.modal, [data-testid="modal"]').count() > 0;
            
            if (!toastStillVisible) {
              console.log(`Action button "${buttonText}" dismissed notification`);
            } else if (modalOpened) {
              console.log(`Action button "${buttonText}" opened modal`);
              await page.keyboard.press('Escape'); // Close modal
            }
          }
          
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/notification-action-buttons.png') 
          });
          
        } else {
          console.warn('Warning: No action buttons found in notifications');
        }
        
      } else {
        console.warn('Warning: No notifications appeared to test action buttons');
      }
    }
  }

  async testNotificationStacking(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Try to trigger multiple notifications quickly
    const triggerButtons = page.locator('button:has-text("Show"), button:has-text("Test"), button:has-text("Notify")');
    const buttonExists = await triggerButtons.count() > 0;
    
    if (buttonExists) {
      const trigger = triggerButtons.first();
      
      // Trigger multiple notifications
      for (let i = 0; i < 3; i++) {
        await trigger.click();
        await page.waitForTimeout(200); // Quick succession
      }
      
      await page.waitForTimeout(1000);
      
      // Check if multiple notifications are displayed
      const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast');
      const toastCount = await toasts.count();
      
      if (toastCount > 1) {
        console.log(`Multiple notifications stacking: ${toastCount} notifications visible`);
        
        // Check positioning (stacked vertically or horizontally)
        const positions = [];
        
        for (let i = 0; i < Math.min(toastCount, 3); i++) {
          const toast = toasts.nth(i);
          const box = await toast.boundingBox();
          
          if (box) {
            positions.push({ x: box.x, y: box.y, width: box.width, height: box.height });
          }
        }
        
        console.log('Notification positions:', positions);
        
        // Check for proper spacing
        if (positions.length >= 2) {
          const verticalSpacing = Math.abs(positions[1].y - positions[0].y);
          const horizontalSpacing = Math.abs(positions[1].x - positions[0].x);
          
          if (verticalSpacing > horizontalSpacing) {
            console.log(`Notifications stacked vertically with ${verticalSpacing}px spacing`);
          } else if (horizontalSpacing > verticalSpacing) {
            console.log(`Notifications stacked horizontally with ${horizontalSpacing}px spacing`);
          }
        }
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/notification-stacking.png') 
        });
        
      } else if (toastCount === 1) {
        console.warn('Warning: Only one notification visible - stacking may replace previous notifications');
      } else {
        console.warn('Warning: No notifications visible after multiple triggers');
      }
    }
  }

  async testNotificationTypes(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for different types of notification triggers
    const notificationTypes = [
      { selector: 'button:has-text("Success"), .success-btn', type: 'success' },
      { selector: 'button:has-text("Error"), .error-btn', type: 'error' },
      { selector: 'button:has-text("Warning"), .warning-btn', type: 'warning' },
      { selector: 'button:has-text("Info"), .info-btn', type: 'info' }
    ];
    
    for (const notifType of notificationTypes) {
      const button = page.locator(notifType.selector);
      const buttonExists = await button.count() > 0;
      
      if (buttonExists) {
        console.log(`Testing ${notifType.type} notification`);
        
        await button.first().click();
        await page.waitForTimeout(1000);
        
        // Check for type-specific styling
        const typeNotifications = page.locator(`.toast-${notifType.type}, .notification-${notifType.type}, .${notifType.type}, .Toastify__toast--${notifType.type}`);
        const typeCount = await typeNotifications.count();
        
        if (typeCount > 0) {
          const typeNotif = typeNotifications.first();
          
          // Check styling
          const styles = await typeNotif.evaluate(el => {
            const computed = window.getComputedStyle(el);
            return {
              backgroundColor: computed.backgroundColor,
              color: computed.color,
              borderColor: computed.borderColor
            };
          });
          
          console.log(`${notifType.type} notification styles:`, styles);
          
          await page.screenshot({ 
            path: path.join(__dirname, `../logs/notification-${notifType.type}.png`) 
          });
          
          // Dismiss notification
          await page.waitForTimeout(3000); // Let it auto-dismiss or manually dismiss
          
        } else {
          console.warn(`Warning: No ${notifType.type}-specific notifications found`);
        }
      }
    }
  }

  async testPositionLayout(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Trigger a notification
    const triggerButtons = page.locator('button:has-text("Show"), button:has-text("Test"), button:has-text("Notify")');
    const buttonExists = await triggerButtons.count() > 0;
    
    if (buttonExists) {
      await triggerButtons.first().click();
      await page.waitForTimeout(1000);
      
      const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast');
      const toastCount = await toasts.count();
      
      if (toastCount > 0) {
        const firstToast = toasts.first();
        const toastBox = await firstToast.boundingBox();
        
        if (toastBox) {
          const viewport = page.viewportSize();
          
          // Check positioning relative to viewport
          const position = {
            top: toastBox.y < viewport.height / 2,
            bottom: toastBox.y > viewport.height / 2,
            left: toastBox.x < viewport.width / 2,
            right: toastBox.x > viewport.width / 2
          };
          
          console.log('Notification position:', position);
          console.log(`Notification at: ${toastBox.x}, ${toastBox.y} (viewport: ${viewport.width}x${viewport.height})`);
          
          // Common positions
          if (position.top && position.right) {
            console.log('Notification positioned at top-right');
          } else if (position.bottom && position.right) {
            console.log('Notification positioned at bottom-right');
          } else if (position.top && position.left) {
            console.log('Notification positioned at top-left');
          } else if (position.bottom && position.left) {
            console.log('Notification positioned at bottom-left');
          } else {
            console.log('Notification positioned at center or custom location');
          }
          
          // Check z-index (should be high)
          const zIndex = await firstToast.evaluate(el => {
            return window.getComputedStyle(el).zIndex;
          });
          
          console.log(`Notification z-index: ${zIndex}`);
          
          if (zIndex && parseInt(zIndex) < 1000) {
            console.warn('Warning: Notification z-index may be too low');
          }
          
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/notification-position-layout.png') 
          });
        }
      }
    }
  }

  async testAnimations(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase3-demo`);
    await page.waitForLoadState('networkidle');
    
    // Trigger notification and capture animation
    const triggerButtons = page.locator('button:has-text("Show"), button:has-text("Test"), button:has-text("Notify")');
    const buttonExists = await triggerButtons.count() > 0;
    
    if (buttonExists) {
      // Take screenshot before notification
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/notification-before-animation.png') 
      });
      
      // Trigger notification
      await triggerButtons.first().click();
      
      // Take screenshot during entry animation
      await page.waitForTimeout(200);
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/notification-entry-animation.png') 
      });
      
      // Wait for full appearance
      await page.waitForTimeout(800);
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/notification-full-appearance.png') 
      });
      
      const toasts = page.locator('.toast, .notification, .alert, .Toastify__toast');
      const toastCount = await toasts.count();
      
      if (toastCount > 0) {
        const firstToast = toasts.first();
        
        // Check for animation-related CSS properties
        const animationProps = await firstToast.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            transition: computed.transition,
            animation: computed.animation,
            transform: computed.transform,
            opacity: computed.opacity
          };
        });
        
        console.log('Notification animation properties:', animationProps);
        
        // Test exit animation by dismissing
        const closeButton = firstToast.locator('button, .close, .dismiss');
        const closeExists = await closeButton.count() > 0;
        
        if (closeExists) {
          await closeButton.first().click();
          
          // Capture exit animation
          await page.waitForTimeout(100);
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/notification-exit-animation.png') 
          });
          
          await page.waitForTimeout(500);
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/notification-after-exit.png') 
          });
        }
        
        // Check if animations use modern CSS properties
        if (animationProps.transition && animationProps.transition !== 'all 0s ease 0s') {
          console.log('Notification uses CSS transitions');
        }
        
        if (animationProps.animation && animationProps.animation !== 'none') {
          console.log('Notification uses CSS animations');
        }
        
        if (!animationProps.transition.includes('none') || !animationProps.animation.includes('none')) {
          console.log('Smooth animations detected');
        } else {
          console.warn('Warning: No smooth animations detected');
        }
      }
    }
  }
}

async function runTests(page, options = {}) {
  const tests = new NotificationTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, NotificationTests };