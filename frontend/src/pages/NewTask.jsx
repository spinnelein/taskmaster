// New task page
// NO EMOJIS
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import TaskForm from '../components/tasks/TaskForm';
import taskService from '../services/taskService';
import { initiativeService } from '../services/initiativeService';

function NewTask() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');
  const [initiative, setInitiative] = useState(null);
  
  const initiativeId = searchParams.get('initiative_id');

  useEffect(() => {
    if (initiativeId) {
      loadInitiative();
    }
  }, [initiativeId]);

  const loadInitiative = async () => {
    try {
      const response = await initiativeService.getById(initiativeId);
      setInitiative(response);
    } catch (err) {
      console.error('Failed to load initiative:', err);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      setError('');
      // Convert empty strings to null for optional fields
      const taskData = {
        ...formData,
        due_date: formData.due_date || null,
        due_time: formData.due_time || null,
        initiative_id: initiativeId || null
      };
      
      await taskService.createTask(taskData);
      
      // Navigate back to initiative tasks if we came from there, otherwise go to tasks
      if (initiativeId) {
        navigate(`/initiatives/${initiativeId}/tasks`);
      } else {
        navigate('/tasks');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleCancel = () => {
    // Navigate back to where we came from
    if (initiativeId) {
      navigate(`/initiatives/${initiativeId}/tasks`);
    } else {
      navigate('/tasks');
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Create New Task</h1>
        {initiative && (
          <p className="text-gray-600 mt-2">
            For initiative: <span className="font-medium">{initiative.title}</span>
          </p>
        )}
      </div>
      
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