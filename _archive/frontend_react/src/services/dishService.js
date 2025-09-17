/**
 * Dish service for API calls
 * NO EMOJIS
 */
import { api } from './api';

export const dishService = {
    // Get all dishes with filtering
    async getAll(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.search) queryParams.append('search', params.search);
        if (params.dish_type) queryParams.append('dish_type', params.dish_type);
        if (params.dietary_tags && params.dietary_tags.length > 0) {
            params.dietary_tags.forEach(tag => queryParams.append('dietary_tags', tag));
        }
        if (params.quick_only) queryParams.append('quick_only', 'true');
        if (params.skip) queryParams.append('skip', params.skip);
        if (params.limit) queryParams.append('limit', params.limit);
        
        const response = await api.get(`/dishes?${queryParams.toString()}`);
        return response.data;
    },

    // Search dishes
    async search(query) {
        const response = await api.get(`/dishes/search?q=${encodeURIComponent(query)}`);
        return response.data;
    },

    // Get quick dishes
    async getQuick(maxMinutes = 30) {
        const response = await api.get(`/dishes/quick?max_minutes=${maxMinutes}`);
        return response.data;
    },

    // Get dish by ID with recipe
    async getById(id) {
        const response = await api.get(`/dishes/${id}`);
        return response.data;
    },

    // Create new dish
    async create(dishData) {
        const response = await api.post('/dishes', dishData);
        return response.data;
    },

    // Update dish
    async update(id, updateData) {
        const response = await api.put(`/dishes/${id}`, updateData);
        return response.data;
    },

    // Delete dish
    async delete(id) {
        await api.delete(`/dishes/${id}`);
    },

    // Recipe management
    async createRecipe(dishId, recipeData) {
        const response = await api.post(`/dishes/${dishId}/recipe`, recipeData);
        return response.data;
    },

    async updateRecipe(recipeId, recipeData) {
        const response = await api.put(`/dishes/recipes/${recipeId}`, recipeData);
        return response.data;
    },

    async createRecipeVariation(recipeId, variationData) {
        const response = await api.post(`/dishes/recipes/${recipeId}/variations`, variationData);
        return response.data;
    },

    // Shopping list
    async generateShoppingList(mealIds) {
        const response = await api.post('/dishes/shopping-list', mealIds);
        return response.data;
    },

    // Ingredients
    async createIngredient(name, category = null) {
        const params = new URLSearchParams();
        params.append('name', name);
        if (category) params.append('category', category);
        
        const response = await api.post(`/dishes/ingredients?${params.toString()}`);
        return response.data;
    }
};

export default dishService;