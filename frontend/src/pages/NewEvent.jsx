// New event page
// NO EMOJIS
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import EventForm from '../components/events/EventForm';
import eventService from '../services/eventService';

function NewEvent() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleSubmit = async (formData) => {
    try {
      setError('');
      await eventService.createEvent(formData);
      navigate('/events');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create event');
    }
  };

  const handleCancel = () => {
    navigate('/events');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Create New Event</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="bg-white p-6 rounded-lg shadow">
        <EventForm onSubmit={handleSubmit} onCancel={handleCancel} />
      </div>
    </div>
  );
}

export default NewEvent;