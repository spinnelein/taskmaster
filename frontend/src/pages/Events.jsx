// Events page
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import eventService from '../services/eventService';
import EventForm from '../components/events/EventForm';

function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingEvent, setEditingEvent] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const data = await eventService.getEvents();
      setEvents(data.events);
    } catch (error) {
      console.error('Failed to load events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (event) => {
    setEditingEvent(event);
    setShowEditModal(true);
  };

  const handleEditSubmit = async (eventData) => {
    try {
      await eventService.updateEvent(editingEvent.id, eventData);
      setShowEditModal(false);
      setEditingEvent(null);
      loadEvents();
    } catch (error) {
      console.error('Failed to update event:', error);
      alert('Failed to update event. Please try again.');
    }
  };

  const handleEditCancel = () => {
    setShowEditModal(false);
    setEditingEvent(null);
  };

  const handleDelete = async (eventId) => {
    if (window.confirm('Are you sure you want to delete this event?')) {
      try {
        await eventService.deleteEvent(eventId);
        loadEvents();
      } catch (error) {
        console.error('Failed to delete event:', error);
      }
    }
  };

  const formatDateTime = (dateTimeStr) => {
    return new Date(dateTimeStr).toLocaleString();
  };

  if (loading) {
    return <div className="text-center py-8">Loading events...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Events</h1>
        <Link 
          to="/events/new" 
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          New Event
        </Link>
      </div>

      {events.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-500">No events scheduled. Create your first event!</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow">
          <ul className="divide-y">
            {events.map((event) => (
              <li key={event.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold">{event.title}</h3>
                    <p className="text-sm text-gray-500">
                      {formatDateTime(event.start_time)} - {formatDateTime(event.end_time)}
                    </p>
                    <p className="text-sm text-gray-500">
                      Duration: {event.duration_minutes} minutes
                      {event.is_blocking && (
                        <span className="ml-2 text-red-600">(Blocking)</span>
                      )}
                    </p>
                    {event.is_recurring && (
                      <p className="text-sm text-blue-600 font-medium">
                        🔁 Recurring: {event.recurrence_pattern?.pattern || 'Unknown pattern'}
                        {event.recurrence_pattern?.interval && event.recurrence_pattern.interval > 1 && 
                          ` (every ${event.recurrence_pattern.interval} ${event.recurrence_pattern.pattern}s)`
                        }
                      </p>
                    )}
                    {event.location && (
                      <p className="text-sm text-gray-600">Location: {event.location}</p>
                    )}
                    {event.description && (
                      <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEdit(event)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(event.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Edit Event Modal */}
      {showEditModal && editingEvent && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '800px',
            width: '90%',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px' }}>
              Edit Event
            </h2>
            <EventForm
              event={editingEvent}
              onSubmit={handleEditSubmit}
              onCancel={handleEditCancel}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default Events;