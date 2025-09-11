import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import DaySchedule from '../components/schedule/DaySchedule';
import TaskQueue from '../components/schedule/TaskQueue';
import { Event, Task, TimePool } from '../types';
import { scheduleService } from '../services/scheduleService';
import taskService from '../services/taskService.js';
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