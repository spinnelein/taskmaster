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
    navigate('/events');
  };

  return (
    <div style={{ background: '#f9fafb', minHeight: 'calc(100vh - 64px)', paddingTop: '40px' }}>
      <div className="max-w-3xl mx-auto px-4">
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: '700', color: '#1f2937', marginBottom: '8px' }}>
            Create New Event
          </h1>
          <p style={{ color: '#6b7280', fontSize: '15px' }}>
            Add a new event to your schedule
          </p>
        </div>
        
        {error && (
          <div style={{
            background: '#fee',
            border: '1px solid #fcc',
            color: '#c00',
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}
        
        <EventForm onSubmit={handleSubmit} onCancel={handleCancel} />
      </div>
    </div>
  );
}

export default NewEvent;