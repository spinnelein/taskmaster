// Test Series Management Integration - Final Test
// NO EMOJIS
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://localhost:5173';

// Ensure logs directory exists
try {
  fs.mkdirSync(path.resolve('./logs'), { recursive: true });
} catch (e) {
  // Directory might already exist
}

async function testSeriesManagement() {
  const logFile = `logs/series-final-${Date.now()}.log`;
  const logs = [];
  
  function log(level, message) {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] ${level.padEnd(7)} | ${message}`;
    console.log(logEntry);
    logs.push(logEntry);
  }

  const browser = await chromium.launch({ 
    headless: false,
    args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
  });
  const page = await browser.newPage();
  
  // Capture console logs
  page.on('console', msg => log('CONSOLE', `${msg.type().toUpperCase()}: ${msg.text()}`));
  page.on('pageerror', error => log('ERROR', `PAGE ERROR: ${error.message}`));

  try {
    log('INFO', 'Testing final series management integration...');
    
    // Navigate to schedule page
    log('INFO', 'Navigating to schedule page...');
    await page.goto(`${BASE_URL}/schedule`, { waitUntil: 'networkidle' });
    
    // Wait for events to load
    log('INFO', 'Waiting for events to load (8 seconds)...');
    await page.waitForTimeout(8000);
    
    // Take screenshot of loaded calendar
    await page.screenshot({ path: 'logs/final-calendar-loaded.png', fullPage: true });
    log('INFO', 'Screenshot saved: final-calendar-loaded.png');
    
    // Look for FullCalendar events
    const eventElements = await page.$$('.fc-event');
    log('INFO', `Found ${eventElements.length} events on calendar`);
    
    // Also check for any error messages
    const errorMessages = await page.$$('.error, .text-red-600, .bg-red-50');
    if (errorMessages.length > 0) {
      log('WARNING', `Found ${errorMessages.length} potential error elements`);
    }
    
    if (eventElements.length > 0) {
      log('INFO', 'Clicking on first event to test series management...');
      
      // Get event title before clicking
      const eventTitle = await eventElements[0].textContent();
      log('INFO', `Clicking event: "${eventTitle}"`);
      
      // Click on the first event
      await eventElements[0].click();
      await page.waitForTimeout(2000);
      
      // Take screenshot after click
      await page.screenshot({ path: 'logs/final-after-click.png', fullPage: true });
      log('INFO', 'Screenshot saved: final-after-click.png');
      
      // Check for any modal that opened (generic selector)
      const modals = await page.$$('.modal, [role="dialog"], .fixed.inset-0, .relative.z-50');
      log('INFO', `Found ${modals.length} potential modal elements`);
      
      // Check for series management specific content
      const seriesContent = await page.$$('text=Series Overview');
      const seriesButtons = await page.$$('text=Delete Entire Series');
      
      if (seriesContent.length > 0 || seriesButtons.length > 0) {
        log('SUCCESS', 'Series management modal appears to be working!');
        log('INFO', `Series content elements: ${seriesContent.length}`);
        log('INFO', `Series buttons: ${seriesButtons.length}`);
        
        // Take screenshot of successful modal
        await page.screenshot({ path: 'logs/final-series-success.png', fullPage: true });
        log('INFO', 'Screenshot saved: final-series-success.png');
        
        // Try to close modal by clicking outside or finding close button
        const closeButtons = await page.$$('button:has-text("Close"), [aria-label="Close"], .close, .modal-close');
        if (closeButtons.length > 0) {
          await closeButtons[0].click();
          log('INFO', 'Closed modal successfully');
        }
      } else {
        log('INFO', 'No series management content found - checking what opened...');
        
        // Log what elements are visible
        const visibleText = await page.evaluate(() => {
          const elements = document.querySelectorAll('.modal, [role="dialog"], .fixed');
          return Array.from(elements).map(el => el.textContent?.substring(0, 100)).filter(Boolean);
        });
        log('INFO', `Visible modal content: ${JSON.stringify(visibleText)}`);
      }
    } else {
      log('WARNING', 'No events found on calendar - checking for loading or error states');
      
      // Check for loading indicators
      const loadingElements = await page.$$('text=Loading, .loading, .spinner');
      log('INFO', `Loading indicators: ${loadingElements.length}`);
      
      // Check page content
      const pageContent = await page.textContent('body');
      log('INFO', `Page contains "Schedule": ${pageContent.includes('Schedule')}`);
      log('INFO', `Page contains "events": ${pageContent.toLowerCase().includes('events')}`);
    }
    
    log('SUCCESS', 'Series management integration test completed');
    
  } catch (error) {
    log('ERROR', `Test failed: ${error.message}`);
    log('ERROR', `Stack trace: ${error.stack}`);
  } finally {
    await browser.close();
    
    // Save logs
    fs.writeFileSync(logFile, logs.join('\n'));
    log('INFO', `Logs saved to: ${logFile}`);
  }
}

testSeriesManagement().catch(console.error);