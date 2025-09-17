/**
 * Initiative detail page component
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { initiativeService } from '../services/initiativeService';
import InitiativeForm from '../components/forms/InitiativeForm';

const InitiativeDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    
    const [initiative, setInitiative] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        loadInitiativeData();
    }, [id]);

    const loadInitiativeData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const [initiativeResponse, statsResponse] = await Promise.all([
                initiativeService.getById(id),
                initiativeService.getStats(id)
            ]);
            
            setInitiative(initiativeResponse.initiative);
            setStats(statsResponse);
        } catch (err) {
            setError('Failed to load initiative: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading initiative:', err);
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
            const response = await initiativeService.update(id, updateData);
            setInitiative(response.initiative);
            setIsEditing(false);
            await loadInitiativeData(); // Reload stats
        } catch (err) {
            setError('Failed to update initiative: ' + (err.response?.data?.detail || err.message));
        }
    };

    const handleDelete = async () => {
        if (window.confirm('Are you sure you want to delete this initiative?')) {
            try {
                await initiativeService.delete(id);
                navigate('/initiatives');
            } catch (err) {
                setError('Failed to delete initiative: ' + (err.response?.data?.detail || err.message));
            }
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active':
                return 'bg-green-100 text-green-800';
            case 'paused':
                return 'bg-yellow-100 text-yellow-800';
            case 'completed':
                return 'bg-purple-100 text-purple-800';
            case 'archived':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="p-6">Loading initiative...</div>;
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
                <button 
                    onClick={loadInitiativeData}
                    className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!initiative) {
        return (
            <div className="p-6">
                <div className="text-center text-gray-500">
                    Initiative not found
                </div>
            </div>
        );
    }

    if (isEditing) {
        return (
            <div className="p-6">
                <InitiativeForm
                    initiative={initiative}
                    onSubmit={handleUpdate}
                    onCancel={handleCancelEdit}
                />
            </div>
        );
    }

    return (
        <div className="p-6 max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <h1 className="text-2xl font-bold">{initiative.title}</h1>
                        <span className={`px-3 py-1 text-sm rounded-full ${getStatusColor(initiative.status)}`}>
                            {initiative.status}
                        </span>
                        {initiative.is_template && (
                            <span className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full">
                                Template
                            </span>
                        )}
                    </div>
                    {initiative.description && (
                        <p className="text-gray-600">{initiative.description}</p>
                    )}
                </div>
                
                <div className="flex gap-2">
                    <button
                        onClick={() => navigate(`/initiatives/${id}/tasks`)}
                        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    >
                        View Tasks
                    </button>
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
                        onClick={() => navigate('/initiatives')}
                        className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                    >
                        Back
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
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
                        <div className="text-2xl font-bold text-purple-600">
                            {stats.completion_rate ? `${Math.round(stats.completion_rate)}%` : '0%'}
                        </div>
                        <div className="text-sm text-gray-500">Completion Rate</div>
                    </div>
                </div>
            )}

            {/* Details Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Schedule Details */}
                <div className="bg-white p-6 rounded-lg border shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">Schedule Details</h3>
                    <dl className="space-y-3">
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Frequency</dt>
                            <dd className="text-sm text-gray-900">{initiative.frequency}</dd>
                        </div>
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Interval</dt>
                            <dd className="text-sm text-gray-900">Every {initiative.interval} {initiative.frequency}</dd>
                        </div>
                        {initiative.preferred_start_time && (
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Preferred Start Time</dt>
                                <dd className="text-sm text-gray-900">{initiative.preferred_start_time}</dd>
                            </div>
                        )}
                        {initiative.estimated_duration_minutes && (
                            <div>
                                <dt className="text-sm font-medium text-gray-500">Estimated Duration</dt>
                                <dd className="text-sm text-gray-900">{initiative.estimated_duration_minutes} minutes</dd>
                            </div>
                        )}
                    </dl>
                </div>

                {/* System Details */}
                <div className="bg-white p-6 rounded-lg border shadow-sm">
                    <h3 className="text-lg font-semibold mb-4">System Details</h3>
                    <dl className="space-y-3">
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Initiative ID</dt>
                            <dd className="text-sm text-gray-900 font-mono">{initiative.id}</dd>
                        </div>
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Created</dt>
                            <dd className="text-sm text-gray-900">
                                {new Date(initiative.created_at).toLocaleDateString()} at{' '}
                                {new Date(initiative.created_at).toLocaleTimeString()}
                            </dd>
                        </div>
                        <div>
                            <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                            <dd className="text-sm text-gray-900">
                                {new Date(initiative.updated_at).toLocaleDateString()} at{' '}
                                {new Date(initiative.updated_at).toLocaleTimeString()}
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>

            {/* Recent Tasks */}
            {stats?.recent_tasks?.length > 0 && (
                <div className="bg-white p-6 rounded-lg border shadow-sm mt-6">
                    <h3 className="text-lg font-semibold mb-4">Recent Tasks</h3>
                    <div className="space-y-3">
                        {stats.recent_tasks.map((task) => (
                            <div key={task.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                                <div>
                                    <div className="font-medium">{task.title}</div>
                                    <div className="text-sm text-gray-500">
                                        Due: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}
                                    </div>
                                </div>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                    task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                    task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                                    'bg-gray-100 text-gray-800'
                                }`}>
                                    {task.status}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default InitiativeDetail;