/**
 * Edit Initiative page component
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import InitiativeContainerForm from '../components/forms/InitiativeContainerForm';
import { initiativeService } from '../services/initiativeService';

const EditInitiative = () => {
    const navigate = useNavigate();
    const { id } = useParams();
    const [initiative, setInitiative] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadInitiative();
    }, [id]);

    const loadInitiative = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await initiativeService.getById(id);
            setInitiative(data);
        } catch (err) {
            setError('Failed to load initiative: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading initiative:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (formData) => {
        try {
            setIsSubmitting(true);
            setError(null);
            
            const updatedInitiative = await initiativeService.update(id, formData);
            
            // Navigate to the initiative detail page
            navigate(`/initiatives/${updatedInitiative.id}`);
        } catch (err) {
            setError('Failed to update initiative: ' + (err.response?.data?.detail || err.message));
            console.error('Error updating initiative:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancel = () => {
        navigate(`/initiatives/${id}`);
    };

    if (loading) {
        return (
            <div className="p-6">
                <div className="max-w-4xl mx-auto">
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="text-gray-600 mt-2">Loading initiative...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error && !initiative) {
        return (
            <div className="p-6">
                <div className="max-w-4xl mx-auto">
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                        {error}
                    </div>
                    <div className="mt-4 flex gap-2">
                        <button 
                            onClick={loadInitiative}
                            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                        >
                            Retry
                        </button>
                        <button 
                            onClick={() => navigate('/initiatives')}
                            className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
                        >
                            Back to Initiatives
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold">Edit Initiative</h1>
                    <p className="text-gray-600 mt-1">
                        Update the details of your initiative.
                    </p>
                </div>

                {error && (
                    <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                        {error}
                    </div>
                )}

                <div className="relative">
                    {isSubmitting && (
                        <div className="absolute inset-0 bg-gray-100 bg-opacity-50 flex items-center justify-center z-10 rounded-lg">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                                <p className="text-gray-600 mt-2">Updating initiative...</p>
                            </div>
                        </div>
                    )}
                    
                    {initiative && (
                        <InitiativeContainerForm
                            initiative={initiative}
                            onSubmit={handleSubmit}
                            onCancel={handleCancel}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default EditInitiative;