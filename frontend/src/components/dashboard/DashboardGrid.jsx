// Widget-based Dashboard Grid System
// NO EMOJIS
import { useState, useCallback, useMemo } from 'react';
import { DndContext, DragOverlay, useSensor, useSensors, PointerSensor, KeyboardSensor } from '@dnd-kit/core';
import { SortableContext, sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useSortable } from '@dnd-kit/sortable';
import TodaysFocusWidget from './widgets/TodaysFocusWidget';
import CalendarSnapshotWidget from './widgets/CalendarSnapshotWidget';
import './DashboardGrid.css';

const GRID_COLS = 12;
const DEFAULT_WIDGETS = {
  'todays-focus': { component: 'TodaysFocus', size: { w: 4, h: 3 }, position: { x: 0, y: 0 } },
  'calendar-snapshot': { component: 'CalendarSnapshot', size: { w: 8, h: 4 }, position: { x: 4, y: 0 } },
  'project-progress': { component: 'ProjectProgress', size: { w: 6, h: 3 }, position: { x: 0, y: 3 } },
  'quick-actions': { component: 'QuickActions', size: { w: 3, h: 2 }, position: { x: 9, y: 4 } },
  'recent-activity': { component: 'RecentActivity', size: { w: 6, h: 3 }, position: { x: 6, y: 3 } }
};

// Draggable Widget Wrapper
function DraggableWidget({ id, widget, children, onResize, customizable = true }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    gridColumn: `span ${widget.size.w}`,
    gridRow: `span ${widget.size.h}`,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`dashboard-widget ${isDragging ? 'dragging' : ''}`}
      {...attributes}
    >
      {customizable && (
        <div className="widget-controls" {...listeners}>
          <div className="widget-drag-handle">
            <span className="drag-dots">⋮⋮</span>
          </div>
          <div className="widget-actions">
            <button 
              className="widget-action-btn"
              onClick={() => onResize(id, 'expand')}
              aria-label="Expand widget"
            >
              ⛶
            </button>
            <button 
              className="widget-action-btn"
              onClick={() => onResize(id, 'shrink')}
              aria-label="Shrink widget"
            >
              ⊟
            </button>
          </div>
        </div>
      )}
      <div className="widget-content">
        {children}
      </div>
    </div>
  );
}

function DashboardGrid({ 
  widgets = DEFAULT_WIDGETS, 
  onLayoutChange,
  customizable = true,
  className = '',
  children 
}) {
  const [activeId, setActiveId] = useState(null);
  const [widgetLayout, setWidgetLayout] = useState(widgets);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = useCallback((event) => {
    setActiveId(event.active.id);
  }, []);

  const handleDragEnd = useCallback((event) => {
    const { active, over } = event;
    
    if (active.id !== over?.id) {
      setWidgetLayout((prev) => {
        const oldIndex = Object.keys(prev).indexOf(active.id);
        const newIndex = Object.keys(prev).indexOf(over.id);
        
        // Reorder widgets
        const entries = Object.entries(prev);
        const [removed] = entries.splice(oldIndex, 1);
        entries.splice(newIndex, 0, removed);
        
        const newLayout = Object.fromEntries(entries);
        onLayoutChange?.(newLayout);
        return newLayout;
      });
    }
    
    setActiveId(null);
  }, [onLayoutChange]);

  const handleWidgetResize = useCallback((widgetId, action) => {
    setWidgetLayout(prev => {
      const widget = prev[widgetId];
      if (!widget) return prev;

      let newSize = { ...widget.size };
      
      if (action === 'expand') {
        newSize.w = Math.min(newSize.w + 2, GRID_COLS);
        newSize.h = Math.min(newSize.h + 1, 6);
      } else if (action === 'shrink') {
        newSize.w = Math.max(newSize.w - 2, 2);
        newSize.h = Math.max(newSize.h - 1, 2);
      }

      const updated = {
        ...prev,
        [widgetId]: {
          ...widget,
          size: newSize
        }
      };

      onLayoutChange?.(updated);
      return updated;
    });
  }, [onLayoutChange]);

  const widgetIds = useMemo(() => Object.keys(widgetLayout), [widgetLayout]);

  const renderWidget = useCallback((widgetId) => {
    const widget = widgetLayout[widgetId];
    if (!widget) return null;

    // This would be replaced with actual widget components
    const WidgetComponent = getWidgetComponent(widget.component);
    
    return (
      <DraggableWidget
        key={widgetId}
        id={widgetId}
        widget={widget}
        onResize={handleWidgetResize}
        customizable={customizable}
      >
        <WidgetComponent widgetId={widgetId} />
      </DraggableWidget>
    );
  }, [widgetLayout, handleWidgetResize, customizable]);

  const activeWidget = activeId ? widgetLayout[activeId] : null;

  return (
    <div className={`dashboard-container ${className}`}>
      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={widgetIds}>
          <div className="dashboard-grid">
            {widgetIds.map(renderWidget)}
            {children}
          </div>
        </SortableContext>
        
        <DragOverlay>
          {activeId && activeWidget && (
            <div className="widget-drag-overlay">
              <div className="widget-drag-preview">
                {activeWidget.component}
              </div>
            </div>
          )}
        </DragOverlay>
      </DndContext>
      
      {customizable && (
        <div className="dashboard-controls">
          <button className="add-widget-btn">
            + Add Widget
          </button>
          <button className="layout-reset-btn">
            Reset Layout
          </button>
        </div>
      )}
    </div>
  );
}

// Helper function to get widget components
function getWidgetComponent(componentName) {
  const components = {
    TodaysFocus: TodaysFocusWidget,
    CalendarSnapshot: CalendarSnapshotWidget,
    ProjectProgress: ({ widgetId }) => (
      <div className="widget-placeholder project-progress">
        <h3>Project Progress</h3>
        <p>Active projects and milestones</p>
      </div>
    ),
    QuickActions: ({ widgetId }) => (
      <div className="widget-placeholder quick-actions">
        <h3>Quick Actions</h3>
        <div className="quick-action-buttons">
          <button>+ Task</button>
          <button>+ Event</button>
          <button>+ Meal</button>
        </div>
      </div>
    ),
    RecentActivity: ({ widgetId }) => (
      <div className="widget-placeholder recent-activity">
        <h3>Recent Activity</h3>
        <p>Latest updates and changes</p>
      </div>
    )
  };

  return components[componentName] || components.TodaysFocus;
}

export default DashboardGrid;