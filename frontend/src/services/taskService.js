// Task API service
// NO EMOJIS
import apiClient from './api';

const taskService = {
  // Get all tasks
  getTasks: async (status = null) => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/tasks', { params });
    return response.data;
  },

  // Get single task
  getTask: async (id) => {
    const response = await apiClient.get(`/tasks/${id}`);
    return response.data;
  },

  // Create task
  createTask: async (taskData) => {
    const response = await apiClient.post('/tasks', taskData);
    return response.data;
  },

  // Update task
  updateTask: async (id, taskData) => {
    const response = await apiClient.put(`/tasks/${id}`, taskData);
    return response.data;
  },

  // Delete task
  deleteTask: async (id) => {
    const response = await apiClient.delete(`/tasks/${id}`);
    return response.data;
  },

  // Complete task
  completeTask: async (id) => {
    const response = await apiClient.post(`/tasks/${id}/complete`);
    return response.data;
  },

  // Get overdue tasks
  getOverdueTasks: async () => {
    const response = await apiClient.get('/tasks/overdue');
    return response.data;
  },

  // Get tasks by initiative
  getByInitiative: async (initiativeId) => {
    const response = await apiClient.get('/tasks', {
      params: { initiative_id: initiativeId }
    });
    return response.data.tasks || [];
  }
};

export { taskService };
export default taskService;