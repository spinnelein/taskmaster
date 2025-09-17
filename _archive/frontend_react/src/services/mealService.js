/**
 * Meal service for API calls
 * NO EMOJIS
 */
import { api } from './api';

export const mealService = {
    // Get all meals
    async getAll(upcomingDays = null, startDate = null, endDate = null) {
        const params = new URLSearchParams();
        if (upcomingDays) params.append('upcoming_days', upcomingDays);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        const response = await api.get(`/meals?${params.toString()}`);
        return response.data;
    },

    // Get upcoming meals
    async getUpcoming(days = 7) {
        const response = await api.get(`/meals/upcoming?days=${days}`);
        return response.data;
    },

    // Get meal by ID with dishes
    async getById(id) {
        const response = await api.get(`/meals/${id}`);
        return response.data;
    },

    // Create new meal
    async create(mealData) {
        const response = await api.post('/meals', mealData);
        return response.data;
    },

    // Update meal
    async update(id, updateData) {
        const response = await api.put(`/meals/${id}`, updateData);
        return response.data;
    },

    // Delete meal
    async delete(id) {
        await api.delete(`/meals/${id}`);
    },

    // Dish management
    async addDish(mealId, dishData) {
        const response = await api.post(`/meals/${mealId}/dishes`, dishData);
        return response.data;
    },

    async removeDish(mealId, dishId) {
        const response = await api.delete(`/meals/${mealId}/dishes/${dishId}`);
        return response.data;
    },

    // Meal prep and events
    async generatePrepTasks(mealId) {
        const response = await api.post(`/meals/${mealId}/generate-prep-tasks`);
        return response.data;
    },

    async createEvent(mealId) {
        const response = await api.post(`/meals/${mealId}/create-event`);
        return response.data;
    },

    // Nutrition
    async getNutrition(mealId) {
        const response = await api.get(`/meals/${mealId}/nutrition`);
        return response.data;
    }
};

export default mealService;