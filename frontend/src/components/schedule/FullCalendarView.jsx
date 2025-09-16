// FullCalendar Integration Component
// NO EMOJIS
import { useState, useEffect, useCallback } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import rrulePlugin from '@fullcalendar/rrule';
import eventService from '../../services/eventService';
import { useRecurringEventEdit } from '../../hooks/useRecurringEventEdit';
import { useSeriesManagement } from '../../hooks/useSeriesManagement';
import RecurringEditModeModal from '../events/RecurringEditModeModal';
import SeriesManagementModal from '../events/SeriesManagementModal';
import { useSidebar } from '../layout/ModernLayout';
import './FullCalendarView.css';
import './ExceptionStyles.css';

function FullCalendarView() {
  const { isSidebarCollapsed } = useSidebar();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const {
    isEditModeModalOpen,
    pendingEdit,
    initiateEdit,
    handleModeSelect,
    cancelEdit
  } = useRecurringEventEdit();
  
  const {
    isSeriesModalOpen,
    selectedSeries,
    openSeriesModal,
    closeSeriesModal
  } = useSeriesManagement();

  // Load events from API using new RRULE-based expansion
  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await eventService.getEvents();
      
      // Transform and expand events for FullCalendar format
      const transformedEvents = [];
      
      // Calculate date range for expansion (show 30 days)
      const today = new Date().toISOString().split('T')[0];
      const thirtyDaysFromNow = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      // Process each master event
      for (const event of response.events) {
        const baseEvent = {
          backgroundColor: getEventColor(event),
          borderColor: getEventColor(event),
          classNames: [`priority-${event.priority || 5}`, `status-${event.status || 'scheduled'}`],
          extendedProps: {
            description: event.description,
            location: event.location,
            event_type: event.event_type,
            status: event.status,
            priority: event.priority,
            is_blocking: event.is_blocking,
            notifications_enabled: event.notifications_enabled,
            is_master: !event.is_recurring // Track if this is a master or occurrence
          }
        };
        
        if (event.is_recurring) {
          // Use new RRULE-based expansion API
          try {
            const expansionData = await eventService.getEventOccurrences(
              event.id,
              today,
              thirtyDaysFromNow,
              50 // Max occurrences to prevent overload
            );
            
            // Add each occurrence to the calendar
            expansionData.occurrences.forEach(occurrence => {
              const eventColor = occurrence.is_exception ? 
                '#f59e0b' : getEventColor(event); // Orange for exceptions
              
              transformedEvents.push({
                ...baseEvent,
                id: occurrence.id,
                title: occurrence.title,
                start: occurrence.start,
                end: occurrence.end,
                backgroundColor: eventColor,
                borderColor: eventColor,
                className: occurrence.is_exception ? 'fc-event-exception' : 'fc-event-normal',
                extendedProps: {
                  ...baseEvent.extendedProps,
                  occurrence_date: occurrence.occurrence_date,
                  is_exception: occurrence.is_exception,
                  master_event_id: occurrence.master_event_id,
                  is_master: false
                }
              });
            });
            
            console.log(`Expanded ${event.title}: ${expansionData.total_occurrences} occurrences`);
            
          } catch (expansionError) {
            console.warn(`Failed to expand ${event.title}:`, expansionError);
            // Fallback: show the master event once
            transformedEvents.push({
              ...baseEvent,
              id: event.id,
              title: `${event.title} (expansion failed)`,
              start: event.start_time,
              end: event.end_time,
              backgroundColor: '#dc2626', // Red to indicate issue
              borderColor: '#dc2626'
            });
          }
        } else {
          // Non-recurring event - add directly
          transformedEvents.push({
            ...baseEvent,
            id: event.id,
            title: event.title,
            start: event.start_time,
            end: event.end_time
          });
        }
      }
      
      console.log(`Calendar loaded: ${transformedEvents.length} total events (from ${response.events.length} masters)`);
      setEvents(transformedEvents);
      
    } catch (error) {
      console.error('Failed to load events:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Get event color based on type/layer
  const getEventColor = (event) => {
    if (event.layer === 'work') return '#06b6d4';
    if (event.layer === 'personal') return '#8b5cf6';
    if (event.layer === 'meals') return '#f59e0b';
    return '#3b82f6'; // Default events color
  };

  // Load events on component mount
  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // Handle date click for creating new events
  const handleDateClick = useCallback((info) => {
    console.log('Date clicked:', info.dateStr);
    // TODO: Open event creation modal with pre-filled date/time
  }, []);

  // Handle event click for editing
  const handleEventClick = useCallback((info) => {
    const event = info.event;
    const extendedProps = event.extendedProps;
    
    console.log('Event clicked:', event.title);
    
    // For recurring events, show series management option
    if (extendedProps.master_event_id || (!extendedProps.is_master && extendedProps.is_recurring)) {
      const eventData = {
        id: extendedProps.master_event_id || event.id,
        title: event.title,
        master_event_id: extendedProps.master_event_id,
        is_recurring: true,
        occurrence_date: extendedProps.occurrence_date
      };
      
      // Show context menu or directly open series modal
      // For now, open series modal directly for recurring events
      openSeriesModal(eventData);
    } else {
      // Regular event editing would go here
      console.log('Regular event editing not yet implemented');
      // TODO: Open regular event edit modal
    }
  }, [openSeriesModal]);

  // Handle event drag/resize
  const handleEventChange = useCallback(async (info) => {
    const event = info.event;
    const extendedProps = event.extendedProps;
    
    console.log('Event changed:', event.title);
    
    // Calculate new start/end times
    const updates = {
      start_time: event.start.toISOString(),
      end_time: event.end ? event.end.toISOString() : event.start.toISOString()
    };
    
    try {
      // Create event object for the hook
      const eventData = {
        id: extendedProps.master_event_id || event.id,
        is_recurring: !extendedProps.is_master,
        master_event_id: extendedProps.master_event_id,
        title: event.title,
        occurrence_date: extendedProps.occurrence_date
      };
      
      await initiateEdit(eventData, updates, extendedProps.occurrence_date);
      
      // Reload events after successful update
      await loadEvents();
      
    } catch (error) {
      console.error('Failed to update event:', error);
      // Revert the change in the calendar
      info.revert();
    }
  }, [initiateEdit, loadEvents]);

  // Custom event content based on duration
  const renderEventContent = useCallback((eventInfo) => {
    const event = eventInfo.event;
    const duration = event.end - event.start; // Duration in milliseconds
    const durationMinutes = duration / (1000 * 60);
    
    const title = event.title;
    const location = event.extendedProps.location;
    const eventType = event.extendedProps.event_type;
    const isException = event.extendedProps.is_exception;
    
    // Smart content based on duration
    if (durationMinutes <= 30) {
      // Short events: Title + Time only
      return (
        <div className="fc-event-content-short">
          <div className="fc-event-title-short">
            {title}
            {isException && <span className="exception-indicator"> *</span>}
          </div>
        </div>
      );
    } else if (durationMinutes <= 60) {
      // Medium events: Title + Location (if available)
      return (
        <div className="fc-event-content-medium">
          <div className="fc-event-title-medium">
            {title}
            {isException && <span className="exception-indicator"> *</span>}
          </div>
          {location && <div className="fc-event-location">{location}</div>}
        </div>
      );
    } else {
      // Long events: Title + Location + Type indicator
      return (
        <div className="fc-event-content-long">
          <div className="fc-event-title-long">
            {title}
            {isException && <span className="exception-indicator"> *</span>}
          </div>
          {location && <div className="fc-event-location">{location}</div>}
          {eventType && <div className="fc-event-type">{eventType}</div>}
        </div>
      );
    }
  }, []);

  return (
    <div className="fullcalendar-container">
      {/* Header */}
      <div className="calendar-header mb-4">
        <h1 className="text-3xl font-bold text-gray-900">Schedule</h1>
        <p className="text-gray-600 mt-2">
          {isSidebarCollapsed 
            ? 'Sidebar collapsed - more space for your calendar!' 
            : 'Manage your events, tasks, and time blocks'
          }
        </p>
      </div>

      {/* Loading indicator */}
      {loading && (
        <div className="text-center py-4">
          <div className="text-gray-600">Loading events...</div>
        </div>
      )}

      {/* FullCalendar */}
      <div className="calendar-wrapper">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, rrulePlugin]}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
          }}
          initialView="timeGridWeek"
          height="calc(100vh - 200px)"
          contentHeight="auto"
          expandRows={true}
          events={events}
          dateClick={handleDateClick}
          eventClick={handleEventClick}
          eventChange={handleEventChange}
          editable={true}
          selectable={true}
          selectMirror={true}
          dayMaxEvents={true}
          weekends={true}
          slotMinTime="06:00:00"
          slotMaxTime="24:00:00"
          slotDuration="00:15:00"
          slotLabelInterval="01:00:00"
          scrollTime="08:00:00"
          allDaySlot={false}
          eventDisplay="block"
          eventTimeFormat={{
            hour: 'numeric',
            minute: '2-digit',
            meridiem: 'short'
          }}
          slotLabelFormat={{
            hour: 'numeric',
            minute: '2-digit',
            meridiem: 'short'
          }}
          businessHours={{
            daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
            startTime: '09:00',
            endTime: '17:00'
          }}
          eventClassNames="fc-event-small-text"
          eventContent={renderEventContent}
        />
      </div>
      
      {/* Recurring Edit Mode Modal */}
      <RecurringEditModeModal
        isOpen={isEditModeModalOpen}
        onClose={cancelEdit}
        onModeSelect={handleModeSelect}
        eventTitle={pendingEdit?.event.title || ''}
        occurrenceDate={pendingEdit?.occurrenceDate || ''}
      />
      
      {/* Series Management Modal */}
      <SeriesManagementModal
        isOpen={isSeriesModalOpen}
        onClose={closeSeriesModal}
        masterEventId={selectedSeries?.masterEventId}
        eventTitle={selectedSeries?.title || ''}
        onSeriesDeleted={() => {
          // Reload events after series deletion
          loadEvents();
          closeSeriesModal();
        }}
      />
    </div>
  );
}

export default FullCalendarView;