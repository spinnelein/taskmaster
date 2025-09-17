// Modern Schedule View Component
// NO EMOJIS
import { useState, useEffect, useRef } from 'react';
import { format, addDays, startOfWeek, isSameDay } from 'date-fns';
import eventService from '../../services/eventService';
import { parsePacificTime } from '../../utils/timezone';
import './ModernScheduleView.css';

function ModernScheduleView() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('week'); // 'day', 'week', 'month'
  const [events, setEvents] = useState([]);
  const [timePools, setTimePools] = useState([]);
  const [hoveredEvent, setHoveredEvent] = useState(null);
  const scheduleRef = useRef(null);

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const weekStart = startOfWeek(selectedDate);
    return addDays(weekStart, i);
  });

  useEffect(() => {
    loadEvents();
  }, [selectedDate]);

  const loadEvents = async () => {
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const response = await eventService.getEvents(dateStr);
      const apiEvents = response.events || [];
      
      // Transform API events to match component format
      const transformedEvents = apiEvents.map(event => ({
        id: event.id,
        title: event.title,
        start_time: parsePacificTime(event.start_time),
        end_time: parsePacificTime(event.end_time),
        type: event.type || 'event',
        color: getEventColor(event.type),
        location: event.location,
        description: event.description,
        is_blocking: event.is_blocking
      }));
      
      setEvents(transformedEvents);
    } catch (error) {
      console.error('Failed to load events:', error);
      setEvents([]);
    }
  };

  const getEventColor = (type) => {
    const colorMap = {
      'meeting': 'primary',
      'work': 'accent', 
      'break': 'success',
      'call': 'warning',
      'personal': 'info',
      'default': 'primary'
    };
    return colorMap[type] || colorMap.default;
  };

  const getEventPosition = (event) => {
    const startHour = event.start_time.getHours();
    const startMinutes = event.start_time.getMinutes();
    const endHour = event.end_time.getHours();
    const endMinutes = event.end_time.getMinutes();

    const top = ((startHour * 60 + startMinutes) / (24 * 60)) * 100;
    const height = (((endHour * 60 + endMinutes) - (startHour * 60 + startMinutes)) / (24 * 60)) * 100;

    return { top: `${top}%`, height: `${height}%` };
  };

  const formatEventTime = (start, end) => {
    const startStr = format(start, 'h:mm a');
    const endStr = format(end, 'h:mm a');
    return `${startStr} - ${endStr}`;
  };

  const getDayEvents = (day) => {
    return events.filter(event => 
      isSameDay(new Date(event.start_time), day)
    );
  };

  const handleDateChange = (direction) => {
    const days = viewMode === 'day' ? 1 : viewMode === 'week' ? 7 : 30;
    setSelectedDate(prevDate => addDays(prevDate, direction * days));
  };

  const scrollToCurrentTime = () => {
    if (scheduleRef.current) {
      const currentHour = new Date().getHours();
      const scrollPosition = (currentHour / 24) * scheduleRef.current.scrollHeight;
      scheduleRef.current.scrollTo({
        top: scrollPosition - 100,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    scrollToCurrentTime();
  }, []);

  return (
    <div className="modern-schedule">
      {/* Schedule Header */}
      <div className="schedule-header">
        <div className="schedule-nav">
          <button 
            className="nav-btn"
            onClick={() => handleDateChange(-1)}
          >
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <div className="date-display">
            <h2>{format(selectedDate, 'MMMM yyyy')}</h2>
            <p>{format(selectedDate, 'EEEE, MMMM d')}</p>
          </div>
          
          <button 
            className="nav-btn"
            onClick={() => handleDateChange(1)}
          >
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div className="schedule-controls">
          <button 
            className="today-btn"
            onClick={() => setSelectedDate(new Date())}
          >
            Today
          </button>
          
          <div className="view-mode-toggle">
            {['day', 'week', 'month'].map(mode => (
              <button
                key={mode}
                className={`view-mode-btn ${viewMode === mode ? 'active' : ''}`}
                onClick={() => setViewMode(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>

          <button className="add-event-btn">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Event
          </button>
        </div>
      </div>

      {/* Schedule Grid */}
      <div className="schedule-container">
        <div className="time-axis">
          {hours.map(hour => (
            <div key={hour} className="time-slot">
              <span className="time-label">
                {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
              </span>
            </div>
          ))}
        </div>

        <div className="schedule-grid" ref={scheduleRef}>
          {/* Hour Lines */}
          {hours.map(hour => (
            <div key={hour} className="hour-line" />
          ))}

          {/* Current Time Indicator */}
          <div 
            className="current-time-indicator"
            style={{ 
              top: `${((new Date().getHours() * 60 + new Date().getMinutes()) / (24 * 60)) * 100}%` 
            }}
          >
            <div className="time-dot"></div>
            <div className="time-line"></div>
          </div>

          {/* Week View */}
          {viewMode === 'week' && (
            <div className="week-grid">
              {weekDays.map((day, index) => (
                <div key={index} className="day-column">
                  <div className={`day-header ${isSameDay(day, new Date()) ? 'today' : ''}`}>
                    <span className="day-name">{format(day, 'EEE')}</span>
                    <span className="day-number">{format(day, 'd')}</span>
                  </div>
                  <div className="day-events">
                    {getDayEvents(day).map(event => {
                      const position = getEventPosition(event);
                      return (
                        <div
                          key={event.id}
                          className={`event-block ${event.color} ${event.type}`}
                          style={position}
                          onMouseEnter={() => setHoveredEvent(event.id)}
                          onMouseLeave={() => setHoveredEvent(null)}
                        >
                          <div className="event-content">
                            <h4>{event.title}</h4>
                            {hoveredEvent === event.id && (
                              <div className="event-details">
                                <p>{formatEventTime(event.start_time, event.end_time)}</p>
                                {event.location && <p>{event.location}</p>}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Day View */}
          {viewMode === 'day' && (
            <div className="day-view">
              {events.map(event => {
                const position = getEventPosition(event);
                return (
                  <div
                    key={event.id}
                    className={`event-block large ${event.color} ${event.type}`}
                    style={{ ...position, left: '10%', width: '80%' }}
                  >
                    <div className="event-content">
                      <h4>{event.title}</h4>
                      <p>{formatEventTime(event.start_time, event.end_time)}</p>
                      {event.location && <p className="event-location">{event.location}</p>}
                      {event.description && <p className="event-description">{event.description}</p>}
                    </div>
                    <div className="event-actions">
                      <button className="event-action-btn">Edit</button>
                      <button className="event-action-btn">Delete</button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Quick Add FAB */}
      <button className="fab-add">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  );
}

export default ModernScheduleView;