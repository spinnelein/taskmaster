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

  // Get events for schedule (expands recurring events)
  getEventsForSchedule: async (date = null) => {
    const params = date ? { date } : {};
    const response = await apiClient.get('/events/schedule', { params });
    return response.data;
  },

  // Get expanded occurrences for a recurring event (NEW RRULE-based expansion)
  getEventOccurrences: async (eventId, startDate, endDate, maxOccurrences = 365) => {
    const params = {
      start_date: startDate,
      end_date: endDate,
      max_occurrences: maxOccurrences
    };
    const response = await apiClient.get(`/events/expand/${eventId}`, { params });
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
    // First check if this is a recurring event
    try {
      const recurringInfo = await apiClient.get(`/events/${id}/recurring-info`);
      
      if (recurringInfo.data.is_recurring_event) {
        // For recurring events, delete entire series by default
        // In the future, this could be enhanced to show a modal asking which mode
        const deleteRequest = {
          edit_mode: 'all_in_series', // Delete entire series
          original_date: null // Not needed for delete all
        };
        
        const response = await apiClient.delete(`/events/${id}/recurring`, {
          data: deleteRequest
        });
        return response.data;
      } else {
        // Non-recurring event, use regular delete
        const response = await apiClient.delete(`/events/${id}`);
        return response.data;
      }
    } catch (error) {
      // If recurring info check fails, try regular delete as fallback
      const response = await apiClient.delete(`/events/${id}`);
      return response.data;
    }
  },

  // Update recurring event with specific mode
  updateRecurringEvent: async (id, editRequest) => {
    const response = await apiClient.put(`/events/${id}/recurring`, editRequest);
    return response.data;
  },

  // Delete recurring event with specific mode
  deleteRecurringEvent: async (id, editMode, originalDate = null) => {
    const deleteRequest = {
      edit_mode: editMode, // 'this_only', 'this_and_future', 'all_in_series'
      original_date: originalDate
    };
    
    const response = await apiClient.delete(`/events/${id}/recurring`, {
      data: deleteRequest
    });
    return response.data;
  }
};

export default eventService;