/**
 * Initiative form component for create/edit - Container version
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';

const InitiativeContainerForm = ({ initiative = null, onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        status: 'active',
        is_template: false,
        target_completion_count: ''
    });

    const [errors, setErrors] = useState({});

    useEffect(() => {
        if (initiative) {
            setFormData({
                title: initiative.title || '',
                description: initiative.description || '',
                status: initiative.status || 'active',
                is_template: initiative.is_template || false,
                target_completion_count: initiative.target_completion_count || ''
            });
        }
    }, [initiative]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
        
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.title.trim()) {
            newErrors.title = 'Title is required';
        }
        
        if (formData.target_completion_count && formData.target_completion_count < 1) {
            newErrors.target_completion_count = 'Target must be at least 1';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validateForm()) {
            const submitData = {
                ...formData,
                target_completion_count: formData.target_completion_count ? 
                    parseInt(formData.target_completion_count) : null
            };
            onSubmit(submitData);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-semibold mb-6">
                {initiative ? 'Edit Initiative' : 'New Initiative'}
            </h2>
            
            <div className="mb-4 bg-blue-50 border border-blue-200 rounded p-4">
                <p className="text-sm text-blue-800">
                    <strong>Initiative:</strong> A container for organizing related tasks and events. 
                    For example, "Health & Fitness" could contain tasks like "Morning workout", 
                    "Meal prep", and "Take vitamins".
                </p>
            </div>
            
            <div className="grid gap-6">
                {/* Title */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Initiative Title *
                    </label>
                    <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            errors.title ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="e.g., Health & Fitness, Home Maintenance, Learning Python"
                    />
                    {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
                </div>

                {/* Description */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                    </label>
                    <textarea
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Describe the purpose of this initiative and what types of tasks it will contain"
                    />
                </div>

                {/* Status */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Status
                    </label>
                    <select
                        name="status"
                        value={formData.status}
                        onChange={handleChange}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="active">Active</option>
                        <option value="paused">Paused</option>
                        <option value="completed">Completed</option>
                        <option value="archived">Archived</option>
                    </select>
                    <p className="text-sm text-gray-500 mt-1">
                        Active initiatives will show their tasks in your task queue
                    </p>
                </div>

                {/* Target Completion Count (Optional) */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Target Completion Count (Optional)
                    </label>
                    <input
                        type="number"
                        name="target_completion_count"
                        value={formData.target_completion_count}
                        onChange={handleChange}
                        min="1"
                        className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            errors.target_completion_count ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="e.g., 30 for '30 workouts'"
                    />
                    {errors.target_completion_count && <p className="text-red-500 text-sm mt-1">{errors.target_completion_count}</p>}
                    <p className="text-sm text-gray-500 mt-1">
                        Set a goal for how many times tasks in this initiative should be completed
                    </p>
                </div>

                {/* Template Checkbox */}
                <div className="flex items-center">
                    <input
                        type="checkbox"
                        name="is_template"
                        checked={formData.is_template}
                        onChange={handleChange}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-700">
                        Save as template for future use
                    </label>
                </div>

                {/* Info about adding tasks */}
                {!initiative && (
                    <div className="bg-gray-50 border border-gray-200 rounded p-4">
                        <p className="text-sm text-gray-700">
                            <strong>Next step:</strong> After creating this initiative, you'll be able to add tasks to it. 
                            Tasks can be one-time or recurring, and each can have its own schedule and settings.
                        </p>
                    </div>
                )}
            </div>

            {/* Form Actions */}
            <div className="flex gap-3 pt-6 mt-6 border-t">
                <button
                    type="submit"
                    className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {initiative ? 'Update Initiative' : 'Create Initiative'}
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                    Cancel
                </button>
            </div>
        </form>
    );
};

export default InitiativeContainerForm;