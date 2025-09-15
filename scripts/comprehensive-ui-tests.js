// Comprehensive UI Test Suite for TaskMaster
// Tests all Phase 1-3 UI upgrades and identifies broken functionality
// NO EMOJIS

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Test modules
const modalSystemTests = require('./modal-system-tests');
const formComponentTests = require('./form-component-tests');
const dashboardWidgetTests = require('./dashboard-widget-tests');
const commandPaletteTests = require('./command-palette-tests');
const calendarLayerTests = require('./calendar-layer-tests');
const notificationTests = require('./notification-tests');
const integrationTests = require('./integration-tests');

// Ensure logs directory exists
const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

class UITestSuite {
  constructor(options = {}) {
    this.options = {
      headless: options.headless !== false,
      timeout: options.timeout || 30000,
      baseUrl: options.baseUrl || 'http://localhost:5173',
      verbose: options.verbose || false,
      screenshotOnFailure: options.screenshotOnFailure !== false,
      ...options
    };
    
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      skippedTests: 0,
      errors: [],
      testResults: {},
      startTime: null,
      endTime: null
    };
    
    this.logFile = path.join(logsDir, `comprehensive-test-${Date.now()}.log`);
  }

  log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level}] ${message}`;
    
    console.log(logEntry);
    fs.appendFileSync(this.logFile, logEntry + '\n');
  }

  async setupBrowser() {
    this.log('Setting up browser context');
    
    this.browser = await chromium.launch({
      headless: this.options.headless,
      devtools: !this.options.headless
    });
    
    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      // Capture console logs and errors
      recordVideo: this.options.recordVideo ? { 
        dir: path.join(logsDir, 'videos') 
      } : undefined
    });
    
    this.page = await this.context.newPage();
    
    // Capture console logs
    this.page.on('console', msg => {
      this.log(`CONSOLE ${msg.type().toUpperCase()}: ${msg.text()}`, 'CONSOLE');
    });
    
    // Capture page errors
    this.page.on('pageerror', err => {
      this.log(`PAGE ERROR: ${err.message}`, 'ERROR');
      this.results.errors.push({
        type: 'page-error',
        message: err.message,
        stack: err.stack
      });
    });
    
    // Capture network failures
    this.page.on('response', response => {
      if (response.status() >= 400) {
        this.log(`HTTP ${response.status()}: ${response.url()}`, 'WARNING');
      }
    });
  }

  async teardownBrowser() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  async runTest(testName, testFunction) {
    this.results.totalTests++;
    this.log(`Running test: ${testName}`);
    
    try {
      const startTime = Date.now();
      await testFunction(this.page, this.options);
      const duration = Date.now() - startTime;
      
      this.results.passedTests++;
      this.results.testResults[testName] = { 
        status: 'PASSED', 
        duration,
        timestamp: new Date().toISOString()
      };
      
      this.log(`Test PASSED: ${testName} (${duration}ms)`, 'SUCCESS');
      
    } catch (error) {
      this.results.failedTests++;
      this.results.testResults[testName] = { 
        status: 'FAILED', 
        error: error.message,
        timestamp: new Date().toISOString()
      };
      
      this.log(`Test FAILED: ${testName} - ${error.message}`, 'ERROR');
      
      // Take screenshot on failure
      if (this.options.screenshotOnFailure) {
        const screenshotPath = path.join(logsDir, `failure-${testName}-${Date.now()}.png`);
        await this.page.screenshot({ path: screenshotPath });
        this.log(`Failure screenshot saved: ${screenshotPath}`);
      }
      
      this.results.errors.push({
        test: testName,
        message: error.message,
        stack: error.stack
      });
    }
  }

  async runAllTests() {
    this.results.startTime = new Date();
    this.log('Starting comprehensive UI test suite');
    
    try {
      await this.setupBrowser();
      
      // Test categories in order of priority
      const testSuites = [
        { name: 'Modal System', tests: modalSystemTests },
        { name: 'Form Components', tests: formComponentTests },
        { name: 'Dashboard Widgets', tests: dashboardWidgetTests },
        { name: 'Command Palette', tests: commandPaletteTests },
        { name: 'Calendar Layers', tests: calendarLayerTests },
        { name: 'Notifications', tests: notificationTests },
        { name: 'Integration', tests: integrationTests }
      ];
      
      for (const suite of testSuites) {
        this.log(`\n=== Starting ${suite.name} Tests ===`);
        
        if (suite.tests && typeof suite.tests.runTests === 'function') {
          try {
            const suiteResults = await suite.tests.runTests(this.page, this.options);
            
            // Merge results
            if (suiteResults) {
              this.results.totalTests += suiteResults.totalTests || 0;
              this.results.passedTests += suiteResults.passedTests || 0;
              this.results.failedTests += suiteResults.failedTests || 0;
              
              // Merge individual test results
              Object.assign(this.results.testResults, suiteResults.testResults || {});
            }
            
          } catch (suiteError) {
            this.log(`Suite ${suite.name} failed: ${suiteError.message}`, 'ERROR');
            this.results.errors.push({
              suite: suite.name,
              message: suiteError.message,
              stack: suiteError.stack
            });
          }
        } else {
          this.log(`Suite ${suite.name} not implemented yet`, 'WARNING');
          this.results.skippedTests++;
        }
      }
      
    } finally {
      await this.teardownBrowser();
    }
    
    this.results.endTime = new Date();
    await this.generateReport();
  }

  async generateReport() {
    const duration = this.results.endTime - this.results.startTime;
    const successRate = (this.results.passedTests / this.results.totalTests * 100).toFixed(2);
    
    const report = `
=== COMPREHENSIVE UI TEST RESULTS ===

Execution Time: ${duration}ms
Total Tests: ${this.results.totalTests}
Passed: ${this.results.passedTests}
Failed: ${this.results.failedTests}  
Skipped: ${this.results.skippedTests}
Success Rate: ${successRate}%

=== FAILED TESTS ===
${Object.entries(this.results.testResults)
  .filter(([_, result]) => result.status === 'FAILED')
  .map(([testName, result]) => `- ${testName}: ${result.error}`)
  .join('\n')}

=== ERRORS ENCOUNTERED ===
${this.results.errors.map(error => `- ${error.message || error.test}`).join('\n')}

Full logs: ${this.logFile}
`;

    this.log(report);
    
    // Save detailed report
    const reportPath = path.join(logsDir, `test-report-${Date.now()}.txt`);
    fs.writeFileSync(reportPath, report);
    fs.writeFileSync(
      path.join(logsDir, `test-results-${Date.now()}.json`), 
      JSON.stringify(this.results, null, 2)
    );
    
    this.log(`Detailed report saved: ${reportPath}`);
    
    return this.results;
  }
}

// CLI execution
async function main() {
  const args = process.argv.slice(2);
  
  const options = {
    headless: !args.includes('--head'),
    verbose: args.includes('--verbose'),
    baseUrl: args.find(arg => arg.startsWith('--url='))?.split('=')[1] || 'http://localhost:5173'
  };
  
  console.log('Starting TaskMaster Comprehensive UI Test Suite');
  console.log(`Options: ${JSON.stringify(options, null, 2)}`);
  
  const testSuite = new UITestSuite(options);
  const results = await testSuite.runAllTests();
  
  // Exit with error code if tests failed
  process.exit(results.failedTests > 0 ? 1 : 0);
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { UITestSuite };