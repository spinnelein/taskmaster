/**
 * Enhanced Schedule service for API calls
 * NO EMOJIS
 */
import { api } from './api';

export const scheduleServiceEnhanced = {
    // Get current week's schedule
    async getCurrentWeek() {
        const response = await api.get('/schedules/current');
        return response.data;
    },

    // Get schedule by week
    async getByWeek(weekStartDate) {
        const response = await api.get(`/schedules/week/${weekStartDate}`);
        return response.data;
    },

    // Generate/regenerate schedule
    async generate(options = {}) {
        const requestData = {
            week_start_date: options.weekStartDate || null,
            regenerate_pools: options.regeneratePools !== false, // Default true
            auto_schedule_tasks: options.autoScheduleTasks !== false // Default true
        };
        
        const response = await api.post('/schedules/generate', requestData);
        return response.data;
    },

    // Get unscheduled task queue
    async getUnscheduledTasks(options = {}) {
        const params = new URLSearchParams();
        if (options.limit) params.append('limit', options.limit);
        if (options.includeBlocked) params.append('include_blocked', 'true');
        if (options.includeSnoozed) params.append('include_snoozed', 'true');
        
        const response = await api.get(`/schedules/queue/unscheduled?${params.toString()}`);
        return response.data;
    },

    // Schedule a specific task
    async scheduleTask(taskId, timePoolId, durationMinutes) {
        const taskSchedule = {
            task_id: taskId,
            time_pool_id: timePoolId,
            scheduled_duration_minutes: durationMinutes
        };
        
        const response = await api.post('/schedules/schedule-task', taskSchedule);
        return response.data;
    },

    // Auto-schedule tasks
    async autoSchedule(scheduleId, maxTasks = 50) {
        const params = new URLSearchParams();
        params.append('max_tasks', maxTasks);
        
        const response = await api.post(`/schedules/auto-schedule/${scheduleId}?${params.toString()}`);
        return response.data;
    },

    // Task management
    async snoozeTask(taskId, snoozeUntil, reason = null) {
        const snoozeData = {
            snooze_until: snoozeUntil,
            reason: reason
        };
        
        const response = await api.post(`/schedules/tasks/${taskId}/snooze`, snoozeData);
        return response.data;
    },

    async markPartialComplete(taskId, minutesWorked, notes = null) {
        const completionData = {
            minutes_worked: minutesWorked,
            notes: notes
        };
        
        const response = await api.post(`/schedules/tasks/${taskId}/partial-complete`, completionData);
        return response.data;
    },

    // Create schedule
    async create(scheduleData) {
        const response = await api.post('/schedules', scheduleData);
        return response.data;
    },

    // Update schedule
    async update(scheduleId, updateData) {
        const response = await api.put(`/schedules/${scheduleId}`, updateData);
        return response.data;
    }
};

export default scheduleServiceEnhanced;