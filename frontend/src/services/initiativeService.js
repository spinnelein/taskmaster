/**
 * Initiative service for API calls
 * NO EMOJIS
 */
import { api } from './api';

export const initiativeService = {
    // Get all initiatives
    async getAll(activeOnly = false) {
        const params = new URLSearchParams();
        if (activeOnly) params.append('active_only', 'true');
        
        const response = await api.get(`/initiatives?${params.toString()}`);
        return response.data;
    },

    // Get initiative by ID
    async getById(id) {
        const response = await api.get(`/initiatives/${id}`);
        return response.data;
    },

    // Get initiative statistics
    async getStats(id) {
        const response = await api.get(`/initiatives/${id}/stats`);
        return response.data;
    },

    // Get initiative templates
    async getTemplates() {
        const response = await api.get('/initiatives/templates');
        return response.data;
    },

    // Create new initiative
    async create(initiativeData) {
        const response = await api.post('/initiatives', initiativeData);
        return response.data;
    },

    // Create initiative from template
    async createFromTemplate(templateId, title) {
        const response = await api.post(`/initiatives/templates/${templateId}/create`, null, {
            params: { title }
        });
        return response.data;
    },

    // Update initiative
    async update(id, updateData) {
        const response = await api.put(`/initiatives/${id}`, updateData);
        return response.data;
    },

    // Delete initiative
    async delete(id) {
        await api.delete(`/initiatives/${id}`);
    }
};

export default initiativeService;