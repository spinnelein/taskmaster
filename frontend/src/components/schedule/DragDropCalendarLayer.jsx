// Enhanced Calendar Layer with advanced drag-and-drop functionality
// NO EMOJIS
import { useState, useRef, useCallback } from 'react';
import './DragDropCalendarLayer.css';

const LAYER_TYPES = {
  events: { color: '#3b82f6', name: 'Events', icon: 'E' },
  tasks: { color: '#10b981', name: 'Tasks', icon: 'T' },
  meals: { color: '#f59e0b', name: 'Meals', icon: 'M' },
  personal: { color: '#8b5cf6', name: 'Personal', icon: 'P' },
  work: { color: '#06b6d4', name: 'Work', icon: 'W' }
};

function DragDropCalendarLayer({ 
  type = 'events',
  items = [],
  visible = true,
  onToggle,
  onItemClick,
  onItemMove,
  onItemResize,
  onQuickCreate,
  timeSlots = [],
  className = '',
  conflictItems = []
}) {
  const [dragState, setDragState] = useState({
    isDragging: false,
    draggedItem: null,
    dragOffset: { x: 0, y: 0 },
    dropTarget: null,
    resizing: false,
    resizeHandle: null
  });

  const layerRef = useRef(null);
  const layerConfig = LAYER_TYPES[type] || LAYER_TYPES.events;

  // Time slot calculations
  const HOUR_HEIGHT = 60; // 60px per hour
  const MINUTES_PER_PIXEL = 1; // 1 minute per pixel

  const timeToPixels = useCallback((timeString) => {
    if (!timeString) return 0;
    const date = new Date(timeString);
    const hours = date.getHours();
    const minutes = date.getMinutes();
    return (hours * HOUR_HEIGHT) + (minutes);
  }, []);

  const pixelsToTime = useCallback((pixels, baseDate) => {
    const totalMinutes = Math.round(pixels / MINUTES_PER_PIXEL);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    
    const newDate = new Date(baseDate);
    newDate.setHours(hours, minutes, 0, 0);
    return newDate.toISOString();
  }, []);

  const getItemPosition = useCallback((item) => {
    if (!item.start_time || !item.end_time) return null;
    
    const startPixels = timeToPixels(item.start_time);
    const endPixels = timeToPixels(item.end_time);
    const height = Math.max(endPixels - startPixels, 30); // Minimum 30px height
    
    return {
      top: `${startPixels}px`,
      height: `${height}px`,
      left: '4px',
      right: '4px',
      position: 'absolute'
    };
  }, [timeToPixels]);

  // Drag handlers for moving items
  const handleItemDragStart = useCallback((e, item) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const layerRect = layerRef.current.getBoundingClientRect();
    
    setDragState({
      isDragging: true,
      draggedItem: item,
      dragOffset: {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      },
      dropTarget: null,
      resizing: false,
      resizeHandle: null
    });

    // Set drag data for cross-layer compatibility
    e.dataTransfer.setData('application/json', JSON.stringify({
      item,
      sourceLayer: type,
      action: 'move'
    }));
    
    e.dataTransfer.effectAllowed = 'move';
    e.currentTarget.style.opacity = '0.5';
  }, [type]);

  const handleItemDragEnd = useCallback((e) => {
    e.currentTarget.style.opacity = '1';
    setDragState({
      isDragging: false,
      draggedItem: null,
      dragOffset: { x: 0, y: 0 },
      dropTarget: null,
      resizing: false,
      resizeHandle: null
    });
  }, []);

  // Resize handlers
  const handleResizeStart = useCallback((e, item, handle) => {
    e.stopPropagation();
    e.preventDefault();
    
    setDragState(prev => ({
      ...prev,
      resizing: true,
      draggedItem: item,
      resizeHandle: handle
    }));

    const handleMouseMove = (moveEvent) => {
      if (!layerRef.current) return;
      
      const layerRect = layerRef.current.getBoundingClientRect();
      const relativeY = moveEvent.clientY - layerRect.top;
      const timePosition = pixelsToTime(relativeY, new Date(item.start_time));
      
      // Update item dimensions based on resize handle
      if (handle === 'top') {
        onItemResize?.(item, { start_time: timePosition });
      } else if (handle === 'bottom') {
        onItemResize?.(item, { end_time: timePosition });
      }
    };

    const handleMouseUp = () => {
      setDragState(prev => ({
        ...prev,
        resizing: false,
        draggedItem: null,
        resizeHandle: null
      }));
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [onItemResize, pixelsToTime]);

  // Drop zone handlers
  const handleLayerDragOver = useCallback((e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    if (!layerRef.current) return;
    
    const layerRect = layerRef.current.getBoundingClientRect();
    const relativeY = e.clientY - layerRect.top;
    const targetTime = Math.max(0, Math.floor(relativeY / HOUR_HEIGHT));
    
    setDragState(prev => ({
      ...prev,
      dropTarget: `${targetTime}:00`
    }));
  }, []);

  const handleLayerDragLeave = useCallback((e) => {
    // Only clear if actually leaving the layer (not moving between child elements)
    if (!layerRef.current?.contains(e.relatedTarget)) {
      setDragState(prev => ({
        ...prev,
        dropTarget: null
      }));
    }
  }, []);

  const handleLayerDrop = useCallback((e) => {
    e.preventDefault();
    
    if (!layerRef.current) return;
    
    const layerRect = layerRef.current.getBoundingClientRect();
    const relativeY = e.clientY - layerRect.top;
    const targetPixels = Math.max(0, relativeY);
    
    try {
      const dragData = JSON.parse(e.dataTransfer.getData('application/json'));
      
      if (dragData.action === 'move' && dragData.item) {
        const newStartTime = pixelsToTime(targetPixels, new Date());
        const duration = new Date(dragData.item.end_time) - new Date(dragData.item.start_time);
        const newEndTime = new Date(new Date(newStartTime).getTime() + duration);
        
        onItemMove?.(dragData.item, {
          start_time: newStartTime,
          end_time: newEndTime.toISOString(),
          targetLayer: type
        });
      }
    } catch (error) {
      console.error('Failed to handle drop:', error);
    }
    
    setDragState(prev => ({
      ...prev,
      dropTarget: null
    }));
  }, [onItemMove, pixelsToTime, type]);

  // Quick creation on empty area click
  const handleEmptyAreaClick = useCallback((e) => {
    if (dragState.isDragging || dragState.resizing) return;
    
    const layerRect = layerRef.current.getBoundingClientRect();
    const relativeY = e.clientY - layerRect.top;
    const targetPixels = Math.max(0, relativeY);
    const targetTime = pixelsToTime(targetPixels, new Date());
    
    onQuickCreate?.(targetTime, type);
  }, [dragState.isDragging, dragState.resizing, onQuickCreate, pixelsToTime, type]);

  // Conflict detection
  const hasConflict = useCallback((item) => {
    return conflictItems.some(conflict => conflict.id === item.id);
  }, [conflictItems]);

  const formatTime = useCallback((timeString) => {
    if (!timeString) return '';
    const date = new Date(timeString);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  }, []);

  if (!visible) return null;

  return (
    <div 
      ref={layerRef}
      className={`calendar-layer calendar-layer-${type} ${className} ${dragState.isDragging ? 'dragging' : ''}`}
      style={{ '--layer-color': layerConfig.color }}
      onDragOver={handleLayerDragOver}
      onDragLeave={handleLayerDragLeave}
      onDrop={handleLayerDrop}
      onClick={handleEmptyAreaClick}
    >
      {/* Drop Target Indicator */}
      {dragState.dropTarget && (
        <div 
          className="drop-target-indicator"
          style={{
            top: `${parseInt(dragState.dropTarget) * HOUR_HEIGHT}px`,
            height: '2px',
            background: layerConfig.color
          }}
        />
      )}

      {/* Layer Items */}
      {items.map((item) => {
        const position = getItemPosition(item);
        if (!position) return null;

        const isConflicted = hasConflict(item);
        const isDraggedItem = dragState.draggedItem?.id === item.id;

        return (
          <div
            key={item.id}
            className={`calendar-item ${isConflicted ? 'conflict' : ''} ${isDraggedItem ? 'dragging' : ''}`}
            style={{
              ...position,
              backgroundColor: layerConfig.color,
              opacity: isDraggedItem ? 0.7 : 1,
              zIndex: isDraggedItem ? 1000 : 1
            }}
            draggable={!dragState.resizing}
            onDragStart={(e) => handleItemDragStart(e, item)}
            onDragEnd={handleItemDragEnd}
            onClick={(e) => {
              e.stopPropagation();
              onItemClick?.(item, type);
            }}
          >
            <div className="calendar-item-content">
              <div className="calendar-item-title" title={item.title}>
                {item.title}
              </div>
              <div className="calendar-item-time">
                {formatTime(item.start_time)}
                {item.end_time && ` - ${formatTime(item.end_time)}`}
              </div>
              {item.location && (
                <div className="calendar-item-location" title={item.location}>
                  {item.location}
                </div>
              )}
              
              {/* Conflict indicator */}
              {isConflicted && (
                <div className="conflict-indicator" title="Time conflict detected">
                  !
                </div>
              )}
            </div>
            
            {/* Resize Handles */}
            {!dragState.isDragging && (
              <>
                <div 
                  className="resize-handle resize-handle-top"
                  onMouseDown={(e) => handleResizeStart(e, item, 'top')}
                />
                <div 
                  className="resize-handle resize-handle-bottom"
                  onMouseDown={(e) => handleResizeStart(e, item, 'bottom')}
                />
              </>
            )}
          </div>
        );
      })}

      {/* Layer Toggle (if needed) */}
      {onToggle && (
        <div className="layer-toggle-mini">
          <button
            className={`layer-toggle-btn-mini ${visible ? 'active' : ''}`}
            onClick={() => onToggle(type)}
            style={{ backgroundColor: visible ? layerConfig.color : '#e5e7eb' }}
          >
            <span className="layer-icon-mini">{layerConfig.icon}</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default DragDropCalendarLayer;