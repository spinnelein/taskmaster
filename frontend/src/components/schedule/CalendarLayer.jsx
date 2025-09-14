// Calendar Layer component for multi-layer calendar system
// NO EMOJIS
import { useState } from 'react';
import './CalendarLayer.css';

const LAYER_TYPES = {
  events: { color: '#3b82f6', name: 'Events', icon: '📅' },
  tasks: { color: '#10b981', name: 'Tasks', icon: '✓' },
  meals: { color: '#f59e0b', name: 'Meals', icon: '🍽' },
  personal: { color: '#8b5cf6', name: 'Personal', icon: '👤' },
  work: { color: '#06b6d4', name: 'Work', icon: '💼' }
};

function CalendarLayer({ 
  type = 'events',
  items = [],
  visible = true,
  onToggle,
  onItemClick,
  onItemDrag,
  timeSlots = [],
  className = ''
}) {
  const [isDragOver, setIsDragOver] = useState(null);
  const layerConfig = LAYER_TYPES[type] || LAYER_TYPES.events;

  const handleDragStart = (e, item) => {
    e.dataTransfer.setData('application/json', JSON.stringify({
      item,
      sourceLayer: type
    }));
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, timeSlot) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setIsDragOver(timeSlot);
  };

  const handleDragLeave = () => {
    setIsDragOver(null);
  };

  const handleDrop = (e, timeSlot) => {
    e.preventDefault();
    setIsDragOver(null);
    
    try {
      const dragData = JSON.parse(e.dataTransfer.getData('application/json'));
      onItemDrag?.(dragData, timeSlot, type);
    } catch (error) {
      console.error('Failed to handle drop:', error);
    }
  };

  const formatTime = (timeString) => {
    if (!timeString) return '';
    const date = new Date(timeString);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const getItemPosition = (item) => {
    if (!item.start_time || !item.end_time) return null;
    
    const startDate = new Date(item.start_time);
    const endDate = new Date(item.end_time);
    
    const startHour = startDate.getHours() + startDate.getMinutes() / 60;
    const endHour = endDate.getHours() + endDate.getMinutes() / 60;
    const duration = endHour - startHour;
    
    return {
      top: `${startHour * 60}px`, // 60px per hour
      height: `${Math.max(duration * 60, 30)}px`, // Minimum 30px height
      left: '0',
      right: '0'
    };
  };

  if (!visible) return null;

  return (
    <div 
      className={`calendar-layer calendar-layer-${type} ${className}`}
      style={{ '--layer-color': layerConfig.color }}
    >
      {/* Layer Header */}
      <div className="calendar-layer-header">
        <div className="layer-toggle">
          <button
            className={`layer-toggle-btn ${visible ? 'active' : ''}`}
            onClick={() => onToggle?.(type)}
            style={{ backgroundColor: visible ? layerConfig.color : '#e5e7eb' }}
          >
            <span className="layer-icon">{layerConfig.icon}</span>
            <span className="layer-name">{layerConfig.name}</span>
            <span className="layer-count">({items.length})</span>
          </button>
        </div>
      </div>

      {/* Time Slots for Drop Targets */}
      <div className="calendar-layer-slots">
        {timeSlots.map((timeSlot, index) => (
          <div
            key={index}
            className={`time-slot ${isDragOver === timeSlot ? 'drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, timeSlot)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, timeSlot)}
            data-time={timeSlot}
          />
        ))}
      </div>

      {/* Layer Items */}
      <div className="calendar-layer-items">
        {items.map((item) => {
          const position = getItemPosition(item);
          if (!position) return null;

          return (
            <div
              key={item.id}
              className="calendar-item"
              style={{
                ...position,
                backgroundColor: layerConfig.color,
                opacity: visible ? 1 : 0.3
              }}
              draggable={true}
              onDragStart={(e) => handleDragStart(e, item)}
              onClick={() => onItemClick?.(item, type)}
            >
              <div className="calendar-item-content">
                <div className="calendar-item-title">{item.title}</div>
                <div className="calendar-item-time">
                  {formatTime(item.start_time)}
                  {item.end_time && ` - ${formatTime(item.end_time)}`}
                </div>
                {item.location && (
                  <div className="calendar-item-location">{item.location}</div>
                )}
              </div>
              
              {/* Resize Handles */}
              <div className="resize-handle resize-handle-top" />
              <div className="resize-handle resize-handle-bottom" />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default CalendarLayer;