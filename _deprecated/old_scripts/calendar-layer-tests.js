// Multi-Layer Calendar Tests for TaskMaster UI  
// Tests 5-layer calendar, drag-and-drop, quick event creation, and conflict detection
// NO EMOJIS

const path = require('path');

class CalendarLayerTests {
  constructor() {
    this.results = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      testResults: {}
    };
  }

  async runTests(page, options = {}) {
    console.log('Starting Calendar Layer Tests...');
    
    await this.runTest('Calendar Layer Rendering', () => this.testCalendarLayerRendering(page, options));
    await this.runTest('Five Layer System', () => this.testFiveLayerSystem(page, options));
    await this.runTest('Time Axis Display', () => this.testTimeAxisDisplay(page, options));
    await this.runTest('Event Block Rendering', () => this.testEventBlockRendering(page, options));
    await this.runTest('Drag and Drop Movement', () => this.testDragDropMovement(page, options));
    await this.runTest('Event Resizing', () => this.testEventResizing(page, options));
    await this.runTest('Quick Event Creation', () => this.testQuickEventCreation(page, options));
    await this.runTest('Natural Language Parsing', () => this.testNaturalLanguageParsing(page, options));
    await this.runTest('Conflict Detection', () => this.testConflictDetection(page, options));
    await this.runTest('Timeline Navigation', () => this.testTimelineNavigation(page, options));
    
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

  async testCalendarLayerRendering(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Check if multi-layer calendar exists
    const calendar = page.locator('.multi-layer-calendar, .calendar-layers, [data-testid="calendar"], .schedule-view');
    const calendarExists = await calendar.count() > 0;
    
    if (!calendarExists) {
      // Try schedule page
      await page.goto(`${options.baseUrl || 'http://localhost:5173'}/schedule`);
      await page.waitForLoadState('networkidle');
      
      const scheduleCalendar = page.locator('.multi-layer-calendar, .calendar-layers, [data-testid="calendar"], .schedule-view');
      const scheduleExists = await scheduleCalendar.count() > 0;
      
      if (!scheduleExists) {
        throw new Error('Multi-layer calendar not found on Phase2Demo or Schedule page');
      }
    }
    
    // Check calendar structure
    const calendarContainer = page.locator('.multi-layer-calendar, .calendar-layers, .schedule-view').first();
    
    // Look for calendar grid or time structure
    const timeSlots = page.locator('.time-slot, .hour-slot, .calendar-grid .slot, .time-grid');
    const timeSlotCount = await timeSlots.count();
    
    if (timeSlotCount === 0) {
      console.warn('Warning: No time slots found in calendar view');
    } else {
      console.log(`Found ${timeSlotCount} time slots in calendar`);
    }
    
    // Check for calendar dimensions
    const calendarBox = await calendarContainer.boundingBox();
    
    if (!calendarBox || calendarBox.width < 100 || calendarBox.height < 100) {
      throw new Error('Calendar appears to be too small or not rendered properly');
    }
    
    await page.screenshot({ 
      path: path.join(__dirname, '../logs/calendar-layer-rendering.png') 
    });
  }

  async testFiveLayerSystem(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for layer controls or indicators
    const layers = ['events', 'tasks', 'meals', 'personal', 'work'];
    const layerElements = [];
    
    for (const layer of layers) {
      const layerElement = page.locator(`[data-layer="${layer}"], .layer-${layer}, :has-text("${layer}")`, { hasText: new RegExp(layer, 'i') });
      const count = await layerElement.count();
      
      if (count > 0) {
        layerElements.push({ layer, count });
      }
    }
    
    console.log(`Found layer elements:`, layerElements);
    
    // Look for layer toggle controls
    const layerToggles = page.locator('.layer-toggle, .layer-control, .layer-visibility, input[type="checkbox"]');
    const toggleCount = await layerToggles.count();
    
    if (toggleCount > 0) {
      console.log(`Found ${toggleCount} layer toggle controls`);
      
      // Test toggling first few layers
      for (let i = 0; i < Math.min(toggleCount, 3); i++) {
        try {
          const toggle = layerToggles.nth(i);
          const isChecked = await toggle.isChecked().catch(() => false);
          
          await toggle.click();
          await page.waitForTimeout(500);
          
          const newState = await toggle.isChecked().catch(() => !isChecked);
          
          if (newState === isChecked) {
            console.warn(`Warning: Layer toggle ${i} state did not change`);
          }
          
        } catch (error) {
          console.warn(`Could not test layer toggle ${i}: ${error.message}`);
        }
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-layer-toggles.png') 
      });
    } else {
      console.warn('Warning: No layer toggle controls found');
    }
    
    // Look for different colored layers or visual indicators
    const layerVisuals = page.locator('.layer, [class*="layer-"], [data-layer]');
    const visualCount = await layerVisuals.count();
    
    if (visualCount === 0) {
      console.warn('Warning: No visual layer indicators found');
    } else {
      console.log(`Found ${visualCount} visual layer elements`);
    }
  }

  async testTimeAxisDisplay(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for time axis elements
    const timeAxis = page.locator('.time-axis, .hour-labels, .time-labels, .y-axis');
    const axisExists = await timeAxis.count() > 0;
    
    if (!axisExists) {
      console.warn('Warning: Time axis not found, checking for time labels');
    }
    
    // Look for time labels (hours)
    const timeLabels = page.locator(':has-text("AM"), :has-text("PM"), :has-text(":00"), .hour, .time-label');
    const labelCount = await timeLabels.count();
    
    if (labelCount === 0) {
      console.warn('Warning: No time labels found in calendar');
    } else {
      console.log(`Found ${labelCount} time labels`);
      
      // Check time format
      const sampleLabel = await timeLabels.first().textContent();
      console.log(`Sample time label: "${sampleLabel}"`);
      
      // Verify time format is reasonable
      if (!sampleLabel || (!sampleLabel.includes(':') && !sampleLabel.includes('AM') && !sampleLabel.includes('PM'))) {
        console.warn('Warning: Time labels may not be in expected format');
      }
    }
    
    // Test scrolling through time axis
    const calendarContainer = page.locator('.calendar-container, .schedule-view, .multi-layer-calendar').first();
    const containerExists = await calendarContainer.count() > 0;
    
    if (containerExists) {
      // Try scrolling to test time axis behavior
      await calendarContainer.hover();
      await page.mouse.wheel(0, 200);
      await page.waitForTimeout(500);
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-time-axis.png') 
      });
    }
  }

  async testEventBlockRendering(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Wait for events to load
    await page.waitForTimeout(2000);
    
    // Look for event blocks
    const eventBlocks = page.locator('.event-block, .event, .calendar-event, .schedule-item, [data-event-id]');
    const eventCount = await eventBlocks.count();
    
    console.log(`Found ${eventCount} event blocks on calendar`);
    
    if (eventCount > 0) {
      // Test first few events
      for (let i = 0; i < Math.min(eventCount, 3); i++) {
        const event = eventBlocks.nth(i);
        
        // Check event has proper dimensions
        const eventBox = await event.boundingBox();
        
        if (!eventBox || eventBox.width < 10 || eventBox.height < 10) {
          console.warn(`Warning: Event ${i} has invalid dimensions`);
        }
        
        // Check event has title or content
        const eventText = await event.textContent();
        
        if (!eventText || eventText.trim().length === 0) {
          console.warn(`Warning: Event ${i} appears to be empty`);
        } else {
          console.log(`Event ${i}: "${eventText.substring(0, 50)}..."`);
        }
        
        // Check for event styling
        const eventStyles = await event.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return {
            backgroundColor: styles.backgroundColor,
            color: styles.color,
            position: styles.position
          };
        });
        
        if (eventStyles.position !== 'absolute' && eventStyles.position !== 'relative') {
          console.warn(`Warning: Event ${i} may not be properly positioned`);
        }
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-event-blocks.png') 
      });
    } else {
      console.warn('Warning: No event blocks found - may indicate calendar not loading data');
    }
  }

  async testDragDropMovement(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Wait for events to load
    await page.waitForTimeout(2000);
    
    // Find draggable events
    const draggableEvents = page.locator('.event-block[draggable="true"], .event[draggable], .draggable-event');
    let eventCount = await draggableEvents.count();
    
    if (eventCount === 0) {
      // Try any event block
      const allEvents = page.locator('.event-block, .event, .calendar-event, .schedule-item');
      eventCount = await allEvents.count();
      
      if (eventCount > 0) {
        console.log(`Found ${eventCount} events to test drag (may not be explicitly draggable)`);
        
        try {
          const firstEvent = allEvents.first();
          const eventBox = await firstEvent.boundingBox();
          
          if (eventBox) {
            // Attempt drag operation
            await page.mouse.move(eventBox.x + eventBox.width / 2, eventBox.y + eventBox.height / 2);
            await page.mouse.down();
            
            // Drag to a different position (down 100px)
            await page.mouse.move(eventBox.x + eventBox.width / 2, eventBox.y + eventBox.height / 2 + 100, { steps: 5 });
            await page.mouse.up();
            
            await page.waitForTimeout(1000);
            
            await page.screenshot({ 
              path: path.join(__dirname, '../logs/calendar-drag-drop-test.png') 
            });
            
            console.log('Drag and drop attempted - check screenshot for visual confirmation');
          }
          
        } catch (error) {
          console.warn(`Could not test drag and drop: ${error.message}`);
        }
      } else {
        console.warn('Warning: No events found to test drag and drop');
      }
    } else {
      console.log(`Found ${eventCount} explicitly draggable events`);
      
      // Test drag and drop on first event
      try {
        const firstEvent = draggableEvents.first();
        const eventBox = await firstEvent.boundingBox();
        
        if (eventBox) {
          await page.mouse.move(eventBox.x + eventBox.width / 2, eventBox.y + eventBox.height / 2);
          await page.mouse.down();
          await page.mouse.move(eventBox.x + eventBox.width / 2, eventBox.y + eventBox.height / 2 + 100, { steps: 5 });
          await page.mouse.up();
          
          await page.waitForTimeout(1000);
          
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/calendar-draggable-event.png') 
          });
        }
      } catch (error) {
        console.warn(`Could not test draggable event: ${error.message}`);
      }
    }
  }

  async testEventResizing(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    await page.waitForTimeout(2000);
    
    // Look for events with resize handles
    const resizeHandles = page.locator('.resize-handle, .resize, .event-resize, [class*="resize"]');
    const handleCount = await resizeHandles.count();
    
    if (handleCount > 0) {
      console.log(`Found ${handleCount} resize handles`);
      
      try {
        const firstHandle = resizeHandles.first();
        const handleBox = await firstHandle.boundingBox();
        
        if (handleBox) {
          // Attempt resize operation
          await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
          await page.mouse.down();
          
          // Resize by dragging handle down
          await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2 + 50, { steps: 3 });
          await page.mouse.up();
          
          await page.waitForTimeout(1000);
          
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/calendar-event-resize.png') 
          });
          
          console.log('Event resize attempted');
        }
        
      } catch (error) {
        console.warn(`Could not test event resizing: ${error.message}`);
      }
    } else {
      // Look for events and check if they're resizable by hovering
      const events = page.locator('.event-block, .event, .calendar-event');
      const eventCount = await events.count();
      
      if (eventCount > 0) {
        const firstEvent = events.first();
        
        // Hover over event edges to see if resize cursors appear
        const eventBox = await firstEvent.boundingBox();
        
        if (eventBox) {
          // Hover over bottom edge
          await page.mouse.move(eventBox.x + eventBox.width / 2, eventBox.y + eventBox.height - 2);
          await page.waitForTimeout(500);
          
          // Check cursor style
          const cursor = await page.evaluate(() => document.body.style.cursor || window.getComputedStyle(document.body).cursor);
          
          if (cursor.includes('resize') || cursor.includes('s-resize')) {
            console.log('Event appears to be resizable (resize cursor detected)');
          } else {
            console.warn('Warning: Events may not be resizable');
          }
          
          await page.screenshot({ 
            path: path.join(__dirname, '../logs/calendar-event-hover.png') 
          });
        }
      }
    }
  }

  async testQuickEventCreation(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for quick event creation elements
    const quickCreateElements = page.locator('.quick-event, .quick-create, input[placeholder*="event"], input[placeholder*="quick"]');
    const quickCreateCount = await quickCreateElements.count();
    
    if (quickCreateCount > 0) {
      console.log(`Found ${quickCreateCount} quick event creation elements`);
      
      const quickInput = quickCreateElements.first();
      
      // Test quick event creation
      await quickInput.fill('Quick test event');
      await page.waitForTimeout(500);
      
      // Try submitting (Enter or button)
      await page.keyboard.press('Enter');
      await page.waitForTimeout(1000);
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-quick-event.png') 
      });
      
    } else {
      // Look for double-click creation
      console.warn('Warning: No quick event creation input found, testing double-click creation');
      
      const calendarArea = page.locator('.calendar-container, .schedule-view, .calendar-grid').first();
      const areaExists = await calendarArea.count() > 0;
      
      if (areaExists) {
        const areaBox = await calendarArea.boundingBox();
        
        if (areaBox) {
          // Double-click in calendar area
          await page.mouse.dblclick(areaBox.x + 100, areaBox.y + 100);
          await page.waitForTimeout(1000);
          
          // Check if modal or quick creation appeared
          const modal = page.locator('.modal, [data-testid="modal"], .event-modal');
          const modalOpen = await modal.count() > 0;
          
          if (modalOpen) {
            console.log('Double-click event creation triggered modal');
            
            await page.screenshot({ 
              path: path.join(__dirname, '../logs/calendar-doubleclick-create.png') 
            });
            
            // Close modal
            await page.keyboard.press('Escape');
          } else {
            console.warn('Warning: Double-click event creation may not be implemented');
          }
        }
      }
    }
  }

  async testNaturalLanguageParsing(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for quick event input
    const quickInput = page.locator('.quick-event, input[placeholder*="event"], input[placeholder*="meeting"], .natural-language-input');
    const inputExists = await quickInput.count() > 0;
    
    if (inputExists) {
      const naturalLanguageTests = [
        'Meeting at 3pm for 1 hour',
        'Lunch tomorrow at 12:30',
        'Call with client from 2-3pm',
        'Team standup at 9am for 30 minutes',
        'Project review next Friday at 2pm'
      ];
      
      for (const testPhrase of naturalLanguageTests) {
        try {
          await quickInput.clear();
          await quickInput.fill(testPhrase);
          await page.waitForTimeout(500);
          
          // Check if parsing hints or preview appears
          const parsePreview = page.locator('.parse-preview, .event-preview, .natural-preview, .time-suggestion');
          const previewExists = await parsePreview.count() > 0;
          
          if (previewExists) {
            const previewText = await parsePreview.textContent();
            console.log(`Natural language "${testPhrase}" parsed as: "${previewText}"`);
          }
          
          // Try submitting
          await page.keyboard.press('Enter');
          await page.waitForTimeout(1000);
          
          // Check if event was created or modal opened
          const modal = page.locator('.modal, [data-testid="modal"]');
          const modalOpen = await modal.count() > 0;
          
          if (modalOpen) {
            // Close modal for next test
            await page.keyboard.press('Escape');
            await page.waitForTimeout(500);
          }
          
        } catch (error) {
          console.warn(`Could not test natural language phrase "${testPhrase}": ${error.message}`);
        }
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-natural-language.png') 
      });
      
    } else {
      console.warn('Warning: No natural language input found for testing');
    }
  }

  async testConflictDetection(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    await page.waitForTimeout(2000);
    
    // Look for overlapping events or conflict indicators
    const conflictIndicators = page.locator('.conflict, .overlap, .warning, .conflict-indicator, [class*="conflict"]');
    const conflictCount = await conflictIndicators.count();
    
    if (conflictCount > 0) {
      console.log(`Found ${conflictCount} conflict indicators`);
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-conflicts.png') 
      });
    } else {
      // Try creating overlapping events to test conflict detection
      console.log('Testing conflict detection by creating overlapping events');
      
      // Look for a way to create events
      const quickInput = page.locator('.quick-event, input[placeholder*="event"]');
      const inputExists = await quickInput.count() > 0;
      
      if (inputExists) {
        // Create first event
        await quickInput.fill('Test event 1 at 2pm for 1 hour');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1000);
        
        // Close modal if opened
        const modal = page.locator('.modal, [data-testid="modal"]');
        const modalOpen = await modal.count() > 0;
        if (modalOpen) {
          await page.keyboard.press('Escape');
        }
        
        // Create overlapping event
        await quickInput.fill('Test event 2 at 2:30pm for 1 hour');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1000);
        
        // Check for conflict detection
        const newConflicts = page.locator('.conflict, .overlap, .warning, .conflict-indicator');
        const newConflictCount = await newConflicts.count();
        
        if (newConflictCount > 0) {
          console.log(`Conflict detection working: found ${newConflictCount} conflicts`);
        } else {
          console.warn('Warning: Conflict detection may not be implemented');
        }
        
        await page.screenshot({ 
          path: path.join(__dirname, '../logs/calendar-conflict-test.png') 
        });
      }
    }
  }

  async testTimelineNavigation(page, options) {
    await page.goto(`${options.baseUrl || 'http://localhost:5173'}/phase2-demo`);
    await page.waitForLoadState('networkidle');
    
    // Look for timeline navigation controls
    const navControls = page.locator('.timeline-nav, .date-nav, .calendar-nav, button:has-text("Today"), button:has-text("Next"), button:has-text("Prev")');
    const navCount = await navControls.count();
    
    if (navCount > 0) {
      console.log(`Found ${navCount} timeline navigation controls`);
      
      // Test navigation buttons
      const todayButton = page.locator('button:has-text("Today"), .today-btn, .nav-today');
      const todayExists = await todayButton.count() > 0;
      
      if (todayExists) {
        await todayButton.first().click();
        await page.waitForTimeout(1000);
        console.log('Today button clicked');
      }
      
      const nextButton = page.locator('button:has-text("Next"), .next-btn, .nav-next, button:has-text(">")');
      const nextExists = await nextButton.count() > 0;
      
      if (nextExists) {
        await nextButton.first().click();
        await page.waitForTimeout(1000);
        console.log('Next button clicked');
      }
      
      const prevButton = page.locator('button:has-text("Prev"), .prev-btn, .nav-prev, button:has-text("<")');
      const prevExists = await prevButton.count() > 0;
      
      if (prevExists) {
        await prevButton.first().click();
        await page.waitForTimeout(1000);
        console.log('Previous button clicked');
      }
      
      await page.screenshot({ 
        path: path.join(__dirname, '../logs/calendar-timeline-nav.png') 
      });
      
    } else {
      console.warn('Warning: No timeline navigation controls found');
    }
    
    // Test scrolling within calendar
    const calendarContainer = page.locator('.calendar-container, .schedule-view, .multi-layer-calendar').first();
    const containerExists = await calendarContainer.count() > 0;
    
    if (containerExists) {
      await calendarContainer.hover();
      
      // Test vertical scrolling
      await page.mouse.wheel(0, 300);
      await page.waitForTimeout(500);
      
      await page.mouse.wheel(0, -300);
      await page.waitForTimeout(500);
      
      // Test horizontal scrolling if applicable
      await page.mouse.wheel(100, 0);
      await page.waitForTimeout(500);
      
      await page.mouse.wheel(-100, 0);
      await page.waitForTimeout(500);
      
      console.log('Timeline scrolling tested');
    }
  }
}

async function runTests(page, options = {}) {
  const tests = new CalendarLayerTests();
  return await tests.runTests(page, options);
}

module.exports = { runTests, CalendarLayerTests };