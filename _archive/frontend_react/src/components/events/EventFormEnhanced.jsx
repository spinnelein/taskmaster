// Enhanced Event form component with modern UI
// NO EMOJIS
import { useState, useEffect } from 'react';
import { 
  FormGrid, 
  FormField, 
  FormSection, 
  TextInput, 
  Select, 
  Textarea, 
  FormActions,
  Button,
  CancelButton
} from '../common/FormComponents';

function EventFormEnhanced({ event, onSubmit, onCancel }) {
  const [eventType, setEventType] = useState('timed'); // 'timed', 'all-day', 'instant'
  const [isRecurring, setIsRecurring] = useState(event?.is_recurring || false);
  const [recurrence, setRecurrence] = useState(
    event?.recurrence_pattern || {
      pattern: 'daily', // 'daily', 'weekly', 'monthly', 'yearly'
      interval: 1,
      weekdays: [],
      end_type: 'never', // 'never', 'after', 'on'
      end_after_count: 10,
      end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // 30 days from now
    }
  );
  
  // Update recurring state when event prop changes
  useEffect(() => {
    if (event) {
      setIsRecurring(event.is_recurring || false);
      if (event.recurrence_pattern) {
        setRecurrence(event.recurrence_pattern);
      }
    }
  }, [event]);
  
  // Helper function to parse API datetime to local components
  const parseEventDateTime = (dateTimeString) => {
    if (!dateTimeString) return null;
    
    try {
      const date = new Date(dateTimeString);
      const dateStr = date.getFullYear() + '-' + 
                     String(date.getMonth() + 1).padStart(2, '0') + '-' + 
                     String(date.getDate()).padStart(2, '0');
      const timeStr = String(date.getHours()).padStart(2, '0') + ':' + 
                     String(date.getMinutes()).padStart(2, '0');
      return { date: dateStr, time: timeStr };
    } catch (error) {
      console.error('Error parsing event datetime:', error);
      return null;
    }
  };

  // Parse existing event times if editing
  const startDateTime = event?.start_time ? parseEventDateTime(event.start_time) : null;
  const endDateTime = event?.end_time ? parseEventDateTime(event.end_time) : null;

  const [formData, setFormData] = useState({
    title: event?.title || '',
    date: startDateTime?.date || new Date().toISOString().split('T')[0],
    start_time: startDateTime?.time || '09:00',
    end_time: endDateTime?.time || '10:00',
    is_blocking: event?.is_blocking !== undefined ? event.is_blocking : true,
    location: event?.location || '',
    description: event?.description || ''
  });

  // Auto-update end time when start time changes
  useEffect(() => {
    if (eventType === 'timed' && formData.start_time && !event) {
      const [hours, minutes] = formData.start_time.split(':').map(Number);
      const endHours = (hours + 1) % 24;
      const endTime = `${endHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      setFormData(prev => ({ ...prev, end_time: endTime }));
    }
  }, [formData.start_time, eventType, event]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const setDuration = (minutes) => {
    const [hours, mins] = formData.start_time.split(':').map(Number);
    const startDate = new Date();
    startDate.setHours(hours, mins, 0, 0);
    
    const endDate = new Date(startDate.getTime() + minutes * 60000);
    const endTime = `${endDate.getHours().toString().padStart(2, '0')}:${endDate.getMinutes().toString().padStart(2, '0')}`;
    
    setFormData(prev => ({ ...prev, end_time: endTime }));
  };

  const toggleWeekday = (day) => {
    setRecurrence(prev => ({
      ...prev,
      weekdays: prev.weekdays.includes(day)
        ? prev.weekdays.filter(d => d !== day)
        : [...prev.weekdays, day]
    }));
  };

  const getRecurrenceSummary = () => {
    if (!isRecurring) return '';
    
    let summary = 'Repeats ';
    
    switch (recurrence.pattern) {
      case 'daily':
        summary += recurrence.interval === 1 ? 'every day' : `every ${recurrence.interval} days`;
        break;
      case 'weekly':
        if (recurrence.weekdays.length > 0) {
          summary += recurrence.interval === 1 ? 'weekly on ' : `every ${recurrence.interval} weeks on `;
          summary += recurrence.weekdays.join(', ');
        } else {
          summary += recurrence.interval === 1 ? 'weekly' : `every ${recurrence.interval} weeks`;
        }
        break;
      case 'monthly':
        summary += recurrence.interval === 1 ? 'monthly' : `every ${recurrence.interval} months`;
        break;
      case 'yearly':
        summary += recurrence.interval === 1 ? 'yearly' : `every ${recurrence.interval} years`;
        break;
    }
    
    if (recurrence.end_type === 'after') {
      summary += ` for ${recurrence.end_after_count} occurrences`;
    } else if (recurrence.end_type === 'on') {
      summary += ` until ${recurrence.end_date}`;
    }
    
    return summary;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    let startDateTime, endDateTime;
    
    if (eventType === 'all-day') {
      startDateTime = new Date(`${formData.date}T00:00:00`);
      endDateTime = new Date(`${formData.date}T23:59:59`);
    } else if (eventType === 'instant') {
      startDateTime = new Date(`${formData.date}T${formData.start_time}:00`);
      endDateTime = new Date(`${formData.date}T${formData.start_time}:00`);
    } else {
      startDateTime = new Date(`${formData.date}T${formData.start_time}:00`);
      endDateTime = new Date(`${formData.date}T${formData.end_time}:00`);
    }
    
    const formatAsLocalTime = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');
      const second = String(date.getSeconds()).padStart(2, '0');
      return `${year}-${month}-${day}T${hour}:${minute}:${second}`;
    };

    const eventData = {
      title: formData.title,
      start_time: formatAsLocalTime(startDateTime),
      end_time: formatAsLocalTime(endDateTime),
      is_blocking: formData.is_blocking,
      location: formData.location || null,
      description: formData.description || "",
      is_recurring: isRecurring,
      recurrence_pattern: isRecurring ? recurrence : null
    };
    
    onSubmit(eventData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Event Type Selection */}
      <FormField label="Event Type" fullWidth>
        <div className="event-type-toggle flex bg-gray-100 rounded-lg p-1 mb-6">
          {[
            { value: 'timed', label: 'Timed Event' },
            { value: 'all-day', label: 'All Day' },
            { value: 'instant', label: 'Instant' }
          ].map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => setEventType(type.value)}
              className={`flex-1 px-4 py-2 rounded-md font-medium text-sm transition-all ${
                eventType === type.value
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>
      </FormField>

      {/* Essential Fields */}
      <FormGrid columns={[1, 1, 2]}>
        <FormField label="Event Title" required fullWidth>
          <TextInput
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="e.g., Team Meeting, Lunch with Sarah"
            required
          />
        </FormField>

        <FormField label="Date" required>
          <TextInput
            type="date"
            name="date"
            value={formData.date}
            onChange={handleChange}
            required
          />
        </FormField>
      </FormGrid>

      {/* Time Fields - Conditional based on event type */}
      {eventType === 'timed' && (
        <FormSection title="Timing">
          <FormGrid columns={[1, 2, 2]}>
            <FormField label="Start Time" required>
              <TextInput
                type="time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
              />
            </FormField>

            <FormField label="End Time" required>
              <TextInput
                type="time"
                name="end_time"
                value={formData.end_time}
                onChange={handleChange}
                required
              />
            </FormField>
          </FormGrid>

          {/* Quick Duration Buttons */}
          <div className="duration-buttons flex gap-2 flex-wrap mt-3">
            {[15, 30, 45, 60, 90, 120].map((minutes) => (
              <button
                key={minutes}
                type="button"
                onClick={() => setDuration(minutes)}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:border-blue-500 hover:text-blue-600 transition-colors"
              >
                {minutes < 60 ? `${minutes}m` : `${minutes/60}h`}
              </button>
            ))}
          </div>
        </FormSection>
      )}

      {eventType === 'instant' && (
        <FormField label="Time" required>
          <TextInput
            type="time"
            name="start_time"
            value={formData.start_time}
            onChange={handleChange}
            required
          />
          <p className="text-sm text-gray-600 mt-1">
            Instant events have no duration (e.g., reminder, deadline)
          </p>
        </FormField>
      )}

      {eventType === 'all-day' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
          <p className="text-yellow-800 text-sm">This event will span the entire day</p>
        </div>
      )}

      {/* Additional Details - Collapsible */}
      <FormSection title="Details" collapsible defaultExpanded={false}>
        <FormGrid columns={[1, 1, 2]}>
          <FormField label="Location">
            <TextInput
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="e.g., Conference Room A, Zoom, Coffee Shop"
            />
          </FormField>

          <FormField>
            <div className="flex items-center gap-3 mt-6">
              <input
                type="checkbox"
                id="is_blocking"
                name="is_blocking"
                checked={formData.is_blocking}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_blocking" className="text-sm font-medium text-gray-700">
                Blocking Event
                <span className="block text-xs text-gray-500">
                  Prevents tasks from being scheduled during this time
                </span>
              </label>
            </div>
          </FormField>
        </FormGrid>

        <FormField label="Description" fullWidth>
          <Textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Add any additional details..."
            rows={3}
            autoResize
          />
        </FormField>
      </FormSection>

      {/* Recurrence Section - Collapsible */}
      <FormSection title="Repeat Options" collapsible defaultExpanded={false}>
        <FormField>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_recurring"
              checked={isRecurring}
              onChange={(e) => setIsRecurring(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="is_recurring" className="text-sm font-medium text-gray-700">
              Repeat Event
            </label>
          </div>
        </FormField>

        {isRecurring && (
          <>
            <FormGrid columns={[1, 2, 3]}>
              <FormField label="Repeat Pattern">
                <Select
                  value={recurrence.pattern}
                  onChange={(e) => setRecurrence(prev => ({ ...prev, pattern: e.target.value }))}
                  options={[
                    { value: 'daily', label: 'Daily' },
                    { value: 'weekly', label: 'Weekly' },
                    { value: 'monthly', label: 'Monthly' },
                    { value: 'yearly', label: 'Yearly' }
                  ]}
                />
              </FormField>

              <FormField label="Repeat every">
                <div className="flex items-center gap-2">
                  <TextInput
                    type="number"
                    min="1"
                    max="99"
                    value={recurrence.interval}
                    onChange={(e) => setRecurrence(prev => ({ ...prev, interval: parseInt(e.target.value) || 1 }))}
                  />
                  <span className="text-sm text-gray-500">
                    {recurrence.pattern === 'daily' ? 'days' :
                     recurrence.pattern === 'weekly' ? 'weeks' :
                     recurrence.pattern === 'monthly' ? 'months' : 'years'}
                  </span>
                </div>
              </FormField>

              <FormField label="Ends">
                <Select
                  value={recurrence.end_type}
                  onChange={(e) => setRecurrence(prev => ({ ...prev, end_type: e.target.value }))}
                  options={[
                    { value: 'never', label: 'Never' },
                    { value: 'after', label: 'After occurrences' },
                    { value: 'on', label: 'On date' }
                  ]}
                />
              </FormField>
            </FormGrid>

            {recurrence.pattern === 'weekly' && (
              <FormField label="Repeat on">
                <div className="flex gap-2 flex-wrap">
                  {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                    <button
                      key={day}
                      type="button"
                      onClick={() => toggleWeekday(day)}
                      className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                        recurrence.weekdays.includes(day)
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {day[0]}
                    </button>
                  ))}
                </div>
              </FormField>
            )}

            {recurrence.end_type === 'after' && (
              <FormField label="Number of occurrences">
                <TextInput
                  type="number"
                  min="1"
                  max="999"
                  value={recurrence.end_after_count}
                  onChange={(e) => setRecurrence(prev => ({ ...prev, end_after_count: parseInt(e.target.value) || 1 }))}
                />
              </FormField>
            )}

            {recurrence.end_type === 'on' && (
              <FormField label="End date">
                <TextInput
                  type="date"
                  value={recurrence.end_date}
                  min={formData.date}
                  onChange={(e) => setRecurrence(prev => ({ ...prev, end_date: e.target.value }))}
                />
              </FormField>
            )}

            {getRecurrenceSummary() && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
                <p className="text-blue-800 text-sm font-medium">{getRecurrenceSummary()}</p>
              </div>
            )}
          </>
        )}
      </FormSection>

      <FormActions>
        <CancelButton type="button" onClick={onCancel}>
          Cancel
        </CancelButton>
        <Button type="submit">
          {event ? 'Update' : 'Create'} Event
        </Button>
      </FormActions>
    </form>
  );
}

export default EventFormEnhanced;