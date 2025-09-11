// Event API service
// NO EMOJIS
import apiClient from './api';

const eventService = {
  // Get all events
  getEvents: async (date = null) => {
    const params = date ? { date } : {};
    const response = await apiClient.get('/events', { params });
    return response.data;
  },

  // Get single event
  getEvent: async (id) => {
    const response = await apiClient.get(`/events/${id}`);
    return response.data;
  },

  // Create event
  createEvent: async (eventData) => {
    const response = await apiClient.post('/events', eventData);
    return response.data;
  },

  // Update event
  updateEvent: async (id, eventData) => {
    const response = await apiClient.put(`/events/${id}`, eventData);
    return response.data;
  },

  // Delete event
  deleteEvent: async (id) => {
    const response = await apiClient.delete(`/events/${id}`);
    return response.data;
  }
};

export default eventService;