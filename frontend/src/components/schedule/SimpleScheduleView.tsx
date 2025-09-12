import React, { useState, useEffect } from 'react';
import './ScheduleView.css';
import { format } from 'date-fns';
import eventService from '../../services/eventService';
import taskService from '../../services/taskService';

interface Event {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  is_blocking: boolean;
}

interface Task {
  id: string;
  title: string;
  duration: number;
  urgency: number;
  completion_status: string;
}

interface TimePool {
  start: Date;
  end: Date;
  minutes: number;
}

const SimpleScheduleView: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState<Event[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timePools, setTimePools] = useState<TimePool[]>([]);
  const [loading, setLoading] = useState(true);

  // Load real data from API
  useEffect(() => {
    loadScheduleData();
  }, [selectedDate]);

  const loadScheduleData = async () => {
    try {
      setLoading(true);
      console.log('=== LOADING SCHEDULE DATA ===');
      console.log('Selected date:', selectedDate);
      
      // Format date for API (YYYY-MM-DD in local timezone)
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      console.log('Loading data for date:', dateStr);
      
      // Load events and tasks in parallel
      const [eventsResponse, tasksResponse] = await Promise.all([
        eventService.getEvents(dateStr),
        taskService.getTasks()
      ]);
      
      console.log('Events loaded:', eventsResponse);
      console.log('Tasks loaded:', tasksResponse);
      
      // Extract events array from response
      const eventsArray = eventsResponse.events || eventsResponse || [];
      const tasksArray = tasksResponse.tasks || tasksResponse || [];
      
      setEvents(eventsArray);
      setTasks(tasksArray);
      
    } catch (error) {
      console.error('=== SCHEDULE DATA LOADING ERROR ===');
      console.error('Error loading schedule data:', error);
      
      // Fallback to mock data on error
      setEvents([
        {
          id: '1',
          title: 'Take kids to school',
          start_time: '2024-01-01T08:00:00',
          end_time: '2024-01-01T08:40:00',
          is_blocking: true
        },
        {
          id: '2',
          title: 'Team Meeting',
          start_time: '2024-01-01T11:00:00',
          end_time: '2024-01-01T12:00:00',
          is_blocking: false
        }
      ]);
      
      setTasks([
        { id: '1', title: 'Review code PR', duration: 45, urgency: 8, completion_status: 'pending' },
        { id: '2', title: 'Write documentation', duration: 60, urgency: 5, completion_status: 'pending' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Calculate time pools
  useEffect(() => {
    const pools: TimePool[] = [];
    const dayStart = new Date(selectedDate);
    dayStart.setHours(7, 0, 0, 0);
    const dayEnd = new Date(selectedDate);
    dayEnd.setHours(22, 0, 0, 0);

    const blockingEvents = events
      .filter(e => e.is_blocking)
      .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

    let currentTime = dayStart;

    blockingEvents.forEach(event => {
      const eventStart = new Date(event.start_time);
      eventStart.setFullYear(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
      
      if (eventStart > currentTime) {
        const minutes = Math.round((eventStart.getTime() - currentTime.getTime()) / 60000);
        if (minutes >= 30) {
          pools.push({ start: new Date(currentTime), end: eventStart, minutes });
        }
      }
      
      const eventEnd = new Date(event.end_time);
      eventEnd.setFullYear(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
      currentTime = eventEnd;
    });

    // Add pool after last event
    if (currentTime < dayEnd) {
      const minutes = Math.round((dayEnd.getTime() - currentTime.getTime()) / 60000);
      if (minutes >= 30) {
        pools.push({ start: new Date(currentTime), end: dayEnd, minutes });
      }
    }

    setTimePools(pools);
  }, [events, selectedDate]);

  const formatTime = (date: Date): string => {
    return format(date, 'h:mm a');
  };

  const getEventStyle = (event: Event) => {
    const start = new Date(event.start_time);
    const end = new Date(event.end_time);
    const startMinutes = start.getHours() * 60 + start.getMinutes();
    const endMinutes = end.getHours() * 60 + end.getMinutes();
    const duration = endMinutes - startMinutes;
    
    // Assuming day starts at 7 AM
    const top = (startMinutes - 7 * 60) * (60 / 60); // 60px per hour
    const height = duration * (60 / 60);
    
    return {
      top: `${top}px`,
      height: `${height}px`
    };
  };

  const getPoolStyle = (pool: TimePool) => {
    const startMinutes = pool.start.getHours() * 60 + pool.start.getMinutes();
    const top = (startMinutes - 7 * 60) * (60 / 60);
    const height = pool.minutes * (60 / 60);
    
    return {
      top: `${top}px`,
      height: `${height}px`
    };
  };

  const hours = Array.from({ length: 16 }, (_, i) => i + 7); // 7 AM to 10 PM

  const getTaskUrgencyClass = (urgency: number): string => {
    if (urgency >= 8) return 'urgent';
    if (urgency >= 5) return 'medium';
    return 'low';
  };

  if (loading) {
    return (
      <div className="schedule-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '16px', color: '#6b7280' }}>Loading schedule...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="schedule-container">
      {/* Sidebar with tasks */}
      <div className="schedule-sidebar">
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
          Unscheduled Tasks
        </h3>
        {tasks.filter(t => t.completion_status === 'pending').map(task => (
          <div key={task.id} className={`task-card ${getTaskUrgencyClass(task.urgency)}`}>
            <div className="task-title">{task.title}</div>
            <div className="task-meta">
              <span>{task.duration} min</span>
              <span>Priority: {task.urgency}/10</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main schedule area */}
      <div className="schedule-main">
        <div className="schedule-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button 
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setDate(newDate.getDate() - 1);
                setSelectedDate(newDate);
              }}
              style={{
                padding: '8px 16px',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              Previous
            </button>
            
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>
              {format(selectedDate, 'EEEE, MMMM d, yyyy')}
            </h2>
            
            <button 
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setDate(newDate.getDate() + 1);
                setSelectedDate(newDate);
              }}
              style={{
                padding: '8px 16px',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              Next
            </button>
          </div>
          
          <button style={{
            padding: '8px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 500,
            cursor: 'pointer'
          }}>
            Auto-Schedule
          </button>
        </div>

        <div className="day-view">
          {/* Time column */}
          <div className="time-column">
            {hours.map(hour => (
              <div key={hour} className="time-label">
                {hour === 12 ? '12 PM' : hour > 12 ? `${hour - 12} PM` : `${hour} AM`}
              </div>
            ))}
          </div>

          {/* Schedule column */}
          <div className="schedule-column">
            {/* Hour lines */}
            {hours.map((hour, i) => (
              <div key={hour} className="hour-line" style={{ top: `${i * 60}px` }} />
            ))}

            {/* Time pools */}
            {timePools.map((pool, i) => (
              <div key={i} className="time-pool" style={getPoolStyle(pool)}>
                <span className="time-pool-label">
                  {Math.floor(pool.minutes / 60)}h {pool.minutes % 60}m available
                </span>
              </div>
            ))}

            {/* Events */}
            {events.map(event => (
              <div
                key={event.id}
                className={`event-block ${event.is_blocking ? 'blocking' : 'non-blocking'}`}
                style={getEventStyle(event)}
              >
                <div className="event-title">{event.title}</div>
                <div className="event-time">
                  {formatTime(new Date(event.start_time))} - {formatTime(new Date(event.end_time))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleScheduleView;