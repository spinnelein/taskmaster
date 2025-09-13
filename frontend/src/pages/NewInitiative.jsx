/**
 * New Initiative page component
 * NO EMOJIS
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import InitiativeContainerForm from '../components/forms/InitiativeContainerForm';
import { initiativeService } from '../services/initiativeService';

const NewInitiative = () => {
    const navigate = useNavigate();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (formData) => {
        try {
            setIsSubmitting(true);
            setError(null);
            
            const newInitiative = await initiativeService.create(formData);
            
            // Navigate to the new initiative detail page
            navigate(`/initiatives/${newInitiative.id}`);
        } catch (err) {
            setError('Failed to create initiative: ' + (err.response?.data?.detail || err.message));
            console.error('Error creating initiative:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancel = () => {
        navigate('/initiatives');
    };

    return (
        <div className="p-6">
            <div className="max-w-4xl mx-auto">
                <div className="mb-6">
                    <h1 className="text-2xl font-bold">New Initiative</h1>
                    <p className="text-gray-600 mt-1">
                        Create a new initiative to organize and group related tasks.
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
                                <p className="text-gray-600 mt-2">Creating initiative...</p>
                            </div>
                        </div>
                    )}
                    
                    <InitiativeContainerForm
                        initiative={null}
                        onSubmit={handleSubmit}
                        onCancel={handleCancel}
                    />
                </div>
            </div>
        </div>
    );
};

export default NewInitiative;