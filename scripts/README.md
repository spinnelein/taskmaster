# TaskMaster Testing and Debugging Scripts

This directory contains scripts for testing and debugging the TaskMaster web application using both simple HTTP requests and full browser automation with Playwright.

## Available Scripts

### 1. Simple Web Testing (`simple-web-test.js`)

A lightweight testing script that doesn't require browser installation. Tests website accessibility and API endpoints.

**Usage:**
```bash
# Run directly
node scripts/simple-web-test.js

# Or via npm script
cd frontend && npm run test:web
```

**What it tests:**
- All main routes (/, /ui-demo, /tasks, /events, /schedule)
- API endpoints (/health, /api/tasks, /api/events) 
- HTTP status codes and response types
- Basic HTML structure validation

### 2. Browser Debug Script (`browser-debug.js`)

Full browser automation using Playwright for detailed debugging and interaction testing.

**Prerequisites:**
```bash
# Install Chromium (if not already done)
cd frontend && npx playwright install chromium
```

**Usage:**
```bash
# Headless mode (default)
node scripts/browser-debug.js http://localhost:5175/ui-demo

# With visible browser
node scripts/browser-debug.js http://localhost:5175/ui-demo --head

# Or via npm script
cd frontend && npm run debug:browser
```

**Features:**
- Console log capture
- Network request/response monitoring
- JavaScript error detection
- Screenshot capability
- Custom actions (click, fill, wait, etc.)

### 3. UI Demo Testing (`test-ui-demo.js`)

Automated testing specifically for the UI Demo page with predefined user interactions.

**Usage:**
```bash
# Run the UI test
node scripts/test-ui-demo.js

# Or via npm script  
cd frontend && npm run test:ui
```

**Test actions:**
1. Takes initial screenshot
2. Opens task creation modal
3. Fills form fields
4. Takes screenshots at each step
5. Tests modal closing
6. Repeats for event creation modal

## Output Files

All scripts generate output in the `logs/` directory:

- **Browser logs**: `browser-console-{timestamp}.log`
- **Screenshots**: `ui-demo-initial.png`, `task-modal-open.png`, etc.
- **Error logs**: JavaScript errors and network failures

## Development Workflow

### Quick Health Check
```bash
cd frontend && npm run test:web
```

### Full UI Testing
```bash
cd frontend && npm run test:ui
```

### Interactive Debugging
```bash
cd frontend && npm run debug:browser -- --head
```

## Troubleshooting

### Common Issues

**1. Playwright not installed:**
```bash
cd frontend && npx playwright install chromium
```

**2. Servers not running:**
```bash
# Start frontend (port 5175)
cd frontend && npm run dev

# Start backend (port 8000) 
python dev.py backend
```

**3. Port conflicts:**
Check the simple web test output - it will show which endpoints are accessible.

### Browser Debug Features

The browser debug script captures:

- **Console logs**: All console.log, console.error, console.warn messages
- **Page errors**: JavaScript runtime errors with stack traces  
- **Network failures**: Failed HTTP requests with error details
- **HTTP errors**: 4xx/5xx responses with URLs
- **Performance**: Page load timing and network idle detection

### Custom Actions

You can extend the browser debug script with custom actions:

```javascript
const actions = [
  { type: 'click', selector: 'button.primary', description: 'Click main button' },
  { type: 'fill', selector: 'input[name="title"]', value: 'Test Task' },
  { type: 'screenshot', path: 'custom-screenshot.png' },
  { type: 'wait', duration: 2000 },
  { type: 'evaluate', script: 'return document.title' }
];
```

## Integration with Development

These scripts are designed to complement the existing development workflow:

1. **Development**: Use `npm run dev` and `python dev.py`
2. **Quick Check**: `npm run test:web` before committing
3. **UI Testing**: `npm run test:ui` after UI changes
4. **Deep Debug**: `npm run debug:browser -- --head` for complex issues

The scripts work with the existing:
- TaskMaster API on port 8000
- Vite dev server on port 5175  
- Modal system and form components
- React Router routing

## Future Enhancements

Potential additions to the testing suite:

- **E2E test suites** for complete user workflows
- **Visual regression testing** with screenshot comparison
- **Performance testing** with Lighthouse integration
- **Accessibility testing** with axe-core
- **Cross-browser testing** (Firefox, WebKit)
- **Mobile device simulation**