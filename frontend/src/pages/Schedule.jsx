// Schedule page
// NO EMOJIS
import { useState, useEffect } from 'react';
import eventService from '../services/eventService';
import { format } from 'date-fns';

function Schedule() {
  const [schedule, setSchedule] = useState(null);
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSchedule();
  }, [selectedDate]);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      
      // Get all master events
      const eventsResponse = await eventService.getEvents();
      const masterEvents = eventsResponse.events;
      
      let allDayEvents = [];
      
      // Expand recurring events for the selected date
      for (const event of masterEvents) {
        if (event.is_recurring) {
          try {
            // Get occurrences for just this date
            const expansionData = await eventService.getEventOccurrences(
              event.id,
              selectedDate,
              selectedDate,
              1 // Just need to know if it occurs on this date
            );
            
            if (expansionData.occurrences && expansionData.occurrences.length > 0) {
              const occurrence = expansionData.occurrences[0];
              allDayEvents.push({
                id: occurrence.id,
                title: occurrence.title,
                start_time: occurrence.start,
                end_time: occurrence.end,
                location: occurrence.location,
                description: occurrence.description,
                is_blocking: true // Assume blocking for now
              });
            }
          } catch (expandError) {
            console.warn(`Failed to expand ${event.title}:`, expandError);
          }
        } else {
          // Non-recurring event - check if it's on this date
          const eventDate = new Date(event.start_time).toISOString().split('T')[0];
          if (eventDate === selectedDate) {
            allDayEvents.push(event);
          }
        }
      }
      
      // Sort events by start time
      allDayEvents.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
      
      setSchedule({
        date: selectedDate,
        events: allDayEvents,
        free_slots: [] // Will be calculated later
      });
      
    } catch (error) {
      console.error('Failed to load schedule:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateTimeStr) => {
    return new Date(dateTimeStr).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading) {
    return <div className="text-center py-8">Loading schedule...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Schedule</h1>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Events</h2>
          {schedule?.events.length === 0 ? (
            <p className="text-gray-500">No events scheduled</p>
          ) : (
            <ul className="space-y-2">
              {schedule?.events.map((event) => (
                <li key={event.id} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="font-semibold">{event.title}</div>
                  <div className="text-sm text-gray-600">
                    {formatTime(event.start_time)} - {formatTime(event.end_time)}
                  </div>
                  {event.is_blocking && (
                    <span className="text-xs text-red-600">Blocking</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Free Time Slots</h2>
          {schedule?.free_slots.length === 0 ? (
            <p className="text-gray-500">No free time slots available</p>
          ) : (
            <ul className="space-y-2">
              {schedule?.free_slots.map((slot, index) => (
                <li key={index} className="border-l-4 border-green-500 pl-4 py-2">
                  <div className="text-sm">
                    {formatTime(slot.start)} - {formatTime(slot.end)}
                  </div>
                  <div className="text-xs text-gray-600">
                    {slot.duration_minutes} minutes available
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

export default Schedule;