import React from 'react';

interface TimeAxisProps {
  startHour: number;
  endHour: number;
  hourHeight: number;
}

const TimeAxis: React.FC<TimeAxisProps> = ({ startHour, endHour, hourHeight }) => {
  const hours = [];
  for (let i = startHour; i <= endHour; i++) {
    hours.push(i);
  }

  const formatHour = (hour: number): string => {
    if (hour === 0) return '12 AM';
    if (hour === 12) return '12 PM';
    if (hour < 12) return `${hour} AM`;
    return `${hour - 12} PM`;
  };

  return (
    <div className="w-16 flex-shrink-0 border-r border-gray-200">
      {hours.map(hour => (
        <div
          key={hour}
          className="text-xs text-gray-500 pr-2 text-right"
          style={{ height: `${hourHeight}px` }}
        >
          {formatHour(hour)}
        </div>
      ))}
    </div>
  );
};

export default TimeAxis;