// FullCalendar Integration Component
// NO EMOJIS
import { useState, useEffect, useCallback } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import rrulePlugin from '@fullcalendar/rrule';
import eventService from '../../services/eventService';
import { useSidebar } from '../layout/ModernLayout';
import './FullCalendarView.css';

function FullCalendarView() {
  const { isSidebarCollapsed } = useSidebar();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load events from API
  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      const response = await eventService.getEvents();
      
      // Transform and expand events for FullCalendar format
      const transformedEvents = [];
      
      response.events.forEach(event => {
        const baseEvent = {
          id: event.id,
          title: event.title,
          start: event.start_time,
          end: event.end_time,
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
            notifications_enabled: event.notifications_enabled
          }
        };
        
        // Handle recurring events by manually expanding them
        if (event.is_recurring && event.recurrence_pattern) {
          const pattern = event.recurrence_pattern;
          const startDate = new Date(event.start_time);
          const endDate = new Date(event.end_time);
          const duration = endDate.getTime() - startDate.getTime();
          
          // Generate instances for the next 30 days
          const currentDate = new Date();
          const endRange = new Date(currentDate.getTime() + 30 * 24 * 60 * 60 * 1000);
          
          let instanceDate = new Date(startDate);
          let instanceCount = 0;
          const maxInstances = pattern.end_after_count || 50; // Limit to prevent infinite loops
          
          while (instanceDate <= endRange && instanceCount < maxInstances) {
            // Only include instances that are today or in the future
            if (instanceDate >= currentDate.setHours(0, 0, 0, 0)) {
              const instanceStart = new Date(instanceDate);
              const instanceEnd = new Date(instanceDate.getTime() + duration);
              
              transformedEvents.push({
                ...baseEvent,
                id: `${event.id}-${instanceDate.toISOString().split('T')[0]}`,
                start: instanceStart.toISOString(),
                end: instanceEnd.toISOString()
              });
            }
            
            // Calculate next occurrence
            if (pattern.pattern === 'daily') {
              instanceDate.setDate(instanceDate.getDate() + (pattern.interval || 1));
            } else if (pattern.pattern === 'weekly') {
              instanceDate.setDate(instanceDate.getDate() + 7 * (pattern.interval || 1));
            }
            
            instanceCount++;
          }
        } else {
          // Non-recurring event
          transformedEvents.push(baseEvent);
        }
      });
      
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
    console.log('Event clicked:', info.event.title);
    // TODO: Open event edit modal
  }, []);

  // Handle event drag/resize
  const handleEventChange = useCallback((info) => {
    console.log('Event changed:', info.event.title);
    // TODO: Update event via API
  }, []);

  // Custom event content based on duration
  const renderEventContent = useCallback((eventInfo) => {
    const event = eventInfo.event;
    const duration = event.end - event.start; // Duration in milliseconds
    const durationMinutes = duration / (1000 * 60);
    
    const title = event.title;
    const location = event.extendedProps.location;
    const eventType = event.extendedProps.event_type;
    
    // Smart content based on duration
    if (durationMinutes <= 30) {
      // Short events: Title + Time only
      return (
        <div className="fc-event-content-short">
          <div className="fc-event-title-short">{title}</div>
        </div>
      );
    } else if (durationMinutes <= 60) {
      // Medium events: Title + Location (if available)
      return (
        <div className="fc-event-content-medium">
          <div className="fc-event-title-medium">{title}</div>
          {location && <div className="fc-event-location">{location}</div>}
        </div>
      );
    } else {
      // Long events: Title + Location + Type indicator
      return (
        <div className="fc-event-content-long">
          <div className="fc-event-title-long">{title}</div>
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
    </div>
  );
}

export default FullCalendarView;