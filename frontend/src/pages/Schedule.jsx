// Schedule page
// NO EMOJIS
import { useState, useEffect } from 'react';
import apiClient from '../services/api';

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
      const response = await apiClient.get(`/schedule/${selectedDate}`);
      setSchedule(response.data);
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