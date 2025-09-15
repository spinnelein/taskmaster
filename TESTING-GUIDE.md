# TaskMaster UI Testing Guide

Comprehensive test suite for validating Phase 1-3 UI upgrades and identifying broken functionality.

## Overview

This testing suite uses Playwright to automatically test all UI improvements implemented in TaskMaster's recent upgrades:

- **Phase 1**: Modal system with enhanced forms
- **Phase 2**: Multi-layer calendar with drag-and-drop
- **Phase 3**: Dashboard widgets with command palette

## Quick Start

```bash
# Install dependencies
cd frontend
npm install

# Run comprehensive test suite
npm run test:all

# Run with visible browser (for debugging)
npm run test:headed

# Run specific test categories
npm run test:integration    # Backend connectivity & workflows
npm run test:modal          # Modal system functionality
npm run test:forms          # Form components & validation
npm run test:widgets        # Dashboard widgets
```

## Test Categories

### 1. Modal System Tests (`test:modal`)
Tests the enhanced modal system with 90vh height constraints and focus management.

**What it tests:**
- Modal opening/closing (ESC, backdrop click, buttons)
- Height constraints (90vh limit prevents scrolling issues)
- Focus trap and keyboard navigation
- WCAG 2.1 AA accessibility compliance
- Responsive behavior across screen sizes
- Multiple modal types (task, event, initiative creation)

**Key files tested:**
- `frontend/src/components/common/Modal.jsx`
- Modal implementations in various forms

### 2. Form Component Tests (`test:forms`)
Validates reusable form components and progressive disclosure functionality.

**What it tests:**
- FormGrid responsive layout behavior
- FormField rendering and validation
- Progressive disclosure (collapsible sections)
- PriorityMatrix interactive selection
- Data persistence during modal interactions
- Required field validation
- Input type support (text, email, date, select, etc.)
- Form responsiveness across devices

**Key files tested:**
- `frontend/src/components/common/FormComponents.jsx`
- Form implementations in task/event/initiative creation

### 3. Dashboard Widget Tests (`test:widgets`)
Tests the customizable widget dashboard with drag-and-drop functionality.

**What it tests:**
- Widget grid rendering and layout
- TodaysFocusWidget API integration and data display
- CalendarSnapshotWidget upcoming events display
- @dnd-kit drag-and-drop widget reordering
- Widget loading states and error handling
- Widget interactions and navigation
- Responsive widget layout
- Widget customization options

**Key files tested:**
- `frontend/src/components/dashboard/DashboardGrid.jsx`
- `frontend/src/components/dashboard/widgets/TodaysFocusWidget.jsx`
- `frontend/src/components/dashboard/widgets/CalendarSnapshotWidget.jsx`

### 4. Command Palette Tests (`test:palette`)
Validates the global Cmd+K/Ctrl+K command palette with fuzzy search.

**What it tests:**
- Keyboard shortcut activation (Cmd+K/Ctrl+K)
- Palette opening and closing behavior
- Search functionality and fuzzy matching
- Navigation command execution
- Focus management and keyboard navigation
- ESC key handling
- Recent commands functionality

**Key files tested:**
- `frontend/src/components/navigation/CommandPalette.jsx`
- `frontend/src/hooks/useCommandPalette.js`

### 5. Calendar Layer Tests (`test:calendar`)
Tests the multi-layer calendar with drag-and-drop and natural language parsing.

**What it tests:**
- 5-layer system (events, tasks, meals, personal, work)
- Time axis display and navigation
- Event block rendering and positioning
- Drag-and-drop event movement
- Event resizing functionality
- Quick event creation with natural language
- Conflict detection between overlapping events
- Timeline navigation and scrolling

**Key files tested:**
- `frontend/src/components/schedule/MultiLayerCalendar.jsx`
- `frontend/src/components/schedule/DragDropCalendarLayer.jsx`
- `frontend/src/components/schedule/QuickEventModal.jsx`

### 6. Notification Tests (`test:notifications`)
Validates smart toast notifications with actions and auto-dismiss.

**What it tests:**
- Toast notification display and positioning
- Auto-dismiss functionality (timing)
- Manual dismiss with close buttons
- Progress bar notifications
- Action button functionality
- Multiple notification stacking
- Notification types (success, error, warning, info)
- Animation and transition effects

**Key files tested:**
- `frontend/src/components/notifications/NotificationSystem.jsx`

### 7. Integration Tests (`test:integration`) ⭐ **Most Important**
Tests cross-component functionality and real user workflows to identify broken integrations.

**What it tests:**
- **Backend API connectivity** - Critical for finding API issues
- **Page navigation flow** - Tests all routes work
- **Task CRUD operations** - End-to-end task creation/editing
- **Event CRUD operations** - End-to-end event management
- **Modal to API integration** - Forms actually submit data
- **Widget to API integration** - Widgets display real data
- **Command palette navigation** - Palette navigates correctly
- **Cross-page state persistence** - Data survives navigation
- **Error handling** - 404 pages, API failures
- **Real user workflows** - Complete user journey testing

## Usage Examples

### Quick Health Check
```bash
# Fast check of all endpoints and basic functionality
npm run test:web
```

### Find What's Broken
```bash
# Run comprehensive suite to identify issues
npm run test:all

# Debug with visible browser
npm run test:headed

# Focus on integration issues (most likely to be broken)
npm run test:integration
```

### Test Specific Components
```bash
# Test modal system after modal changes
npm run test:modal

# Test forms after form component updates
npm run test:forms

# Test widgets after dashboard changes
npm run test:widgets
```

### Debug Specific Issues
```bash
# Interactive browser debugging
npm run debug:browser http://localhost:5173/ui-demo --head

# Test with custom URL
npm run debug:browser http://localhost:5175/schedule --head
```

## Output and Results

### Log Files
All tests generate detailed logs in `/logs/` directory:
- `comprehensive-test-{timestamp}.log` - Main test execution log
- `test-report-{timestamp}.txt` - Human-readable test report
- `test-results-{timestamp}.json` - Machine-readable results

### Screenshots
Visual evidence captured for each test scenario:
- `modal-test-initial.png` - Modal system screenshots
- `form-grid-layout.png` - Form layout validation
- `dashboard-grid-rendering.png` - Widget layout verification
- `notification-stacking.png` - Notification behavior
- `integration-user-workflow.png` - End-to-end workflows

### Success Criteria
- **Green Tests**: All functionality working as designed
- **Yellow Warnings**: Functionality works but with issues (missing features, suboptimal UX)
- **Red Failures**: Broken functionality that needs immediate attention

## Common Issues Found

Based on the comprehensive test design, these are likely issues to be identified:

### High Priority (Test Failures)
- **API Integration Broken**: Modal forms don't submit to backend
- **Navigation Issues**: Routes don't work or return 404
- **Widget Data Loading**: Widgets show loading forever or error states
- **Modal System Broken**: Modals don't open, don't close, or break focus
- **Form Validation Issues**: Forms submit without validation or show errors incorrectly

### Medium Priority (Test Warnings)
- **Accessibility Issues**: Missing ARIA labels, poor focus management
- **Responsive Problems**: Components break on mobile/tablet
- **Animation Issues**: Transitions not smooth or missing entirely
- **Search Functionality**: Command palette search returns no results
- **Drag and Drop Issues**: Calendar drag-and-drop doesn't work properly

### Low Priority (Nice to Have)
- **Performance Issues**: Slow loading, unoptimized rendering
- **UX Polish**: Missing feedback states, confusing interactions
- **Feature Completeness**: Partially implemented features

## Prerequisites

1. **Backend Running**: Tests assume backend API on port 8000
2. **Frontend Running**: Tests assume frontend dev server on port 5173
3. **Playwright Installed**: `npx playwright install chromium`
4. **Dependencies Updated**: `npm install` in frontend directory

## Troubleshooting

### Tests Won't Start
```bash
# Check Playwright installation
npx playwright install chromium

# Verify servers are running
curl http://localhost:8000/health    # Backend
curl http://localhost:5173           # Frontend
```

### All Tests Fail
```bash
# Check basic connectivity first
npm run test:web

# Start servers if needed
python dev.py                       # Start both backend and frontend
```

### Specific Test Categories Fail
```bash
# Run individual test with visible browser for debugging
npm run test:modal -- --head
npm run test:integration -- --head
```

### Debug Specific Pages
```bash
# Test specific URL with browser debugging
npm run debug:browser http://localhost:5173/ui-demo --head
```

## Development Workflow

1. **After UI Changes**: Run `npm run test:comprehensive` to catch regressions
2. **Before Commits**: Run `npm run test:integration` to verify end-to-end functionality
3. **When Debugging**: Use `npm run test:headed` to see tests run in browser
4. **Component Development**: Run specific test category (e.g., `npm run test:forms`)

## Continuous Integration

The test suite is designed to be run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run UI Tests
  run: |
    cd frontend
    npm run test:all
  continue-on-error: false  # Fail build if tests fail
```

## Advanced Usage

### Custom Test Runs
```bash
# Test with custom base URL
node scripts/comprehensive-ui-tests.js --url=http://localhost:5175

# Verbose output
node scripts/comprehensive-ui-tests.js --verbose

# Record videos
node scripts/comprehensive-ui-tests.js --recordVideo
```

### Extending Tests
The test framework is modular. Add new test categories by:
1. Creating new test file following existing patterns
2. Adding it to `comprehensive-ui-tests.js` imports
3. Adding npm script in `package.json`

## Summary

This comprehensive test suite will systematically validate all Phase 1-3 UI upgrades and identify:
- **Broken functionality** requiring immediate fixes
- **Integration issues** between components and APIs
- **Accessibility problems** affecting user experience
- **Responsive design issues** across different devices
- **Performance bottlenecks** in the user interface

Run `npm run test:all` to get a complete health check of the UI upgrade status.