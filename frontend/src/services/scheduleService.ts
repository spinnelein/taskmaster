import apiClient from './api.js';
import { ScheduleDay, Event, Task } from '../types';

export const scheduleService = {
  async getDaySchedule(date: string): Promise<ScheduleDay> {
    const response = await apiClient.get(`/v1/schedule/day/${date}`);
    return response.data;
  },

  async getWeekSchedule(startDate: string): Promise<ScheduleDay[]> {
    const response = await apiClient.get(`/v1/schedule/week/${startDate}`);
    return response.data;
  },

  async scheduleTask(taskId: string, startTime: string): Promise<Task> {
    const response = await apiClient.post(`/v1/schedule/task`, {
      task_id: taskId,
      start_time: startTime
    });
    return response.data;
  },

  async autoScheduleTasks(date: string): Promise<ScheduleDay> {
    const response = await apiClient.post(`/v1/schedule/auto/${date}`);
    return response.data;
  }
};