// Quick Event Creation Modal for calendar interactions
// NO EMOJIS
import { useState, useEffect, useRef } from 'react';
import Modal from '../common/Modal';
import { 
  FormGrid, 
  FormField, 
  TextInput, 
  Select, 
  Button, 
  CancelButton 
} from '../common/FormComponents';

function QuickEventModal({ 
  isOpen, 
  onClose, 
  onSubmit,
  initialTime = null,
  initialDate = null,
  layerType = 'events' 
}) {
  const [formData, setFormData] = useState({
    title: '',
    date: initialDate || new Date().toISOString().split('T')[0],
    start_time: initialTime || '09:00',
    end_time: '',
    type: layerType,
    location: '',
    description: ''
  });

  const titleInputRef = useRef(null);

  // Auto-calculate end time when start time changes
  useEffect(() => {
    if (formData.start_time && !formData.end_time) {
      const [hours, minutes] = formData.start_time.split(':').map(Number);
      const endHours = (hours + 1) % 24;
      const endTime = `${endHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      setFormData(prev => ({ ...prev, end_time: endTime }));
    }
  }, [formData.start_time, formData.end_time]);

  // Focus title input when modal opens
  useEffect(() => {
    if (isOpen && titleInputRef.current) {
      setTimeout(() => titleInputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Reset form when modal opens with new data
  useEffect(() => {
    if (isOpen) {
      setFormData({
        title: '',
        date: initialDate || new Date().toISOString().split('T')[0],
        start_time: initialTime || '09:00',
        end_time: '',
        type: layerType,
        location: '',
        description: ''
      });
    }
  }, [isOpen, initialTime, initialDate, layerType]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Create the event data
    const eventData = {
      title: formData.title,
      start_time: `${formData.date}T${formData.start_time}:00`,
      end_time: `${formData.date}T${formData.end_time}:00`,
      location: formData.location || null,
      description: formData.description || '',
      type: formData.type,
      is_blocking: true // Default for quick creation
    };
    
    onSubmit?.(eventData);
    onClose?.();
  };

  const setDuration = (minutes) => {
    if (!formData.start_time) return;
    
    const [hours, mins] = formData.start_time.split(':').map(Number);
    const startDate = new Date();
    startDate.setHours(hours, mins, 0, 0);
    
    const endDate = new Date(startDate.getTime() + minutes * 60000);
    const endTime = `${endDate.getHours().toString().padStart(2, '0')}:${endDate.getMinutes().toString().padStart(2, '0')}`;
    
    setFormData(prev => ({ ...prev, end_time: endTime }));
  };

  const parseNaturalLanguage = (text) => {
    // Simple natural language parsing
    const lower = text.toLowerCase();
    
    // Extract time patterns
    const timeMatch = lower.match(/(\d{1,2}):?(\d{0,2})\s*(am|pm)?/);
    if (timeMatch) {
      let hours = parseInt(timeMatch[1]);
      const minutes = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
      const meridiem = timeMatch[3];
      
      if (meridiem === 'pm' && hours !== 12) hours += 12;
      if (meridiem === 'am' && hours === 12) hours = 0;
      
      const startTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      setFormData(prev => ({ ...prev, start_time: startTime }));
    }
    
    // Extract duration patterns
    const durationMatch = lower.match(/(\d+)\s*(hour|hr|minute|min)s?/);
    if (durationMatch) {
      const amount = parseInt(durationMatch[1]);
      const unit = durationMatch[2];
      const minutes = unit.startsWith('hour') || unit === 'hr' ? amount * 60 : amount;
      setDuration(minutes);
    }
    
    // Clean up the title (remove parsed elements)
    let cleanTitle = text
      .replace(/(\d{1,2}):?(\d{0,2})\s*(am|pm)?/gi, '')
      .replace(/(\d+)\s*(hour|hr|minute|min)s?/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
    
    if (cleanTitle) {
      setFormData(prev => ({ ...prev, title: cleanTitle }));
    }
  };

  const handleTitleBlur = () => {
    // Attempt natural language parsing when user finishes typing title
    if (formData.title && !formData.title.includes(':')) {
      parseNaturalLanguage(formData.title);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Quick Event Creation"
      maxWidth="500px"
      maxHeight="80vh"
      scrollable={true}
      closeOnEscape={true}
      closeOnBackdrop={true}
      responsive={true}
    >
      <form onSubmit={handleSubmit}>
        <FormGrid columns={[1, 1, 1]}>
          <FormField label="What?" required fullWidth>
            <TextInput
              ref={titleInputRef}
              name="title"
              value={formData.title}
              onChange={handleChange}
              onBlur={handleTitleBlur}
              placeholder="e.g., Meeting with Sarah at 3pm for 1 hour"
              required
              autoComplete="off"
            />
            <div className="text-xs text-gray-500 mt-1">
              Try: "Lunch at noon", "Team standup 9am for 30 minutes"
            </div>
          </FormField>

          <FormField label="When?" required>
            <div className="grid grid-cols-2 gap-3">
              <TextInput
                type="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
              />
              <TextInput
                type="time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </div>
          </FormField>

          <FormField label="How long?">
            <div className="flex flex-col gap-2">
              <TextInput
                type="time"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
                placeholder="End time"
              />
              
              {/* Quick Duration Buttons */}
              <div className="flex gap-2 flex-wrap">
                {[15, 30, 60, 90, 120].map((minutes) => (
                  <button
                    key={minutes}
                    type="button"
                    onClick={() => setDuration(minutes)}
                    className="px-2 py-1 text-xs border border-gray-300 rounded hover:border-blue-500 hover:text-blue-600 transition-colors"
                  >
                    {minutes < 60 ? `${minutes}m` : `${minutes/60}h`}
                  </button>
                ))}
              </div>
            </div>
          </FormField>

          <FormField label="Type">
            <Select
              name="type"
              value={formData.type}
              onChange={handleChange}
              options={[
                { value: 'events', label: 'Event' },
                { value: 'work', label: 'Work' },
                { value: 'personal', label: 'Personal' },
                { value: 'tasks', label: 'Task' },
                { value: 'meals', label: 'Meal' }
              ]}
            />
          </FormField>

          <FormField label="Where?" fullWidth>
            <TextInput
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="Location (optional)"
            />
          </FormField>
        </FormGrid>

        <div className="mt-6 flex justify-end gap-3">
          <CancelButton type="button" onClick={onClose}>
            Cancel
          </CancelButton>
          <Button type="submit" disabled={!formData.title.trim()}>
            Create Event
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default QuickEventModal;