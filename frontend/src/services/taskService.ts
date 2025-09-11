import apiClient from './api.js';
import { Task } from '../types';

export const taskService = {
  // Get all tasks
  getTasks: async (status: string | null = null): Promise<Task[]> => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/tasks', { params });
    return response.data;
  },

  // Get single task
  getTask: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${id}`);
    return response.data;
  },

  // Create task
  createTask: async (taskData: Partial<Task>): Promise<Task> => {
    const response = await apiClient.post('/tasks', taskData);
    return response.data;
  },

  // Update task
  updateTask: async (id: string, taskData: Partial<Task>): Promise<Task> => {
    const response = await apiClient.put(`/tasks/${id}`, taskData);
    return response.data;
  },

  // Delete task
  deleteTask: async (id: string): Promise<void> => {
    const response = await apiClient.delete(`/tasks/${id}`);
    return response.data;
  },

  // Complete task
  completeTask: async (id: string): Promise<Task> => {
    const response = await apiClient.post(`/tasks/${id}/complete`);
    return response.data;
  },

  // Get overdue tasks
  getOverdueTasks: async (): Promise<Task[]> => {
    const response = await apiClient.get('/tasks/overdue');
    return response.data;
  }
};