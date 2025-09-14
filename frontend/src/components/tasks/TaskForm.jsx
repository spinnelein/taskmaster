// Task form component with enhanced UI
// NO EMOJIS
import { useState } from 'react';
import { 
  FormGrid, 
  FormField, 
  FormSection, 
  TextInput, 
  Select, 
  Textarea, 
  PriorityMatrix, 
  DurationSelect, 
  FormActions,
  Button,
  CancelButton
} from '../common/FormComponents';

function TaskForm({ task, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    title: task?.title || '',
    duration: task?.duration || 30,
    urgency: task?.urgency || 5,
    description: task?.description || '',
    status: task?.status || 'active',
    due_date: task?.due_date || '',
    due_time: task?.due_time || '',
    is_recurring: task?.is_recurring || false,
    recurrence_frequency: task?.recurrence_pattern?.frequency || 'daily',
    recurrence_interval: task?.recurrence_pattern?.interval || 1
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Transform form data for API
    const submitData = {
      ...formData,
      recurrence_pattern: formData.is_recurring ? {
        frequency: formData.recurrence_frequency,
        interval: parseInt(formData.recurrence_interval, 10)
      } : null
    };
    
    // Remove the separate recurrence fields since they're now in recurrence_pattern
    delete submitData.recurrence_frequency;
    delete submitData.recurrence_interval;
    
    onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Essential Fields - Always Visible */}
      <FormGrid columns={[1, 2, 2]}>
        <FormField label="Title" required fullWidth>
          <TextInput
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="What needs to be done?"
            required
            autoComplete="off"
          />
        </FormField>

        <FormField 
          label="Duration" 
          required
          helpText="How long will this take?"
        >
          <DurationSelect
            value={formData.duration}
            onChange={handleChange}
          />
        </FormField>

        <FormField 
          label="Priority" 
          required
          helpText="How important is this?"
        >
          <PriorityMatrix
            value={formData.urgency}
            onChange={(e) => handleChange({ target: { name: 'urgency', value: e.target.value } })}
          />
        </FormField>
      </FormGrid>

      <FormField label="Description" fullWidth>
        <Textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Add any additional details or notes..."
          autoResize
        />
      </FormField>

      {/* Scheduling Section - Collapsible */}
      <FormSection title="Scheduling" collapsible defaultExpanded={false}>
        <FormGrid columns={[1, 2, 2]}>
          <FormField label="Due Date">
            <TextInput
              type="date"
              name="due_date"
              value={formData.due_date}
              onChange={handleChange}
            />
          </FormField>

          <FormField label="Due Time">
            <TextInput
              type="time"
              name="due_time"
              value={formData.due_time}
              onChange={handleChange}
            />
          </FormField>

          <FormField label="Status">
            <Select
              name="status"
              value={formData.status}
              onChange={handleChange}
              options={[
                { value: 'active', label: 'Active' },
                { value: 'blocked', label: 'Blocked' },
                { value: 'completed', label: 'Completed' }
              ]}
            />
          </FormField>
        </FormGrid>
      </FormSection>

      {/* Recurring Task Section - Collapsible */}
      <FormSection title="Recurring Options" collapsible defaultExpanded={false}>
        <FormField>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_recurring"
              name="is_recurring"
              checked={formData.is_recurring}
              onChange={handleChange}
              className="form-input w-5 h-5"
            />
            <label htmlFor="is_recurring" className="text-sm font-medium text-gray-700">
              Make this a recurring task
            </label>
          </div>
        </FormField>

        {formData.is_recurring && (
          <FormGrid columns={[1, 2, 2]}>
            <FormField label="Frequency">
              <Select
                name="recurrence_frequency"
                value={formData.recurrence_frequency}
                onChange={handleChange}
                options={[
                  { value: 'daily', label: 'Daily' },
                  { value: 'weekly', label: 'Weekly' },
                  { value: 'monthly', label: 'Monthly' },
                  { value: 'yearly', label: 'Yearly' }
                ]}
              />
            </Select>
            </FormField>

            <FormField label="Interval">
              <div className="flex items-center gap-2">
                <TextInput
                  type="number"
                  name="recurrence_interval"
                  value={formData.recurrence_interval}
                  onChange={handleChange}
                  min="1"
                  max="365"
                  placeholder="1"
                />
                <span className="text-sm text-gray-500 whitespace-nowrap">
                  {formData.recurrence_frequency === 'daily' ? 'day(s)' :
                   formData.recurrence_frequency === 'weekly' ? 'week(s)' :
                   formData.recurrence_frequency === 'monthly' ? 'month(s)' :
                   'year(s)'}
                </span>
              </div>
            </FormField>
          </FormGrid>
        )}
      </FormSection>

      <FormActions>
        <CancelButton type="button" onClick={onCancel}>
          Cancel
        </CancelButton>
        <Button type="submit">
          {task ? 'Update' : 'Create'} Task
        </Button>
      </FormActions>
    </form>
  );
}

export default TaskForm;