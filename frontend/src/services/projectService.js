/**
 * Project service for API calls
 * NO EMOJIS
 */
import { api } from './api';

export const projectService = {
    // Get all projects
    async getAll(statusFilter = null, initiativeId = null) {
        const params = new URLSearchParams();
        if (statusFilter) params.append('status_filter', statusFilter);
        if (initiativeId) params.append('initiative_id', initiativeId);
        
        const response = await api.get(`/projects?${params.toString()}`);
        return response.data;
    },

    // Get project by ID with phases
    async getById(id) {
        const response = await api.get(`/projects/${id}`);
        return response.data;
    },

    // Get project statistics
    async getStats(id) {
        const response = await api.get(`/projects/${id}/stats`);
        return response.data;
    },

    // Create new project
    async create(projectData) {
        const response = await api.post('/projects', projectData);
        return response.data;
    },

    // Update project
    async update(id, updateData) {
        const response = await api.put(`/projects/${id}`, updateData);
        return response.data;
    },

    // Delete project
    async delete(id) {
        await api.delete(`/projects/${id}`);
    },

    // Phase management
    async createPhase(projectId, phaseData) {
        const response = await api.post(`/projects/${projectId}/phases`, phaseData);
        return response.data;
    },

    async updatePhase(phaseId, updateData) {
        const response = await api.put(`/projects/phases/${phaseId}`, updateData);
        return response.data;
    },

    // Template execution
    async executeTemplate(templateData) {
        const response = await api.post('/projects/templates/execute', templateData);
        return response.data;
    }
};

export default projectService;