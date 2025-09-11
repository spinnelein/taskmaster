import React from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import TimeAxis from './TimeAxis';
import EventBlock from './EventBlock';
import TimePoolBlock from './TimePoolBlock';
import { Event, Task, TimePool } from '../../types';
import { findTimePools } from '../../utils/timeUtils';

interface DayScheduleProps {
  date: Date;
  events: Event[];
  tasks: Task[];
  onDropTask: (taskId: string, pool: TimePool) => void;
  onEditEvent?: (event: Event) => void;
}

const DaySchedule: React.FC<DayScheduleProps> = ({ 
  date, 
  events, 
  tasks, 
  onDropTask,
  onEditEvent 
}) => {
  const startHour = 7;
  const endHour = 22;
  const hourHeight = 60;
  
  const dayStart = new Date(date);
  dayStart.setHours(startHour, 0, 0, 0);
  
  const dayEnd = new Date(date);
  dayEnd.setHours(endHour, 0, 0, 0);
  
  const timePools = findTimePools(events, dayStart, dayEnd);
  const totalHeight = (endHour - startHour + 1) * hourHeight;

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="flex bg-white rounded-lg shadow">
        <TimeAxis 
          startHour={startHour} 
          endHour={endHour} 
          hourHeight={hourHeight} 
        />
        
        <div className="flex-1 relative" style={{ height: `${totalHeight}px` }}>
          {/* Hour lines */}
          {Array.from({ length: endHour - startHour + 1 }).map((_, i) => (
            <div
              key={i}
              className="absolute left-0 right-0 border-t border-gray-100"
              style={{ top: `${i * hourHeight}px` }}
            />
          ))}
          
          {/* Time pools */}
          {timePools.map(pool => (
            <TimePoolBlock
              key={pool.id}
              pool={pool}
              hourHeight={hourHeight}
              onDropTask={onDropTask}
            />
          ))}
          
          {/* Events */}
          {events.map(event => (
            <EventBlock
              key={event.id}
              event={event}
              hourHeight={hourHeight}
              onEdit={onEditEvent}
            />
          ))}
        </div>
      </div>
    </DndProvider>
  );
};

export default DaySchedule;