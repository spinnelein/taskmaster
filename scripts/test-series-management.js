// Test Series Management Integration
// NO EMOJIS
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import path from 'path';

const BASE_URL = 'http://localhost:5174';

// Ensure logs directory exists
try {
  mkdirSync(path.resolve('./logs'), { recursive: true });
} catch (e) {
  // Directory might already exist
}

async function testSeriesManagement() {
  const logFile = `logs/series-test-${Date.now()}.log`;
  const logs = [];
  
  function log(level, message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${level.padEnd(7)} | ${message}`;
    console.log(logEntry);
    logs.push(logEntry);
  }

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Capture console logs
  page.on('console', msg => log('CONSOLE', `${msg.type().toUpperCase()}: ${msg.text()}`));
  page.on('pageerror', error => log('ERROR', `PAGE ERROR: ${error.message}`));

  try {
    log('INFO', 'Testing series management integration...');
    
    // Navigate to schedule page
    log('INFO', 'Navigating to schedule page...');
    await page.goto(`${BASE_URL}/schedule`, { waitUntil: 'networkidle' });
    
    // Wait for events to load
    log('INFO', 'Waiting for events to load...');
    await page.waitForTimeout(3000);
    
    // Take screenshot of loaded calendar
    await page.screenshot({ path: 'logs/series-calendar-loaded.png', fullPage: true });
    log('INFO', 'Screenshot saved: series-calendar-loaded.png');
    
    // Look for recurring events (they should have the fc-event class)
    const eventElements = await page.$$('.fc-event');
    log('INFO', `Found ${eventElements.length} events on calendar`);
    
    if (eventElements.length > 0) {
      log('INFO', 'Clicking on first event to test series management...');
      
      // Click on the first event
      await eventElements[0].click();
      await page.waitForTimeout(1000);
      
      // Take screenshot after click
      await page.screenshot({ path: 'logs/series-after-click.png', fullPage: true });
      log('INFO', 'Screenshot saved: series-after-click.png');
      
      // Check if series management modal opened
      const seriesModal = await page.$('[data-testid="modal"]');
      if (seriesModal) {
        log('SUCCESS', 'Series management modal opened!');
        
        // Look for series management content
        const modalTitle = await page.$('.modal-title');
        if (modalTitle) {
          const titleText = await modalTitle.textContent();
          log('INFO', `Modal title: ${titleText}`);
        }
        
        // Take screenshot of open modal
        await page.screenshot({ path: 'logs/series-modal-open.png', fullPage: true });
        log('INFO', 'Screenshot saved: series-modal-open.png');
        
        // Close modal
        const closeButton = await page.$('[data-testid="modal-close"]');
        if (closeButton) {
          await closeButton.click();
          log('INFO', 'Closed series modal');
        }
      } else {
        log('WARNING', 'No modal opened - might be non-recurring event or modal not implemented');
      }
    }
    
    log('SUCCESS', 'Series management test completed');
    
  } catch (error) {
    log('ERROR', `Test failed: ${error.message}`);
  } finally {
    await browser.close();
    
    // Save logs
    writeFileSync(logFile, logs.join('\n'));
    log('INFO', `Logs saved to: ${logFile}`);
  }
}

testSeriesManagement().catch(console.error);