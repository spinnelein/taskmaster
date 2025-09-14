// Calendar Snapshot Widget - Shows upcoming events
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { format, isToday, isTomorrow, addDays } from 'date-fns';
import eventService from '../../../services/eventService';
import '../widgets.css';

function CalendarSnapshotWidget({ widgetId, size = 'large' }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const today = format(new Date(), 'yyyy-MM-dd');
      const response = await eventService.getEvents(today);
      // Get upcoming events for next 3 days
      const upcoming = response.events
        .filter(event => new Date(event.start_time) >= new Date())
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
        .slice(0, 6);
      setEvents(upcoming);
    } catch (err) {
      console.error('Failed to load events:', err);
      setError('Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  const getRelativeDate = (dateStr) => {
    const date = new Date(dateStr);
    if (isToday(date)) return 'Today';
    if (isTomorrow(date)) return 'Tomorrow';
    return format(date, 'MMM d');
  };

  const formatTime = (timeStr) => {
    const date = new Date(timeStr);
    return format(date, 'h:mm a');
  };

  const getEventTypeColor = (event) => {
    if (event.title.toLowerCase().includes('meeting')) return 'bg-blue-100 text-blue-800';
    if (event.title.toLowerCase().includes('call')) return 'bg-green-100 text-green-800';
    if (event.title.toLowerCase().includes('lunch') || event.title.toLowerCase().includes('meal')) return 'bg-orange-100 text-orange-800';
    return 'bg-purple-100 text-purple-800';
  };

  if (loading) {
    return (
      <div className="widget-loading">
        <div className="loading-spinner">Loading calendar...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="widget-error">
        <p>Error loading events</p>
        <button onClick={loadEvents} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="calendar-snapshot-widget">
      <div className="widget-header">
        <h3 className="widget-title">Upcoming Events</h3>
        <Link to="/events" className="view-all-link">
          View Calendar
        </Link>
      </div>

      <div className="widget-body">
        {events.length === 0 ? (
          <div className="empty-state">
            <p>No upcoming events</p>
            <Link to="/events/new" className="add-event-btn">
              Schedule your first event
            </Link>
          </div>
        ) : (
          <div className="event-list">
            {events.map(event => (
              <div key={event.id} className="event-item">
                <div className="event-time">
                  <div className="event-date">
                    {getRelativeDate(event.start_time)}
                  </div>
                  <div className="event-time-range">
                    {formatTime(event.start_time)}
                    {event.end_time && (
                      <span> - {formatTime(event.end_time)}</span>
                    )}
                  </div>
                </div>
                <div className="event-content">
                  <div className="event-header">
                    <span className="event-title">{event.title}</span>
                    <span className={`event-type ${getEventTypeColor(event)}`}>
                      {event.event_type || 'Event'}
                    </span>
                  </div>
                  {event.location && (
                    <div className="event-location">
                      @ {event.location}
                    </div>
                  )}
                  {event.description && (
                    <div className="event-description">
                      {event.description.substring(0, 50)}
                      {event.description.length > 50 && '...'}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default CalendarSnapshotWidget;