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