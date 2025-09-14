import React from 'react';
import MultiLayerCalendar from '../components/schedule/MultiLayerCalendar';

const SchedulePage: React.FC = () => {
  return (
    <div className="schedule-page">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Schedule</h1>
        <p className="text-gray-600 mt-2">Manage your events, tasks, and time blocks</p>
      </div>
      
      <MultiLayerCalendar />
    </div>
  );
};

export default SchedulePage;