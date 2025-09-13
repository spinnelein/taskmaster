/**
 * Projects page component
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { projectService } from '../services/projectService';

const Projects = () => {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showActiveOnly, setShowActiveOnly] = useState(false);

    useEffect(() => {
        loadProjects();
    }, [showActiveOnly]);

    const loadProjects = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await projectService.getAll(showActiveOnly);
            setProjects(response.projects || []);
        } catch (err) {
            setError('Failed to load projects: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading projects:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleActive = () => {
        setShowActiveOnly(!showActiveOnly);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active':
                return 'bg-green-100 text-green-800';
            case 'planning':
                return 'bg-blue-100 text-blue-800';
            case 'on_hold':
                return 'bg-yellow-100 text-yellow-800';
            case 'completed':
                return 'bg-purple-100 text-purple-800';
            case 'cancelled':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'critical':
                return 'bg-red-500 text-white';
            case 'high':
                return 'bg-orange-500 text-white';
            case 'medium':
                return 'bg-yellow-500 text-white';
            case 'low':
                return 'bg-green-500 text-white';
            default:
                return 'bg-gray-500 text-white';
        }
    };

    if (loading) {
        return <div className="p-6">Loading projects...</div>;
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
                <button 
                    onClick={loadProjects}
                    className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Projects</h1>
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={showActiveOnly}
                            onChange={handleToggleActive}
                            className="rounded"
                        />
                        Active only
                    </label>
                    <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                        New Project
                    </button>
                </div>
            </div>

            {projects.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                    No projects found. Create your first project to get started!
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {projects.map((project) => (
                        <div key={project.id} className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    {project.title}
                                </h3>
                                <div className="flex flex-col gap-1">
                                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(project.status)}`}>
                                        {project.status}
                                    </span>
                                    <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(project.priority)}`}>
                                        {project.priority}
                                    </span>
                                </div>
                            </div>
                            
                            {project.description && (
                                <p className="text-gray-600 text-sm mb-3">
                                    {project.description}
                                </p>
                            )}
                            
                            <div className="text-sm text-gray-500 space-y-1">
                                {project.estimated_start_date && (
                                    <div>Start: {new Date(project.estimated_start_date).toLocaleDateString()}</div>
                                )}
                                {project.estimated_end_date && (
                                    <div>End: {new Date(project.estimated_end_date).toLocaleDateString()}</div>
                                )}
                                {project.initiative && (
                                    <div className="text-blue-600">Initiative: {project.initiative.title}</div>
                                )}
                                {project.template && (
                                    <div className="text-purple-600">From Template: {project.template.title}</div>
                                )}
                            </div>
                            
                            <div className="mt-4 flex gap-2">
                                <Link 
                                    to={`/projects/${project.id}`}
                                    className="text-blue-600 hover:text-blue-800 text-sm"
                                >
                                    View Details
                                </Link>
                                <button className="text-gray-600 hover:text-gray-800 text-sm">
                                    Edit
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Projects;