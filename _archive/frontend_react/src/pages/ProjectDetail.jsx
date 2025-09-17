/**
 * Project detail page component with phases and timeline
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService } from '../services/projectService';
import ProjectForm from '../components/forms/ProjectForm';

const ProjectDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    
    const [project, setProject] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        loadProjectData();
    }, [id]);

    const loadProjectData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const [projectResponse, statsResponse] = await Promise.all([
                projectService.getById(id),
                projectService.getStats(id)
            ]);
            
            setProject(projectResponse.project);
            setStats(statsResponse);
        } catch (err) {
            setError('Failed to load project: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading project:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = () => {
        setIsEditing(true);
    };

    const handleCancelEdit = () => {
        setIsEditing(false);
    };

    const handleUpdate = async (updateData) => {
        try {
            const response = await projectService.update(id, updateData);
            setProject(response.project);
            setIsEditing(false);
            await loadProjectData(); // Reload stats
        } catch (err) {
            setError('Failed to update project: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleDelete = async () => {
        if (window.confirm('Are you sure you want to delete this project?')) {
            try {
                await projectService.delete(id);
                navigate('/projects');
            } catch (err) {
                setError('Failed to delete project: ' + (err.response?.data?.detail || err.message));
            }
        }
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

    const calculateProgress = () => {
        if (!stats || !stats.total_tasks) return 0;
        return Math.round((stats.completed_tasks / stats.total_tasks) * 100);
    };

    if (loading) {
        return <div className="p-6">Loading project...</div>;
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
                <button 
                    onClick={loadProjectData}
                    className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="p-6">
                <div className="text-center text-gray-500">
                    Project not found
                </div>
            </div>
        );
    }

    if (isEditing) {
        return (
            <div className="p-6">
                <ProjectForm
                    project={project}
                    onSubmit={handleUpdate}
                    onCancel={handleCancelEdit}
                />
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-2xl font-bold">{project.title}</h1>
                        <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(project.status)}`}>
                            {project.status}
                        </span>
                        <span className={`px-3 py-1 text-sm rounded-full ${getPriorityColor(project.priority)}`}>
                            {project.priority}
                        </span>
                    </div>
                    {project.description && (
                        <p className="text-gray-600">{project.description}</p>
                    )}
                </div>
                
                <div className="flex gap-2">
                    <button
                        onClick={handleEdit}
                        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                    >
                        Edit
                    </button>
                    <button
                        onClick={handleDelete}
                        className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
                    >
                        Delete
                    </button>
                    <button
                        onClick={() => navigate('/projects')}
                        className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                    >
                        Back
                    </button>
                </div>
            </div>

            {/* Progress Bar */}
            {stats && stats.total_tasks > 0 && (
                <div className="bg-white p-4 rounded-lg border shadow-sm mb-6">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">Project Progress</span>
                        <span className="text-sm text-gray-500">{calculateProgress()}% Complete</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${calculateProgress()}%` }}
                        ></div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'overview'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('phases')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'phases'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Phases ({project.phases?.length || 0})
                    </button>
                    <button
                        onClick={() => setActiveTab('timeline')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'timeline'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Timeline
                    </button>
                </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Stats Cards */}
                    {stats && (
                        <div className="lg:col-span-2">
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                                <div className="bg-white p-4 rounded-lg border shadow-sm">
                                    <div className="text-2xl font-bold text-green-600">{stats.total_tasks || 0}</div>
                                    <div className="text-sm text-gray-500">Total Tasks</div>
                                </div>
                                <div className="bg-white p-4 rounded-lg border shadow-sm">
                                    <div className="text-2xl font-bold text-blue-600">{stats.completed_tasks || 0}</div>
                                    <div className="text-sm text-gray-500">Completed</div>
                                </div>
                                <div className="bg-white p-4 rounded-lg border shadow-sm">
                                    <div className="text-2xl font-bold text-orange-600">{stats.pending_tasks || 0}</div>
                                    <div className="text-sm text-gray-500">Pending</div>
                                </div>
                                <div className="bg-white p-4 rounded-lg border shadow-sm">
                                    <div className="text-2xl font-bold text-purple-600">{project.phases?.length || 0}</div>
                                    <div className="text-sm text-gray-500">Phases</div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Project Details */}
                    <div className="bg-white p-6 rounded-lg border shadow-sm">
                        <h3 className="text-lg font-semibold mb-4">Project Details</h3>
                        <dl className="space-y-3">
                            {project.initiative && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Initiative</dt>
                                    <dd className="text-sm text-gray-900">{project.initiative.title}</dd>
                                </div>
                            )}
                            {project.template && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Template</dt>
                                    <dd className="text-sm text-gray-900">{project.template.title}</dd>
                                </div>
                            )}
                            {project.estimated_start_date && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Estimated Start</dt>
                                    <dd className="text-sm text-gray-900">
                                        {new Date(project.estimated_start_date).toLocaleDateString()}
                                    </dd>
                                </div>
                            )}
                            {project.estimated_end_date && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Estimated End</dt>
                                    <dd className="text-sm text-gray-900">
                                        {new Date(project.estimated_end_date).toLocaleDateString()}
                                    </dd>
                                </div>
                            )}
                            {project.tags && project.tags.length > 0 && (
                                <div>
                                    <dt className="text-sm font-medium text-gray-500">Tags</dt>
                                    <dd className="text-sm text-gray-900">
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {project.tags.map((tag, index) => (
                                                <span key={index} className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </dd>
                                </div>
                            )}
                        </dl>
                    </div>

                    {/* System Details */}
                    <div className="bg-white p-6 rounded-lg border shadow-sm">
                        <h3 className="text-lg font-semibold mb-4">System Details</h3>
                        <dl className="space-y-3">
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Project ID</dt>
                                <dd className="text-sm text-gray-900 font-mono">{project.id}</dd>
                            </div>
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Created</dt>
                                <dd className="text-sm text-gray-900">
                                    {new Date(project.created_at).toLocaleDateString()} at{' '}
                                    {new Date(project.created_at).toLocaleTimeString()}
                                </dd>
                            </div>
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                                <dd className="text-sm text-gray-900">
                                    {new Date(project.updated_at).toLocaleDateString()} at{' '}
                                    {new Date(project.updated_at).toLocaleTimeString()}
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
            )}

            {activeTab === 'phases' && (
                <div className="space-y-4">
                    {project.phases && project.phases.length > 0 ? (
                        project.phases.map((phase, index) => (
                            <div key={phase.id} className="bg-white p-6 rounded-lg border shadow-sm">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <span className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-800 rounded-full font-semibold">
                                                {phase.order}
                                            </span>
                                            <h3 className="text-lg font-semibold">{phase.title}</h3>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(phase.status)}`}>
                                                {phase.status}
                                            </span>
                                        </div>
                                        {phase.description && (
                                            <p className="text-gray-600 mt-2 ml-11">{phase.description}</p>
                                        )}
                                    </div>
                                </div>
                                
                                <div className="ml-11 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    {phase.estimated_start_date && (
                                        <div>
                                            <span className="text-gray-500">Estimated Start:</span>
                                            <span className="ml-2 text-gray-900">
                                                {new Date(phase.estimated_start_date).toLocaleDateString()}
                                            </span>
                                        </div>
                                    )}
                                    {phase.estimated_end_date && (
                                        <div>
                                            <span className="text-gray-500">Estimated End:</span>
                                            <span className="ml-2 text-gray-900">
                                                {new Date(phase.estimated_end_date).toLocaleDateString()}
                                            </span>
                                        </div>
                                    )}
                                    {phase.actual_start_date && (
                                        <div>
                                            <span className="text-gray-500">Actual Start:</span>
                                            <span className="ml-2 text-gray-900">
                                                {new Date(phase.actual_start_date).toLocaleDateString()}
                                            </span>
                                        </div>
                                    )}
                                    {phase.actual_end_date && (
                                        <div>
                                            <span className="text-gray-500">Actual End:</span>
                                            <span className="ml-2 text-gray-900">
                                                {new Date(phase.actual_end_date).toLocaleDateString()}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center text-gray-500 py-8">
                            No phases defined for this project.
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'timeline' && (
                <div className="bg-white p-6 rounded-lg border shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">Project Timeline</h3>
                    <div className="relative">
                        {project.phases && project.phases.length > 0 ? (
                            <div className="space-y-6">
                                {project.phases.map((phase, index) => (
                                    <div key={phase.id} className="relative flex items-start">
                                        <div className="flex-shrink-0 w-4 h-4 bg-blue-500 rounded-full mt-2"></div>
                                        <div className="ml-4 flex-1">
                                            <div className="flex items-center justify-between">
                                                <h4 className="font-medium">{phase.title}</h4>
                                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(phase.status)}`}>
                                                    {phase.status}
                                                </span>
                                            </div>
                                            <div className="text-sm text-gray-600 mt-1">
                                                {phase.estimated_start_date && phase.estimated_end_date ? (
                                                    `${new Date(phase.estimated_start_date).toLocaleDateString()} - ${new Date(phase.estimated_end_date).toLocaleDateString()}`
                                                ) : (
                                                    'Dates not set'
                                                )}
                                            </div>
                                        </div>
                                        {index < project.phases.length - 1 && (
                                            <div className="absolute left-2 top-6 w-0.5 h-6 bg-gray-300"></div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-8">
                                No phases to display in timeline.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectDetail;