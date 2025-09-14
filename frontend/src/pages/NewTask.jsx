// New task page
// NO EMOJIS
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import TaskFormModal from '../components/tasks/TaskFormModal';
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
    <>
      {/* Background overlay with loading state */}
      <div className="fixed inset-0 bg-gray-50 flex items-center justify-center p-4">
        {error && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50">
            {error}
          </div>
        )}
        
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Create New Task</h1>
          {initiative && (
            <p className="text-gray-600 mb-4">
              For initiative: <span className="font-medium">{initiative.title}</span>
            </p>
          )}
        </div>
      </div>

      {/* Task Form Modal - always open for new task page */}
      <TaskFormModal
        isOpen={true}
        onClose={handleCancel}
        task={null}
        onSubmit={handleSubmit}
        title={initiative ? `New Task for ${initiative.title}` : "Create New Task"}
      />
    </>
  );
}

export default NewTask;