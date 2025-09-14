// Multi-Layer Calendar View - Phase 2 Enhanced Scheduling Interface
// NO EMOJIS
import { useState, useEffect, useCallback, useMemo } from 'react';
import { format, addDays, startOfWeek, addHours, isSameDay } from 'date-fns';
import CalendarLayer from './CalendarLayer';
import TimeAxis from './TimeAxis';
import eventService from '../../services/eventService';
import taskService from '../../services/taskService';
import { parsePacificTime } from '../../utils/timezone';
import './MultiLayerCalendar.css';

function MultiLayerCalendar() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('week'); // 'day', 'week', 'month'
  const [layerVisibility, setLayerVisibility] = useState({
    events: true,
    tasks: true,
    meals: false,
    personal: true,
    work: true
  });
  
  // Data states
  const [events, setEvents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Interaction states
  const [selectedItem, setSelectedItem] = useState(null);
  const [draggedItem, setDraggedItem] = useState(null);
  
  // Generate time slots for the view
  const timeSlots = useMemo(() => {
    const slots = [];
    for (let hour = 0; hour < 24; hour++) {
      slots.push(`${hour.toString().padStart(2, '0')}:00`);
    }
    return slots;
  }, []);

  // Generate days for the current view
  const viewDays = useMemo(() => {
    if (viewMode === 'day') {
      return [selectedDate];
    } else if (viewMode === 'week') {
      const weekStart = startOfWeek(selectedDate);
      return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
    } else {
      // Month view - simplified for now
      return [selectedDate];
    }
  }, [selectedDate, viewMode]);

  // Load data for the current view
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // Load events
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const eventsResponse = await eventService.getEvents(dateStr);
      const apiEvents = eventsResponse.events || [];
      
      // Transform events to include layer information
      const transformedEvents = apiEvents.map(event => ({
        id: event.id,
        title: event.title,
        start_time: event.start_time,
        end_time: event.end_time,
        type: 'events',
        layer: determineEventLayer(event),
        location: event.location,
        description: event.description,
        is_blocking: event.is_blocking,
        color: getLayerColor(determineEventLayer(event))
      }));

      setEvents(transformedEvents);

      // Load tasks (if they have scheduling info)
      try {
        const tasksResponse = await taskService.getTasks();
        const scheduledTasks = tasksResponse.filter(task => 
          task.due_date && task.due_time
        ).map(task => ({
          id: task.id,
          title: task.title,
          start_time: `${task.due_date}T${task.due_time}:00`,
          end_time: `${task.due_date}T${addHoursToTime(task.due_time, task.duration || 1)}:00`,
          type: 'tasks',
          layer: 'tasks',
          duration: task.duration,
          priority: task.urgency,
          status: task.status,
          color: getLayerColor('tasks')
        }));
        
        setTasks(scheduledTasks);
      } catch (taskError) {
        console.warn('Failed to load tasks:', taskError);
        setTasks([]);
      }

      // Meals would be loaded here when implemented
      setMeals([]);
      
    } catch (error) {
      console.error('Failed to load calendar data:', error);
      setEvents([]);
      setTasks([]);
      setMeals([]);
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Helper functions
  const determineEventLayer = (event) => {
    // Simple logic to categorize events - can be enhanced
    if (event.title?.toLowerCase().includes('work') || 
        event.title?.toLowerCase().includes('meeting') ||
        event.title?.toLowerCase().includes('standup')) {
      return 'work';
    }
    if (event.title?.toLowerCase().includes('lunch') ||
        event.title?.toLowerCase().includes('dinner') ||
        event.title?.toLowerCase().includes('meal')) {
      return 'meals';
    }
    return 'personal';
  };

  const getLayerColor = (layer) => {
    const colors = {
      events: '#3b82f6',
      tasks: '#10b981',
      meals: '#f59e0b',
      personal: '#8b5cf6',
      work: '#06b6d4'
    };
    return colors[layer] || colors.events;
  };

  const addHoursToTime = (timeString, hours) => {
    const [hour, minute] = timeString.split(':').map(Number);
    const newHour = (hour + hours) % 24;
    return `${newHour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
  };

  // Event handlers
  const handleLayerToggle = (layer) => {
    setLayerVisibility(prev => ({
      ...prev,
      [layer]: !prev[layer]
    }));
  };

  const handleItemClick = (item, layer) => {
    setSelectedItem({ item, layer });
    console.log('Item clicked:', { item, layer });
  };

  const handleItemDrag = (dragData, targetTimeSlot, targetLayer) => {
    console.log('Item drag:', { dragData, targetTimeSlot, targetLayer });
    // TODO: Implement drag and drop logic
    // This would update the item's time and potentially move between layers
  };

  const handleQuickCreate = (timeSlot, layer) => {
    console.log('Quick create:', { timeSlot, layer });
    // TODO: Open quick create modal/form
  };

  const handleDateNavigation = (direction) => {
    const days = viewMode === 'day' ? 1 : viewMode === 'week' ? 7 : 30;
    const newDate = addDays(selectedDate, direction * days);
    setSelectedDate(newDate);
  };

  // Organize items by layer
  const layerData = {
    events: events.filter(event => event.layer === 'personal'),
    work: events.filter(event => event.layer === 'work'),
    meals: events.filter(event => event.layer === 'meals'),
    tasks: tasks,
    personal: events.filter(event => event.layer === 'personal' && !event.layer === 'work')
  };

  return (
    <div className="multi-layer-calendar">
      {/* Calendar Header */}
      <div className="calendar-header">
        <div className="calendar-nav">
          <button 
            className="nav-btn"
            onClick={() => handleDateNavigation(-1)}
            aria-label="Previous period"
          >
            ←
          </button>
          
          <div className="date-display">
            <h2>{format(selectedDate, viewMode === 'week' ? 'MMM d, yyyy' : 'MMMM d, yyyy')}</h2>
          </div>
          
          <button 
            className="nav-btn"
            onClick={() => handleDateNavigation(1)}
            aria-label="Next period"
          >
            →
          </button>
        </div>

        <div className="view-mode-toggle">
          {['day', 'week', 'month'].map(mode => (
            <button
              key={mode}
              className={`view-mode-btn ${viewMode === mode ? 'active' : ''}`}
              onClick={() => setViewMode(mode)}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        <div className="layer-controls">
          {Object.entries(layerVisibility).map(([layer, visible]) => (
            <button
              key={layer}
              className={`layer-control ${visible ? 'active' : ''}`}
              onClick={() => handleLayerToggle(layer)}
              style={{ 
                backgroundColor: visible ? getLayerColor(layer) : '#e5e7eb',
                color: visible ? 'white' : '#6b7280'
              }}
            >
              {layer.charAt(0).toUpperCase() + layer.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Calendar Body */}
      <div className="calendar-body">
        {loading && (
          <div className="calendar-loading">
            <div className="loading-spinner">Loading calendar...</div>
          </div>
        )}

        <div className="calendar-grid">
          {/* Time Axis */}
          <div className="calendar-time-axis">
            <TimeAxis hours={24} />
          </div>

          {/* Calendar Content */}
          <div className="calendar-content">
            {viewDays.map((day, dayIndex) => (
              <div key={dayIndex} className="calendar-day">
                <div className="calendar-day-header">
                  <div className="day-label">
                    {format(day, viewMode === 'week' ? 'EEE d' : 'EEEE, MMMM d')}
                  </div>
                </div>

                <div className="calendar-day-content">
                  {/* Render each layer */}
                  {Object.entries(layerData).map(([layerType, items]) => {
                    const dayItems = items.filter(item => {
                      const itemDate = new Date(item.start_time);
                      return isSameDay(itemDate, day);
                    });

                    return (
                      <CalendarLayer
                        key={layerType}
                        type={layerType}
                        items={dayItems}
                        visible={layerVisibility[layerType]}
                        onToggle={handleLayerToggle}
                        onItemClick={handleItemClick}
                        onItemDrag={handleItemDrag}
                        timeSlots={timeSlots}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="calendar-quick-actions">
        <button 
          className="quick-action-btn"
          onClick={() => handleQuickCreate('09:00', 'events')}
        >
          + Quick Event
        </button>
        <button 
          className="quick-action-btn"
          onClick={() => handleQuickCreate('09:00', 'tasks')}
        >
          + Quick Task
        </button>
      </div>
    </div>
  );
}

export default MultiLayerCalendar;