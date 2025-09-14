# TaskMaster Changelog

## [September 14, 2025] - UI/UX Overhaul & Development Improvements

### Added

#### Phase 1: Modal System & Forms
- **Modal Component** (`Modal.jsx`): 90vh height limit solving form scrolling issues
- **Form Components Library** (`FormComponents.jsx`): Reusable components including:
  - FormGrid with responsive columns
  - FormField with consistent styling
  - FormSection with collapsible support
  - PriorityMatrix for urgency/importance selection
  - DurationSelect with preset options
- **Enhanced Forms**: TaskForm and EventForm with progressive disclosure
- **Accessibility**: Focus trap, keyboard navigation, WCAG 2.1 AA compliance

#### Phase 2: Enhanced Scheduling Interface  
- **Multi-Layer Calendar** (`MultiLayerCalendar.jsx`): 5 distinct layers for comprehensive scheduling
- **Drag-Drop Calendar Layer** (`DragDropCalendarLayer.jsx`): Full drag-and-drop with resize handles
- **Quick Event Modal** (`QuickEventModal.jsx`): Natural language input parsing
- **Conflict Detection**: Real-time detection algorithm with visual indicators
- **Calendar Features**:
  - Drag to move events between time slots
  - Resize handles for duration adjustment
  - Click empty slots for quick creation
  - Layer-specific visibility toggles

#### Phase 3: Dashboard & Navigation
- **Dashboard Grid** (`DashboardGrid.jsx`): Customizable widget system using @dnd-kit
- **Command Palette** (`CommandPalette.jsx`): Global Cmd+K/Ctrl+K navigation
- **Notification System** (`NotificationSystem.jsx`): Smart toast notifications with:
  - Multiple types (success, error, warning, info, smart reminders, conflict alerts)
  - Action buttons with callbacks
  - Auto-dismiss with progress bars
  - Mobile-optimized layout
- **Dashboard Widgets**:
  - `TodaysFocusWidget.jsx`: Priority tasks with completion actions
  - `CalendarSnapshotWidget.jsx`: Upcoming events with time display

#### Testing Infrastructure
- **Playwright Integration**: Browser automation for UI testing
- **Test Scripts**:
  - `browser-debug.js`: Browser debugging with console capture
  - `test-ui-demo.js`: UI component validation
- **npm Scripts**: Added test:web, test:ui, debug:browser commands

#### Development Improvements
- **Enhanced dev.py**: 
  - Auto-detects actual Vite port (5173-5180)
  - `python dev.py clean` command for port cleanup
  - Process detection shows what's using each port
  - Parses Vite output to find actual running port
  - Better error handling for cmdline parsing

### Changed

#### Development Workflow
- **dev.py Enhancements**:
  - Fixed port detection to handle Vite's auto-increment behavior
  - Added process cleanup for orphaned Vite instances
  - Improved status command to show actual ports in use
  - Better cross-platform support with proper exception handling

#### Component Organization
- Reorganized components into feature-based directories:
  - `/common`: Shared components (Modal, FormComponents)
  - `/dashboard`: Dashboard-specific components and widgets
  - `/navigation`: Navigation components (CommandPalette)
  - `/notifications`: Notification system
  - `/schedule`: Calendar and scheduling components

### Fixed

- **Port Conflicts**: dev.py now properly handles cases where Vite chooses alternate ports
- **Form Height Issues**: Modal system prevents forms from being cut off on smaller screens
- **JSX Syntax Error**: Fixed extra closing tag in TaskForm.jsx
- **Process Cleanup**: Enhanced process termination to prevent port blocking

### Technical Details

#### New Dependencies
- `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`: Modern drag-and-drop
- `playwright`: Browser automation and testing
- `date-fns`: Already present, used extensively in calendar components

#### Bundle Size
- Phase 1 Build: 415 KB (Bundle remains optimized)
- Phase 2 Build: 423.79 KB (Minimal increase with calendar enhancements)
- Phase 3 Build: 502.16 KB (146.43 KB gzipped) - Acceptable for feature set

#### Performance Optimizations
- React.memo for widget components
- Efficient drag-and-drop with hardware acceleration
- Debounced keyboard input in command palette
- Optimistic UI updates for calendar operations

## [September 13, 2025] - Major System Overhaul

### Added

#### Recurring Events Master/Instance Architecture
- Industry-standard pattern similar to Google Calendar
- Database fields: `recurrence_master_id`, `is_recurrence_master`, `is_recurrence_exception`, `recurrence_instance_date`
- RecurringEventsService for managing series with edit modes
- Support for "This Only", "This and Future", "All in Series" editing

#### Weather Integration
- Dual API support: National Weather Service (free) and OpenWeatherMap (paid)
- Database caching with 3-hour refresh cycle
- Automatic suitability assessment for activities
- 7-day forecast endpoints

#### Enhanced Telegram Integration
- Event notifications when events start
- Interactive task reminders with action buttons
- Per-event notification control
- Background processing with APScheduler

### Fixed

#### Critical API Issues
- Added missing `get_by_id()` method to BaseRepository
- Fixed task completion endpoint to use proper repository pattern
- Added missing route decorators for individual resource retrieval
- Updated all validators from `@validator` to `@field_validator` (Pydantic v2)
- Fixed SQLAlchemy relationship overlaps

#### Data Cleanup
- Removed 1,093+ duplicate events from old recurring system
- Optimized Events API to show ~15 events instead of 750+

### Changed

#### API Improvements
- All endpoints now use `model_dump()` instead of deprecated `dict()`
- Proper enum conversion in repositories for string-to-enum fields
- Consistent error handling and validation

## Contributing

When adding new features or fixes, please update this changelog with:
- Date of changes
- Category (Added/Changed/Fixed/Deprecated/Removed)
- Brief description of changes
- Technical details if significant

Follow semantic versioning principles for version numbers when applicable.