# Milestone 8: Schedule View with Time Pools

## CRITICAL REMINDERS
- NO EMOJIS in code or comments!
- Use only ASCII characters
- Keep components under 150 lines
- Use TypeScript for type safety
- This is a Windows environment

## Git Commands to Start
git checkout main
git pull origin main
git checkout -b feature/schedule-view

## Objective
Build a schedule view that shows events, time pools, and allows drag-and-drop task scheduling

## Files to Create

### File 1: frontend/src/types/schedule.ts
export interface TimeSlot {
  start: Date;
  end: Date;
  type: 'event' | 'timepool' | 'task';
  isBlocking?: boolean;
  duration: number; // minutes
}

export interface TimePool {
  id: string;
  start: Date;
  end: Date;
  duration: number;
  availableMinutes: number;
  suggestedTasks: string[]; // task IDs that would fit
}

export interface ScheduleDay {
  date: Date;
  events: Event[];
  tasks: Task[];
  timePools: TimePool[];
  totalAvailableMinutes: number;
}

### File 2: frontend/src/utils/timeUtils.ts
import { Event, Task, TimePool } from '../types';

export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('en-US', { 
    hour: 'numeric',
    minute: '2-digit',
    hour12: true 
  });
};

export const calculateDuration = (start: Date, end: Date): number => {
  return Math.round((end.getTime() - start.getTime()) / 60000);
};

export const findTimePools = (events: Event[], dayStart: Date, dayEnd: Date): TimePool[] => {
  const pools: TimePool[] = [];
  const blockingEvents = events
    .filter(e => e.is_blocking)
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

  let currentTime = dayStart;

  blockingEvents.forEach(event => {
    const eventStart = new Date(event.start_time);
    
    if (eventStart > currentTime) {
      const duration = calculateDuration(currentTime, eventStart);
      if (duration >= 15) { // Minimum 15 minutes for a time pool
        pools.push({
          id: `pool-${currentTime.getTime()}`,
          start: currentTime,
          end: eventStart,
          duration,
          availableMinutes: duration,
          suggestedTasks: []
        });
      }
    }
    
    currentTime = new Date(event.end_time);
  });

  // Check for time pool after last event
  if (currentTime < dayEnd) {
    const duration = calculateDuration(currentTime, dayEnd);
    if (duration >= 15) {
      pools.push({
        id: `pool-${currentTime.getTime()}`,
        start: currentTime,
        end: dayEnd,
        duration,
        availableMinutes: duration,
        suggestedTasks: []
      });
    }
  }

  return pools;
};

export const canTaskFitInPool = (task: Task, pool: TimePool): boolean => {
  return task.duration <= pool.availableMinutes;
};

### File 3: frontend/src/services/scheduleService.ts
import { api } from '../config/api';
import { ScheduleDay, Event, Task } from '../types';

export const scheduleService = {
  async getDaySchedule(date: string): Promise<ScheduleDay> {
    const response = await api.get(`/api/v1/schedule/day/${date}`);
    return response.data;
  },

  async getWeekSchedule(startDate: string): Promise<ScheduleDay[]> {
    const response = await api.get(`/api/v1/schedule/week/${startDate}`);
    return response.data;
  },

  async scheduleTask(taskId: string, startTime: string): Promise<Task> {
    const response = await api.post(`/api/v1/schedule/task`, {
      task_id: taskId,
      start_time: startTime
    });
    return response.data;
  },

  async autoScheduleTasks(date: string): Promise<ScheduleDay> {
    const response = await api.post(`/api/v1/schedule/auto/${date}`);
    return response.data;
  }
};

### File 4: frontend/src/components/schedule/TimeAxis.tsx
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

### File 5: frontend/src/components/schedule/EventBlock.tsx
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
  const top = startHour * hourHeight;

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

### File 6: frontend/src/components/schedule/TimePoolBlock.tsx
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
  const top = startHour * hourHeight;

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

### File 7: frontend/src/components/schedule/TaskQueue.tsx
import React from 'react';
import { Task } from '../../types';
import { useDrag } from 'react-dnd';

interface DraggableTaskProps {
  task: Task;
}

const DraggableTask: React.FC<DraggableTaskProps> = ({ task }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'task',
    item: { id: task.id },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  });

  const urgencyColor = task.urgency >= 8 ? 'border-red-400' : 
                       task.urgency >= 5 ? 'border-yellow-400' : 
                       'border-gray-300';

  return (
    <div
      ref={drag}
      className={`p-3 bg-white rounded border-l-4 ${urgencyColor} shadow-sm cursor-move hover:shadow-md transition-shadow ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="font-medium text-sm">{task.title}</div>
      <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
        <span>{task.duration} min</span>
        <span>Urgency: {task.urgency}</span>
      </div>
    </div>
  );
};

interface TaskQueueProps {
  tasks: Task[];
  title?: string;
}

const TaskQueue: React.FC<TaskQueueProps> = ({ tasks, title = "Unscheduled Tasks" }) => {
  const pendingTasks = tasks.filter(t => t.completion_status === 'pending');
  
  return (
    <div className="w-64 bg-gray-50 p-4 h-full overflow-y-auto">
      <h3 className="font-semibold mb-4">{title}</h3>
      <div className="space-y-2">
        {pendingTasks.length === 0 ? (
          <p className="text-gray-500 text-sm">No pending tasks</p>
        ) : (
          pendingTasks.map(task => (
            <DraggableTask key={task.id} task={task} />
          ))
        )}
      </div>
    </div>
  );
};

export default TaskQueue;

### File 8: frontend/src/components/schedule/DaySchedule.tsx
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

### File 9: frontend/src/pages/SchedulePage.tsx
import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import DaySchedule from '../components/schedule/DaySchedule';
import TaskQueue from '../components/schedule/TaskQueue';
import { Event, Task, TimePool } from '../types';
import { scheduleService } from '../services/scheduleService';
import { taskService } from '../services/taskService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import toast from 'react-hot-toast';

const SchedulePage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState<Event[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [unscheduledTasks, setUnscheduledTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSchedule();
  }, [selectedDate]);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      
      // Load both schedule and unscheduled tasks
      const [scheduleData, allTasks] = await Promise.all([
        scheduleService.getDaySchedule(dateStr),
        taskService.getTasks('pending')
      ]);
      
      setEvents(scheduleData.events || []);
      setTasks(scheduleData.tasks || []);
      setUnscheduledTasks(allTasks.filter(t => !t.scheduled_time));
    } catch (err) {
      console.error('Failed to load schedule:', err);
      toast.error('Failed to load schedule');
    } finally {
      setLoading(false);
    }
  };

  const handleDropTask = async (taskId: string, pool: TimePool) => {
    try {
      const startTime = pool.start.toISOString();
      await scheduleService.scheduleTask(taskId, startTime);
      toast.success('Task scheduled!');
      await loadSchedule();
    } catch (err) {
      toast.error('Failed to schedule task');
    }
  };

  const handleAutoSchedule = async () => {
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      await scheduleService.autoScheduleTasks(dateStr);
      toast.success('Tasks auto-scheduled!');
      await loadSchedule();
    } catch (err) {
      toast.error('Failed to auto-schedule');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="flex h-full">
      <TaskQueue tasks={unscheduledTasks} />
      
      <div className="flex-1 p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setDate(newDate.getDate() - 1);
                setSelectedDate(newDate);
              }}
              className="p-2 hover:bg-gray-100 rounded"
            >
              Previous
            </button>
            
            <h2 className="text-xl font-semibold">
              {format(selectedDate, 'EEEE, MMMM d, yyyy')}
            </h2>
            
            <button
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setDate(newDate.getDate() + 1);
                setSelectedDate(newDate);
              }}
              className="p-2 hover:bg-gray-100 rounded"
            >
              Next
            </button>
          </div>
          
          <button
            onClick={handleAutoSchedule}
            className="btn-primary"
          >
            Auto-Schedule Tasks
          </button>
        </div>
        
        <DaySchedule
          date={selectedDate}
          events={events}
          tasks={tasks}
          onDropTask={handleDropTask}
        />
      </div>
    </div>
  );
};

export default SchedulePage;

## Dependencies to Install
cd frontend
npm install react-dnd react-dnd-html5-backend
npm install date-fns

## Test Requirements
1. Schedule page loads without errors
2. Time axis shows hours from 7 AM to 10 PM
3. Events display as blocks (red for blocking, blue for non-blocking)
4. Time pools show as green areas between blocking events
5. Tasks can be dragged from queue to time pools
6. Navigation between days works

## Success Criteria
- Schedule displays events and time pools correctly
- Drag and drop functionality works
- No TypeScript errors
- Visual distinction between blocking/non-blocking events
- Time pools calculate correctly between events

## Git Commands to Finish
git add .
git commit -m "feat: add schedule view with time pools and drag-drop"
git push origin feature/schedule-view

# Create PR and merge
git checkout main
git pull origin main
git merge feature/schedule-view
git push origin main

# Clean up
git branch -d feature/schedule-view

## DO NOT
- Use emojis anywhere in the code
- Create components over 150 lines
- Modify backend files
- Use class components
- Install unnecessary packages
Instructions for Claude Code:
We're building a schedule view for the TaskMaster app. This is the main feature that shows events, calculates time pools between blocking events, and allows drag-and-drop task scheduling.

CRITICAL: 
- NO EMOJIS! Only ASCII characters
- Use TypeScript for all components
- Keep each component under 150 lines
- Use functional components with hooks

Read the milestone document for complete requirements.

The schedule view should:
1. Show a daily timeline from 7 AM to 10 PM
2. Display events as colored blocks (red=blocking, blue=non-blocking)
3. Calculate and show green time pools between blocking events
4. Allow dragging tasks from the left sidebar into time pools
5. Have navigation to move between days

First install the required dependencies (react-dnd and date-fns).
Then create all 9 files in the order listed.
Test that the schedule page loads and drag-drop works.

The visual layout should clearly show the difference between:
- Blocking events (prevent task scheduling)
- Non-blocking events (just for reference)
- Available time pools (where tasks can be scheduled)