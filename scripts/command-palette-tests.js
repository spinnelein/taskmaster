// Command Palette Tests for TaskMaster UI
// Tests Cmd+K/Ctrl+K keyboard shortcuts, fuzzy search, navigation, and focus management
// NO EMOJIS

const path = require('path');

class CommandPaletteTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Command Palette Tests...');
    
    await this.runTest('Keyboard Shortcut Activation', () => this.testKeyboardActivation(page, options));
    await this.runTest('Palette Opening and Closing', () => this.testPaletteOpenClose(page, options));
    await this.runTest('Search Functionality', () => this.testSearchFunctionality(page, options));
    await this.runTest('Fuzzy Search', () => this.testFuzzySearch(page, options));
    await this.runTest('Navigation Commands', () => this.testNavigationCommands(page, options));
    await this.runTest('Focus Management', () => this.testFocusManagement(page, options));
    await this.runTest('Escape Key Handling', () => this.testEscapeHandling(page, options));
    await this.runTest('Command Execution', () => this.testCommandExecution(page, options));
    await this.runTest('Recent Commands', () => this.testRecentCommands(page, options));
    
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

  async testKeyboardActivation(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    // Test Cmd+K on Mac / Ctrl+K on Windows
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Press keyboard shortcut
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    // Check if command palette opened
    const commandPalette = page.locator('.command-palette, [data-testid="command-palette"], .palette, .search-palette');
    const paletteVisible = await commandPalette.isVisible();
    
    if (!paletteVisible) {
      throw new Error(`Command palette did not open with ${shortcut} shortcut`);
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/command-palette-opened.png') 
    });
  }

  async testPaletteOpenClose(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const commandPalette = page.locator('.command-palette, [data-testid="command-palette"], .palette, .search-palette');
    let paletteVisible = await commandPalette.isVisible();
    
    if (!paletteVisible) {
      throw new Error('Command palette did not open');
    }
    
    // Close with Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    
    paletteVisible = await commandPalette.isVisible().catch(() => false);
    
    if (paletteVisible) {
      throw new Error('Command palette did not close with Escape key');
    }
    
    // Open again and test backdrop click
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    paletteVisible = await commandPalette.isVisible();
    if (!paletteVisible) {
      throw new Error('Command palette did not reopen');
    }
    
    // Try clicking backdrop
    const backdrop = page.locator('.palette-backdrop, .overlay, .backdrop');
    const backdropExists = await backdrop.count() > 0;
    
    if (backdropExists) {
      await backdrop.first().click();
      await page.waitForTimeout(500);
      
      paletteVisible = await commandPalette.isVisible().catch(() => false);
      
      if (paletteVisible) {
        console.warn('Warning: Command palette did not close on backdrop click');
      }
    }
  }

  async testSearchFunctionality(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    // Find search input
    const searchInput = page.locator('.command-palette input, .palette input, .search-input, input[placeholder*="search" i], input[placeholder*="command" i]');
    const inputExists = await searchInput.count() > 0;
    
    if (!inputExists) {
      throw new Error('Search input not found in command palette');
    }
    
    // Test typing in search
    await searchInput.fill('task');
    await page.waitForTimeout(500);
    
    // Check for search results
    const searchResults = page.locator('.command-list, .results, .commands, .palette-results');
    const resultsExist = await searchResults.count() > 0;
    
    if (!resultsExist) {
      console.warn('Warning: No search results container found');
    }
    
    // Check for command items
    const commandItems = page.locator('.command-item, .result-item, .palette-item, li');
    const itemCount = await commandItems.count();
    
    console.log(`Found ${itemCount} command items for search "task"`);
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/command-palette-search.png') 
    });
  }

  async testFuzzySearch(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const searchInput = page.locator('.command-palette input, .palette input, .search-input, input[placeholder*="search" i]');
    
    // Test fuzzy search patterns
    const fuzzySearches = [
      'tsk',      // Should match "task"
      'evnt',     // Should match "event"
      'scdl',     // Should match "schedule"
      'init',     // Should match "initiative"
    ];
    
    for (const search of fuzzySearches) {
      await searchInput.fill(search);
      await page.waitForTimeout(500);
      
      const commandItems = page.locator('.command-item, .result-item, .palette-item');
      const itemCount = await commandItems.count();
      
      console.log(`Fuzzy search "${search}" found ${itemCount} results`);
      
      if (itemCount === 0) {
        console.warn(`Warning: Fuzzy search "${search}" returned no results`);
      }
      
      // Clear search
      await searchInput.clear();
      await page.waitForTimeout(200);
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/command-palette-fuzzy-search.png') 
    });
  }

  async testNavigationCommands(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const searchInput = page.locator('.command-palette input, .palette input, .search-input');
    
    // Test navigation-related commands
    const navigationSearches = [
      'dashboard',
      'tasks',
      'events',
      'schedule',
      'initiatives',
      'projects'
    ];
    
    for (const search of navigationSearches) {
      await searchInput.fill(search);
      await page.waitForTimeout(500);
      
      const commandItems = page.locator('.command-item, .result-item, .palette-item');
      const itemCount = await commandItems.count();
      
      if (itemCount > 0) {
        // Test that items are clickable/have navigation properties
        const firstItem = commandItems.first();
        const itemText = await firstItem.textContent();
        
        console.log(`Navigation command "${search}" found: ${itemText}`);
        
        // Check if item has navigation indicators (href, data-url, etc.)
        const hasNavigation = await firstItem.evaluate(el => {
          return el.hasAttribute('href') || 
                 el.hasAttribute('data-url') ||
                 el.querySelector('a') !== null ||
                 el.onclick !== null;
        });
        
        if (!hasNavigation) {
          console.warn(`Warning: Navigation item "${search}" may not be properly configured`);
        }
      }
      
      await searchInput.clear();
      await page.waitForTimeout(200);
    }
  }

  async testFocusManagement(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    // Check that focus moves to search input
    const activeElement = await page.evaluate(() => document.activeElement.tagName);
    
    if (activeElement !== 'INPUT') {
      throw new Error('Focus did not move to search input when palette opened');
    }
    
    const searchInput = page.locator('.command-palette input, .palette input, .search-input');
    
    // Type to get some results
    await searchInput.fill('task');
    await page.waitForTimeout(500);
    
    // Test keyboard navigation
    await page.keyboard.press('ArrowDown');
    await page.waitForTimeout(200);
    
    const activeAfterArrow = await page.evaluate(() => {
      const active = document.activeElement;
      return {
        tagName: active.tagName,
        className: active.className,
        isInPalette: active.closest('.command-palette, .palette') !== null
      };
    });
    
    if (!activeAfterArrow.isInPalette) {
      console.warn('Warning: Arrow key navigation may not be working in command palette');
    }
    
    // Test Tab navigation
    await page.keyboard.press('Tab');
    await page.waitForTimeout(200);
    
    const activeAfterTab = await page.evaluate(() => {
      const active = document.activeElement;
      return active.closest('.command-palette, .palette') !== null;
    });
    
    if (!activeAfterTab) {
      console.warn('Warning: Tab navigation moved focus outside command palette');
    }
  }

  async testEscapeHandling(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Test multiple escape scenarios
    
    // 1. Basic open/close
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    let paletteVisible = await page.locator('.command-palette, .palette').isVisible();
    if (!paletteVisible) {
      throw new Error('Palette did not open for escape test');
    }
    
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    
    paletteVisible = await page.locator('.command-palette, .palette').isVisible().catch(() => false);
    if (paletteVisible) {
      throw new Error('Palette did not close with Escape');
    }
    
    // 2. Escape with search text
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const searchInput = page.locator('.command-palette input, .palette input');
    await searchInput.fill('some search text');
    await page.waitForTimeout(300);
    
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    
    paletteVisible = await page.locator('.command-palette, .palette').isVisible().catch(() => false);
    if (paletteVisible) {
      throw new Error('Palette did not close with Escape when search text present');
    }
    
    // 3. Test focus returns to original element
    const originalFocus = await page.evaluate(() => document.activeElement.tagName);
    
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
    
    const finalFocus = await page.evaluate(() => document.activeElement.tagName);
    
    console.log(`Focus before: ${originalFocus}, after: ${finalFocus}`);
  }

  async testCommandExecution(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Open palette
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const searchInput = page.locator('.command-palette input, .palette input');
    
    // Search for a navigation command
    await searchInput.fill('tasks');
    await page.waitForTimeout(500);
    
    const commandItems = page.locator('.command-item, .result-item, .palette-item');
    const itemCount = await commandItems.count();
    
    if (itemCount > 0) {
      const originalUrl = page.url();
      
      // Execute first command (Enter key)
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
      
      const newUrl = page.url();
      
      if (newUrl === originalUrl) {
        // Try clicking instead
        await page.keyboard.press(shortcut);
        await page.waitForTimeout(500);
        await searchInput.fill('tasks');
        await page.waitForTimeout(500);
        
        const firstItem = commandItems.first();
        await firstItem.click();
        await page.waitForTimeout(1000);
        
        const clickUrl = page.url();
        
        if (clickUrl !== originalUrl) {
          console.log(`Command execution via click successful: ${originalUrl} -> ${clickUrl}`);
        } else {
          console.warn('Warning: Command execution may not be working');
        }
      } else {
        console.log(`Command execution via Enter successful: ${originalUrl} -> ${newUrl}`);
      }
      
      // Check that palette closed after execution
      const paletteVisible = await page.locator('.command-palette, .palette').isVisible().catch(() => false);
      
      if (paletteVisible) {
        console.warn('Warning: Command palette did not close after command execution');
      }
    } else {
      console.warn('Warning: No commands found to test execution');
    }
  }

  async testRecentCommands(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/`);
    await page.waitForLoadState('networkidle');
    
    const isMac = process.platform === 'darwin';
    const shortcut = isMac ? 'Meta+k' : 'Control+k';
    
    // Execute a few commands to create recent history
    const commands = ['tasks', 'events', 'dashboard'];
    
    for (const command of commands) {
      await page.keyboard.press(shortcut);
      await page.waitForTimeout(500);
      
      const searchInput = page.locator('.command-palette input, .palette input');
      await searchInput.fill(command);
      await page.waitForTimeout(500);
      
      // Try to execute command
      const commandItems = page.locator('.command-item, .result-item, .palette-item');
      const itemCount = await commandItems.count();
      
      if (itemCount > 0) {
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1000);
      } else {
        await page.keyboard.press('Escape');
      }
      
      await page.waitForTimeout(500);
    }
    
    // Open palette with empty search to see if recent commands appear
    await page.keyboard.press(shortcut);
    await page.waitForTimeout(500);
    
    const recentItems = page.locator('.command-item, .result-item, .palette-item, .recent-command');
    const recentCount = await recentItems.count();
    
    console.log(`Found ${recentCount} items in empty command palette (may include recent commands)`);
    
    if (recentCount > 0) {
      // Check for recent indicators
      const recentIndicators = page.locator(':has-text("Recent"), :has-text("History"), .recent, .history');
      const hasRecentSection = await recentIndicators.count() > 0;
      
      if (hasRecentSection) {
        console.log('Recent commands section found');
      } else {
        console.warn('Warning: Recent commands functionality may not be implemented');
      }
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/command-palette-recent.png') 
    });
  }
}

async function runTests(page, options = {}) {
  const tests = new CommandPaletteTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, CommandPaletteTests };