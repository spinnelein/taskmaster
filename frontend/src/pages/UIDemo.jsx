// UI Demo page to showcase the new form components and modal system
// NO EMOJIS
import { useState } from 'react';
import TaskFormModal from '../components/tasks/TaskFormModal';
import EventFormModal from '../components/events/EventFormModal';
import { Button, SecondaryButton } from '../components/common/FormComponents';

function UIDemo() {
  const [taskModalOpen, setTaskModalOpen] = useState(false);
  const [eventModalOpen, setEventModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);

  // Sample data for editing
  const sampleTask = {
    id: '123',
    title: 'Sample Task for Editing',
    duration: 60,
    urgency: 7,
    description: 'This is a sample task to demonstrate the edit functionality.',
    status: 'active',
    due_date: '2025-01-20',
    due_time: '14:30',
    is_recurring: true,
    recurrence_pattern: {
      frequency: 'weekly',
      interval: 1
    }
  };

  const sampleEvent = {
    id: '456',
    title: 'Sample Meeting for Editing',
    start_time: '2025-01-20T10:00:00',
    end_time: '2025-01-20T11:00:00',
    location: 'Conference Room A',
    description: 'Weekly team sync meeting',
    is_blocking: true,
    is_recurring: true,
    recurrence_pattern: {
      pattern: 'weekly',
      interval: 1,
      weekdays: ['Mon'],
      end_type: 'never'
    }
  };

  const handleTaskSubmit = (taskData) => {
    console.log('Task submitted:', taskData);
    // Here you would typically send to API
  };

  const handleEventSubmit = (eventData) => {
    console.log('Event submitted:', eventData);
    // Here you would typically send to API
  };

  const openTaskModal = (task = null) => {
    setEditingTask(task);
    setTaskModalOpen(true);
  };

  const openEventModal = (event = null) => {
    setEditingEvent(event);
    setEventModalOpen(true);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          TaskMaster UI Improvements Demo
        </h1>
        <p className="text-gray-600 text-lg">
          Demonstrating Phase 1 improvements: Modal System, Responsive Forms, and Progressive Disclosure
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Task Forms Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Task Forms</h2>
          <p className="text-gray-600 mb-6">
            Enhanced task creation and editing with responsive layouts, priority matrix, 
            and collapsible sections for advanced options.
          </p>
          
          <div className="space-y-3">
            <Button 
              onClick={() => openTaskModal()} 
              className="w-full"
            >
              Create New Task
            </Button>
            
            <SecondaryButton 
              onClick={() => openTaskModal(sampleTask)}
              className="w-full"
            >
              Edit Sample Task
            </SecondaryButton>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Key Features:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Responsive grid layout (1-2-2 columns)</li>
              <li>• Visual priority matrix instead of number input</li>
              <li>• Quick duration selection buttons</li>
              <li>• Collapsible scheduling and recurrence sections</li>
              <li>• Auto-resizing textarea</li>
              <li>• Focus management and keyboard navigation</li>
            </ul>
          </div>
        </div>

        {/* Event Forms Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Event Forms</h2>
          <p className="text-gray-600 mb-6">
            Comprehensive event management with event type toggles, quick duration buttons,
            and advanced recurrence options in collapsible sections.
          </p>
          
          <div className="space-y-3">
            <Button 
              onClick={() => openEventModal()} 
              className="w-full"
            >
              Create New Event
            </Button>
            
            <SecondaryButton 
              onClick={() => openEventModal(sampleEvent)}
              className="w-full"
            >
              Edit Sample Event
            </SecondaryButton>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Key Features:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Event type toggle (Timed/All Day/Instant)</li>
              <li>• Quick duration buttons for common times</li>
              <li>• Collapsible details and recurrence sections</li>
              <li>• Visual weekday selector for weekly events</li>
              <li>• Recurrence summary preview</li>
              <li>• Smart time calculations</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Modal Features Section */}
      <div className="mt-8 bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h2 className="text-xl font-semibold text-blue-900 mb-4">Modal System Features</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="font-medium text-blue-900 mb-2">UX Improvements:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Maximum 90vh height prevents scrolling issues</li>
              <li>• Internal scrollable content area</li>
              <li>• Responsive sizing for mobile/tablet/desktop</li>
              <li>• Smooth animations and transitions</li>
              <li>• Focus trap for keyboard accessibility</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-blue-900 mb-2">Interaction Features:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Escape key to close</li>
              <li>• Click backdrop to close</li>
              <li>• Prevents body scroll when open</li>
              <li>• Keyboard navigation between form fields</li>
              <li>• WCAG 2.1 AA accessibility compliance</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Implementation Notes */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Implementation Notes</h2>
        <p className="text-gray-600 mb-4">
          This demo represents <strong>Phase 1</strong> of the comprehensive UI overhaul plan. 
          The improvements focus on solving immediate usability issues while laying the foundation 
          for future enhancements.
        </p>
        
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Completed in Phase 1:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ Modal system with responsive behavior</li>
              <li>✅ Form component library with progressive disclosure</li>
              <li>✅ Responsive grid layouts</li>
              <li>✅ Enhanced form controls (priority matrix, duration selectors)</li>
              <li>✅ Accessibility improvements</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Coming in Future Phases:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>🔄 Natural language input parsing</li>
              <li>🔄 Multi-layer calendar system</li>
              <li>🔄 Command palette (Cmd+K)</li>
              <li>🔄 Smart scheduling suggestions</li>
              <li>🔄 Mobile gesture navigation</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Task Form Modal */}
      <TaskFormModal
        isOpen={taskModalOpen}
        onClose={() => {
          setTaskModalOpen(false);
          setEditingTask(null);
        }}
        task={editingTask}
        onSubmit={handleTaskSubmit}
      />

      {/* Event Form Modal */}
      <EventFormModal
        isOpen={eventModalOpen}
        onClose={() => {
          setEventModalOpen(false);
          setEditingEvent(null);
        }}
        event={editingEvent}
        onSubmit={handleEventSubmit}
      />
    </div>
  );
}

export default UIDemo;