// Task form component
// NO EMOJIS
import { useState } from 'react';

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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Title *
        </label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Duration (minutes) *
          </label>
          <input
            type="number"
            name="duration"
            value={formData.duration}
            onChange={handleChange}
            min="1"
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Urgency (1-10) *
          </label>
          <input
            type="number"
            name="urgency"
            value={formData.urgency}
            onChange={handleChange}
            min="1"
            max="10"
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="3"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Due Date
          </label>
          <input
            type="date"
            name="due_date"
            value={formData.due_date}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Due Time
          </label>
          <input
            type="time"
            name="due_time"
            value={formData.due_time}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Status (optional)
        </label>
        <select
          name="status"
          value={formData.status}
          onChange={handleChange}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
        >
          <option value="active">Active</option>
          <option value="blocked">Blocked</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Recurring Task Section */}
      <div className="border-t pt-4">
        <div className="flex items-center mb-4">
          <div className="relative">
            <input
              type="checkbox"
              name="is_recurring"
              checked={formData.is_recurring}
              onChange={handleChange}
              className="sr-only"
            />
            <div 
              onClick={() => handleChange({ 
                target: { name: 'is_recurring', type: 'checkbox', checked: !formData.is_recurring } 
              })}
              className={`w-5 h-5 border-2 rounded cursor-pointer flex items-center justify-center ${
                formData.is_recurring 
                  ? 'bg-blue-600 border-blue-600' 
                  : 'bg-white border-gray-300 hover:border-blue-400'
              }`}
            >
              {formData.is_recurring && (
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </div>
          <label 
            className="ml-3 block text-sm font-medium text-gray-700 cursor-pointer"
            onClick={() => handleChange({ 
              target: { name: 'is_recurring', type: 'checkbox', checked: !formData.is_recurring } 
            })}
          >
            Make this a recurring task
          </label>
        </div>

        {formData.is_recurring && (
          <div className="grid grid-cols-2 gap-4 ml-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Frequency
              </label>
              <select
                name="recurrence_frequency"
                value={formData.recurrence_frequency}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Every
              </label>
              <div className="flex items-center">
                <input
                  type="number"
                  name="recurrence_interval"
                  value={formData.recurrence_interval}
                  onChange={handleChange}
                  min="1"
                  max="365"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
                />
                <span className="ml-2 text-sm text-gray-500">
                  {formData.recurrence_frequency === 'daily' ? 'day(s)' :
                   formData.recurrence_frequency === 'weekly' ? 'week(s)' :
                   formData.recurrence_frequency === 'monthly' ? 'month(s)' :
                   'year(s)'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {task ? 'Update' : 'Create'} Task
        </button>
      </div>
    </form>
  );
}

export default TaskForm;