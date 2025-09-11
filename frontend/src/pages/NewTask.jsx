// New task page
// NO EMOJIS
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import TaskForm from '../components/tasks/TaskForm';
import taskService from '../services/taskService';

function NewTask() {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleSubmit = async (formData) => {
    try {
      setError('');
      // Convert empty strings to null for optional fields
      const taskData = {
        ...formData,
        due_date: formData.due_date || null,
        due_time: formData.due_time || null
      };
      
      await taskService.createTask(taskData);
      navigate('/tasks');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleCancel = () => {
    navigate('/tasks');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Create New Task</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="bg-white p-6 rounded-lg shadow">
        <TaskForm onSubmit={handleSubmit} onCancel={handleCancel} />
      </div>
    </div>
  );
}

export default NewTask;