// New event page
// NO EMOJIS
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import EventFormModal from '../components/events/EventFormModal';
import eventService from '../services/eventService';

function NewEvent() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleSubmit = async (formData) => {
    try {
      setError('');
      console.log('=== EVENT CREATION DEBUG ===');
      console.log('Form data received:', formData);
      
      const response = await eventService.createEvent(formData);
      console.log('Backend response:', response);
      console.log('Event created successfully, navigating to schedule page');
      
      navigate('/schedule');
    } catch (err) {
      console.error('=== EVENT CREATION ERROR ===');
      console.error('Error details:', err.response?.data || err.message);
      console.error('Full error:', err);
      setError(err.response?.data?.detail || 'Failed to create event');
    }
  };

  const handleCancel = () => {
    navigate('/schedule');
  };

  return (
    <>
      {/* Background overlay */}
      <div className="fixed inset-0 bg-gray-50 flex items-center justify-center p-4">
        {error && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
            {error}
          </div>
        )}
        
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Create New Event</h1>
          <p className="text-gray-600 mb-4">Add a new event to your schedule</p>
        </div>
      </div>

      {/* Event Form Modal - always open for new event page */}
      <EventFormModal
        isOpen={true}
        onClose={handleCancel}
        event={null}
        onSubmit={handleSubmit}
        title="Create New Event"
      />
    </>
  );
}

export default NewEvent;