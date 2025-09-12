/**
 * Initiatives page component
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { initiativeService } from '../services/initiativeService';

const Initiatives = () => {
    const [initiatives, setInitiatives] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showActiveOnly, setShowActiveOnly] = useState(false);

    useEffect(() => {
        loadInitiatives();
    }, [showActiveOnly]);

    const loadInitiatives = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await initiativeService.getAll(showActiveOnly);
            setInitiatives(response.initiatives || []);
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
                    <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                        New Initiative
                    </button>
                </div>
            </div>

            {initiatives.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                    No initiatives found. Create your first initiative to get started!
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
                            
                            <div className="text-sm text-gray-500 space-y-1">
                                <div>Frequency: {initiative.frequency} (every {initiative.interval})</div>
                                {initiative.estimated_duration_minutes && (
                                    <div>Duration: {initiative.estimated_duration_minutes} minutes</div>
                                )}
                                {initiative.is_template && (
                                    <div className="text-blue-600 font-medium">Template</div>
                                )}
                            </div>
                            
                            <div className="mt-4 flex gap-2">
                                <button className="text-blue-600 hover:text-blue-800 text-sm">
                                    View Details
                                </button>
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

export default Initiatives;