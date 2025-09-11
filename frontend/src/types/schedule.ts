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

export interface Event {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  is_blocking: boolean;
  location?: string;
  description?: string;
  duration_minutes: number;
}

export interface Task {
  id: string;
  title: string;
  duration: number;
  urgency: number;
  description?: string;
  completion_status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  is_completed: boolean;
  scheduled_time?: string;
  due_date?: string;
  due_time?: string;
}