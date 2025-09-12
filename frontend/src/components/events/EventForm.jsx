// Event form component with improved UI
// NO EMOJIS
import { useState, useEffect } from 'react';
import './EventForm.css';

function EventForm({ event, onSubmit, onCancel }) {
  const [eventType, setEventType] = useState('timed'); // 'timed', 'all-day', 'instant'
  const [isRecurring, setIsRecurring] = useState(false);
  const [recurrence, setRecurrence] = useState({
    pattern: 'daily', // 'daily', 'weekly', 'monthly', 'yearly'
    interval: 1,
    weekdays: [],
    end_type: 'never', // 'never', 'after', 'on'
    end_after_count: 10,
    end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] // 30 days from now
  });
  const [formData, setFormData] = useState({
    title: event?.title || '',
    date: event?.start_time ? event.start_time.split('T')[0] : new Date().toISOString().split('T')[0],
    start_time: event?.start_time ? event.start_time.split('T')[1].substring(0, 5) : '09:00',
    end_time: event?.end_time ? event.end_time.split('T')[1].substring(0, 5) : '10:00',
    is_blocking: event?.is_blocking !== undefined ? event.is_blocking : true,
    location: event?.location || '',
    description: event?.description || ''
  });

  // Auto-update end time when start time changes
  useEffect(() => {
    if (eventType === 'timed' && formData.start_time && !event) {
      // Default to 1 hour duration for new events
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
      // All-day events: start at midnight, end at 11:59 PM
      startDateTime = new Date(`${formData.date}T00:00:00`);
      endDateTime = new Date(`${formData.date}T23:59:59`);
    } else if (eventType === 'instant') {
      // Instant events: same start and end time
      startDateTime = new Date(`${formData.date}T${formData.start_time}:00`);
      endDateTime = new Date(`${formData.date}T${formData.start_time}:00`);
    } else {
      // Timed events
      startDateTime = new Date(`${formData.date}T${formData.start_time}:00`);
      endDateTime = new Date(`${formData.date}T${formData.end_time}:00`);
    }
    
    const eventData = {
      title: formData.title,
      start_time: startDateTime.toISOString(),
      end_time: endDateTime.toISOString(),
      is_blocking: formData.is_blocking,
      location: formData.location || null,
      description: formData.description || "",
      is_recurring: isRecurring,
      recurrence_pattern: isRecurring ? recurrence : null
    };
    
    onSubmit(eventData);
  };

  return (
    <form onSubmit={handleSubmit} className="event-form">
      <div className="form-card">
        {/* Event Type Toggle */}
        <div className="event-type-toggle">
          <button
            type="button"
            className={`toggle-option ${eventType === 'timed' ? 'active' : ''}`}
            onClick={() => setEventType('timed')}
          >
            Timed Event
          </button>
          <button
            type="button"
            className={`toggle-option ${eventType === 'all-day' ? 'active' : ''}`}
            onClick={() => setEventType('all-day')}
          >
            All Day
          </button>
          <button
            type="button"
            className={`toggle-option ${eventType === 'instant' ? 'active' : ''}`}
            onClick={() => setEventType('instant')}
          >
            Instant
          </button>
        </div>

        {/* Title */}
        <div className="form-group">
          <label className="form-label">Event Title *</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="e.g., Team Meeting, Lunch with Sarah"
            className="form-input"
          />
        </div>

        {/* Date and Time */}
        <div className="form-section">
          <div className="form-group">
            <label className="form-label">Date *</label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>

          {eventType === 'timed' && (
            <>
              <div className="time-row">
                <div className="form-group">
                  <label className="form-label">Start Time *</label>
                  <input
                    type="time"
                    name="start_time"
                    value={formData.start_time}
                    onChange={handleChange}
                    required
                    className="form-input"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Time *</label>
                  <input
                    type="time"
                    name="end_time"
                    value={formData.end_time}
                    onChange={handleChange}
                    required
                    className="form-input"
                  />
                </div>
              </div>
              
              {/* Quick Duration Buttons */}
              <div className="duration-buttons">
                <button type="button" onClick={() => setDuration(15)} className="duration-btn">15m</button>
                <button type="button" onClick={() => setDuration(30)} className="duration-btn">30m</button>
                <button type="button" onClick={() => setDuration(45)} className="duration-btn">45m</button>
                <button type="button" onClick={() => setDuration(60)} className="duration-btn">1h</button>
                <button type="button" onClick={() => setDuration(90)} className="duration-btn">1.5h</button>
                <button type="button" onClick={() => setDuration(120)} className="duration-btn">2h</button>
              </div>
            </>
          )}

          {eventType === 'instant' && (
            <div className="form-group">
              <label className="form-label">Time *</label>
              <input
                type="time"
                name="start_time"
                value={formData.start_time}
                onChange={handleChange}
                required
                className="form-input"
              />
              <p className="helper-text">Instant events have no duration (e.g., reminder, deadline)</p>
            </div>
          )}

          {eventType === 'all-day' && (
            <div className="all-day-notice">
              <span>This event will span the entire day</span>
            </div>
          )}
        </div>

        {/* Location */}
        <div className="form-group">
          <label className="form-label">Location</label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="e.g., Conference Room A, Zoom, Coffee Shop"
            className="form-input"
          />
        </div>

        {/* Description */}
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Add any additional details..."
            rows="3"
            className="form-input form-textarea"
          />
        </div>

        {/* Recurrence Section */}
        <div className="recurrence-section">
          <div className="recurrence-toggle">
            <input
              type="checkbox"
              id="is_recurring"
              checked={isRecurring}
              onChange={(e) => setIsRecurring(e.target.checked)}
              className="checkbox-input"
            />
            <label htmlFor="is_recurring" className="checkbox-label">
              Repeat Event
            </label>
          </div>

          {isRecurring && (
            <div className="recurrence-options">
              <div className="form-group">
                <label className="form-label">Repeat Pattern</label>
                <select
                  value={recurrence.pattern}
                  onChange={(e) => setRecurrence(prev => ({ ...prev, pattern: e.target.value }))}
                  className="recurrence-type-select"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>

              <div className="recurrence-details">
                <div className="form-group">
                  <label className="form-label">Repeat every</label>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    value={recurrence.interval}
                    onChange={(e) => setRecurrence(prev => ({ ...prev, interval: parseInt(e.target.value) || 1 }))}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    {recurrence.pattern === 'daily' ? 'days' :
                     recurrence.pattern === 'weekly' ? 'weeks' :
                     recurrence.pattern === 'monthly' ? 'months' : 'years'}
                  </label>
                </div>
              </div>

              {recurrence.pattern === 'weekly' && (
                <div className="form-group">
                  <label className="form-label">Repeat on</label>
                  <div className="weekday-selector">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                      <button
                        key={day}
                        type="button"
                        onClick={() => toggleWeekday(day)}
                        className={`weekday-btn ${recurrence.weekdays.includes(day) ? 'selected' : ''}`}
                      >
                        {day[0]}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Ends</label>
                <select
                  value={recurrence.end_type}
                  onChange={(e) => setRecurrence(prev => ({ ...prev, end_type: e.target.value }))}
                  className="form-input"
                >
                  <option value="never">Never</option>
                  <option value="after">After occurrences</option>
                  <option value="on">On date</option>
                </select>
              </div>

              {recurrence.end_type === 'after' && (
                <div className="form-group">
                  <label className="form-label">Number of occurrences</label>
                  <input
                    type="number"
                    min="1"
                    max="999"
                    value={recurrence.end_after_count}
                    onChange={(e) => setRecurrence(prev => ({ ...prev, end_after_count: parseInt(e.target.value) || 1 }))}
                    className="form-input"
                  />
                </div>
              )}

              {recurrence.end_type === 'on' && (
                <div className="form-group">
                  <label className="form-label">End date</label>
                  <input
                    type="date"
                    value={recurrence.end_date}
                    min={formData.date}
                    onChange={(e) => setRecurrence(prev => ({ ...prev, end_date: e.target.value }))}
                    className="form-input"
                  />
                </div>
              )}

              {getRecurrenceSummary() && (
                <div className="recurrence-summary">
                  {getRecurrenceSummary()}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Blocking Toggle */}
        <div className="checkbox-group">
          <input
            type="checkbox"
            id="is_blocking"
            name="is_blocking"
            checked={formData.is_blocking}
            onChange={handleChange}
            className="checkbox-input"
          />
          <label htmlFor="is_blocking" className="checkbox-label">
            Blocking Event
            <span className="helper-text" style={{ marginLeft: '8px' }}>
              (Prevents tasks from being scheduled during this time)
            </span>
          </label>
        </div>

        {/* Form Actions */}
        <div className="form-actions">
          <button
            type="button"
            onClick={onCancel}
            className="btn btn-cancel"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
          >
            {event ? 'Update' : 'Create'} Event
          </button>
        </div>
      </div>
    </form>
  );
}

export default EventForm;