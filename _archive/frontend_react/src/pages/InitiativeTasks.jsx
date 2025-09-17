/**
 * Initiative Tasks page component
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { initiativeService } from '../services/initiativeService';
import { taskService } from '../services/taskService';

const InitiativeTasks = () => {
    const { id: initiativeId } = useParams();
    const navigate = useNavigate();
    
    const [initiative, setInitiative] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadData();
    }, [initiativeId]);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const [initiativeResponse, tasksResponse] = await Promise.all([
                initiativeService.getById(initiativeId),
                taskService.getByInitiative(initiativeId)
            ]);
            
            setInitiative(initiativeResponse);
            setTasks(tasksResponse);
        } catch (err) {
            setError('Failed to load data: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading initiative tasks:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleComplete = async (taskId) => {
        try {
            await taskService.completeTask(taskId);
            await loadData(); // Reload to update counts
        } catch (error) {
            console.error('Failed to complete task:', error);
        }
    };

    const handleDelete = async (taskId) => {
        if (window.confirm('Are you sure you want to delete this task?')) {
            try {
                await taskService.deleteTask(taskId);
                await loadData(); // Reload to update counts
            } catch (error) {
                console.error('Failed to delete task:', error);
            }
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'blocked':
                return 'bg-red-100 text-red-800';
            case 'active':
                return 'bg-blue-100 text-blue-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'critical':
                return 'bg-red-100 text-red-800';
            case 'high':
                return 'bg-orange-100 text-orange-800';
            case 'medium':
                return 'bg-yellow-100 text-yellow-800';
            case 'low':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="p-6">Loading tasks...</div>;
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
                <button 
                    onClick={loadData}
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

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <nav className="text-sm text-gray-500 mb-2">
                        <Link to="/initiatives" className="hover:text-gray-700">Initiatives</Link>
                        {' > '}
                        <Link to={`/initiatives/${initiativeId}`} className="hover:text-gray-700">
                            {initiative.title}
                        </Link>
                        {' > '}
                        <span className="text-gray-900">Tasks</span>
                    </nav>
                    <h1 className="text-2xl font-bold">Tasks for {initiative.title}</h1>
                    {initiative.description && (
                        <p className="text-gray-600 mt-1">{initiative.description}</p>
                    )}
                </div>
                
                <div className="flex gap-2">
                    <Link
                        to={`/tasks/new?initiative_id=${initiativeId}`}
                        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                    >
                        Add Task
                    </Link>
                    <button
                        onClick={() => navigate(`/initiatives/${initiativeId}`)}
                        className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                    >
                        Back to Initiative
                    </button>
                </div>
            </div>

            {/* Task Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="text-2xl font-bold text-blue-600">{tasks.length}</div>
                    <div className="text-sm text-gray-500">Total Tasks</div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="text-2xl font-bold text-green-600">
                        {tasks.filter(t => t.status === 'completed').length}
                    </div>
                    <div className="text-sm text-gray-500">Completed</div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="text-2xl font-bold text-orange-600">
                        {tasks.filter(t => t.status === 'active').length}
                    </div>
                    <div className="text-sm text-gray-500">Active</div>
                </div>
                <div className="bg-white p-4 rounded-lg border shadow-sm">
                    <div className="text-2xl font-bold text-red-600">
                        {tasks.filter(t => t.status === 'blocked').length}
                    </div>
                    <div className="text-sm text-gray-500">Blocked</div>
                </div>
            </div>

            {/* Tasks List */}
            <div className="bg-white rounded-lg shadow">
                {tasks.length === 0 ? (
                    <div className="p-8 text-center">
                        <p className="text-gray-500 mb-4">No tasks yet for this initiative.</p>
                        <Link
                            to={`/tasks/new?initiative_id=${initiativeId}`}
                            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        >
                            Create First Task
                        </Link>
                    </div>
                ) : (
                    <div className="divide-y">
                        {tasks.map((task) => (
                            <div key={task.id} className="p-4 hover:bg-gray-50">
                                <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="font-semibold">{task.title}</h3>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                                                {task.status}
                                            </span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(task.priority)}`}>
                                                {task.priority}
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-500 mb-2">
                                            Duration: {task.duration} min | Urgency: {task.urgency}/10
                                            {task.is_recurring && task.recurrence_pattern && (
                                                <span className="ml-2 text-blue-600">
                                                    (Repeats {task.recurrence_pattern.frequency === 'daily' ? 'daily' :
                                                             task.recurrence_pattern.frequency === 'weekly' ? 'weekly' :
                                                             task.recurrence_pattern.frequency === 'monthly' ? 'monthly' : 'yearly'})
                                                </span>
                                            )}
                                        </div>
                                        {task.description && (
                                            <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                                        )}
                                        {task.due_date && (
                                            <p className="text-sm text-gray-500">
                                                Due: {new Date(task.due_date).toLocaleDateString()}
                                                {task.due_time && ` at ${task.due_time}`}
                                            </p>
                                        )}
                                    </div>
                                    <div className="flex space-x-2">
                                        {task.status !== 'completed' && (
                                            <button
                                                onClick={() => handleComplete(task.id)}
                                                className="text-green-600 hover:text-green-800 px-3 py-1 rounded border border-green-300 hover:bg-green-50"
                                            >
                                                Complete
                                            </button>
                                        )}
                                        <button
                                            onClick={() => handleDelete(task.id)}
                                            className="text-red-600 hover:text-red-800 px-3 py-1 rounded border border-red-300 hover:bg-red-50"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default InitiativeTasks;