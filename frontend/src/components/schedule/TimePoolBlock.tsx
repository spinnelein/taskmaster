import React, { useState } from 'react';
import { TimePool } from '../../types/schedule';
import { formatTime } from '../../utils/timeUtils';
import { useDrop } from 'react-dnd';

interface TimePoolBlockProps {
  pool: TimePool;
  hourHeight: number;
  onDropTask: (taskId: string, pool: TimePool) => void;
}

const TimePoolBlock: React.FC<TimePoolBlockProps> = ({ pool, hourHeight, onDropTask }) => {
  const [isHovered, setIsHovered] = useState(false);
  
  const [{ isOver }, drop] = useDrop({
    accept: 'task',
    drop: (item: { id: string }) => onDropTask(item.id, pool),
    collect: (monitor) => ({
      isOver: !!monitor.isOver()
    })
  });

  const height = (pool.duration / 60) * hourHeight;
  const startHour = pool.start.getHours() + pool.start.getMinutes() / 60;
  const top = (startHour - 7) * hourHeight; // Adjust for 7 AM start

  return (
    <div
      ref={drop}
      className={`absolute left-0 right-0 mx-1 rounded transition-all ${
        isOver ? 'bg-green-200 border-green-400' : 'bg-green-50 border-green-300'
      } border-2 border-dashed`}
      style={{
        top: `${top}px`,
        height: `${height}px`,
        minHeight: '30px'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="p-2">
        <div className="text-xs font-semibold text-green-700">
          Available: {pool.duration} min
        </div>
        {isHovered && (
          <div className="text-xs text-green-600 mt-1">
            Drop task here to schedule
          </div>
        )}
      </div>
    </div>
  );
};

export default TimePoolBlock;