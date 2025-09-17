import React from 'react';
import { Event } from '../../types';
import { formatTime, calculateDuration } from '../../utils/timeUtils';

interface EventBlockProps {
  event: Event;
  hourHeight: number;
  onEdit?: (event: Event) => void;
}

const EventBlock: React.FC<EventBlockProps> = ({ event, hourHeight, onEdit }) => {
  const startTime = new Date(event.start_time);
  const endTime = new Date(event.end_time);
  const duration = calculateDuration(startTime, endTime);
  const height = (duration / 60) * hourHeight;
  
  const startHour = startTime.getHours() + startTime.getMinutes() / 60;
  const top = (startHour - 7) * hourHeight; // Adjust for 7 AM start

  const bgColor = event.is_blocking 
    ? 'bg-red-100 border-red-300' 
    : 'bg-blue-100 border-blue-300';

  return (
    <div
      className={`absolute left-0 right-0 mx-1 p-2 rounded border ${bgColor} cursor-pointer hover:shadow-md transition-shadow`}
      style={{
        top: `${top}px`,
        height: `${height}px`,
        minHeight: '30px'
      }}
      onClick={() => onEdit && onEdit(event)}
    >
      <div className="text-xs font-semibold truncate">{event.title}</div>
      <div className="text-xs text-gray-600">
        {formatTime(startTime)} - {formatTime(endTime)}
      </div>
      {event.is_blocking && (
        <div className="text-xs text-red-600 mt-1">Blocking</div>
      )}
    </div>
  );
};

export default EventBlock;