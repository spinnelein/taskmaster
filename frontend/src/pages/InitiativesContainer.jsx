/**
 * Initiatives page component - Container view
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { initiativeService } from '../services/initiativeService';
import taskService from '../services/taskService';

const InitiativesContainer = () => {
    const [initiatives, setInitiatives] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showActiveOnly, setShowActiveOnly] = useState(true);

    useEffect(() => {
        loadInitiatives();
    }, [showActiveOnly]);

    const loadInitiatives = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await initiativeService.getAll(showActiveOnly);
            
            // For each initiative, get task counts
            const initiativesWithStats = await Promise.all(
                (response.initiatives || []).map(async (initiative) => {
                    try {
                        // Get tasks for this initiative
                        const tasks = await taskService.getByInitiative(initiative.id);
                        const activeTasks = tasks.filter(t => t.status === 'active').length;
                        const completedTasks = tasks.filter(t => t.status === 'completed').length;
                        const blockedTasks = tasks.filter(t => t.status === 'blocked').length;
                        
                        return {
                            ...initiative,
                            taskStats: {
                                total: tasks.length,
                                active: activeTasks,
                                completed: completedTasks,
                                blocked: blockedTasks
                            }
                        };
                    } catch (err) {
                        console.error(`Error loading tasks for initiative ${initiative.id}:`, err);
                        return {
                            ...initiative,
                            taskStats: { total: 0, active: 0, completed: 0, blocked: 0 }
                        };
                    }
                })
            );
            
            setInitiatives(initiativesWithStats);
        } catch (err) {
            setError('Failed to load initiatives: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading initiatives:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleToggleActive = () => {
        setShowActiveOnly(!showActiveOnly);
    };

    const handleCompleteInitiative = async (initiativeId) => {
        if (!window.confirm('Are you sure you want to mark this initiative as completed? This will also mark all associated tasks as completed.')) {
            return;
        }

        try {
            await initiativeService.complete(initiativeId);
            // Reload initiatives to reflect the change
            await loadInitiatives();
        } catch (err) {
            alert('Failed to complete initiative: ' + (err.response?.data?.detail || err.message));
            console.error('Error completing initiative:', err);
        }
    };

    if (loading) {
        return <div className="p-6">Loading initiatives...</div>;
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
                <button 
                    onClick={loadInitiatives}
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
                <h1 className="text-2xl font-bold">Initiatives</h1>
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
                    <Link 
                        to="/initiatives/new"
                        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 inline-block"
                    >
                        New Initiative
                    </Link>
                </div>
            </div>

            {initiatives.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                    No initiatives found. Create your first initiative to organize your tasks!
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {initiatives.map((initiative) => (
                        <div key={initiative.id} className="bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-lg font-semibold text-gray-900">
                                    {initiative.title}
                                </h3>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                    initiative.status === 'active' 
                                        ? 'bg-green-100 text-green-800' 
                                        : initiative.status === 'paused'
                                        ? 'bg-yellow-100 text-yellow-800'
                                        : initiative.status === 'completed'
                                        ? 'bg-blue-100 text-blue-800'
                                        : 'bg-gray-100 text-gray-800'
                                }`}>
                                    {initiative.status}
                                </span>
                            </div>
                            
                            {initiative.description && (
                                <p className="text-gray-600 text-sm mb-3">
                                    {initiative.description}
                                </p>
                            )}
                            
                            {/* Task Statistics */}
                            <div className="border-t pt-3 mt-3">
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                    <div className="text-gray-600">
                                        Total Tasks: <span className="font-medium text-gray-900">{initiative.taskStats.total}</span>
                                    </div>
                                    <div className="text-green-600">
                                        Active: <span className="font-medium">{initiative.taskStats.active}</span>
                                    </div>
                                    <div className="text-blue-600">
                                        Completed: <span className="font-medium">{initiative.taskStats.completed}</span>
                                    </div>
                                    <div className="text-yellow-600">
                                        Blocked: <span className="font-medium">{initiative.taskStats.blocked}</span>
                                    </div>
                                </div>
                                
                                {/* Progress Bar */}
                                {initiative.taskStats.total > 0 && (
                                    <div className="mt-3">
                                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                                            <span>Progress</span>
                                            <span>{Math.round((initiative.taskStats.completed / initiative.taskStats.total) * 100)}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                            <div 
                                                className="bg-blue-600 h-2 rounded-full"
                                                style={{ width: `${(initiative.taskStats.completed / initiative.taskStats.total) * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                )}
                                
                                {/* Target completion if set */}
                                {initiative.target_completion_count && (
                                    <div className="mt-2 text-sm text-gray-600">
                                        Target: {initiative.current_completion_count || 0} / {initiative.target_completion_count}
                                    </div>
                                )}
                            </div>
                            
                            <div className="mt-4 flex gap-2 flex-wrap">
                                <Link 
                                    to={`/initiatives/${initiative.id}`}
                                    className="text-blue-600 hover:text-blue-800 text-sm"
                                >
                                    View Details
                                </Link>
                                <Link 
                                    to={`/initiatives/${initiative.id}/tasks`}
                                    className="text-green-600 hover:text-green-800 text-sm"
                                >
                                    Manage Tasks
                                </Link>
                                <Link 
                                    to={`/initiatives/${initiative.id}/edit`}
                                    className="text-gray-600 hover:text-gray-800 text-sm"
                                >
                                    Edit
                                </Link>
                                {initiative.status === 'active' && (
                                    <button
                                        onClick={() => handleCompleteInitiative(initiative.id)}
                                        className="text-purple-600 hover:text-purple-800 text-sm"
                                    >
                                        Complete
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default InitiativesContainer;