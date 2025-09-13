/**
 * Initiative form component for create/edit
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';

const InitiativeForm = ({ initiative = null, onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        frequency: 'weekly',
        interval: 1,
        status: 'active',
        is_template: false,
        preferred_start_time: '',
        estimated_duration_minutes: ''
    });

    const [errors, setErrors] = useState({});

    useEffect(() => {
        if (initiative) {
            setFormData({
                title: initiative.title || '',
                description: initiative.description || '',
                frequency: initiative.frequency || 'weekly',
                interval: initiative.interval || 1,
                status: initiative.status || 'active',
                is_template: initiative.is_template || false,
                preferred_start_time: initiative.preferred_start_time || '',
                estimated_duration_minutes: initiative.estimated_duration_minutes || ''
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
        
        if (formData.interval < 1) {
            newErrors.interval = 'Interval must be at least 1';
        }
        
        if (formData.estimated_duration_minutes && formData.estimated_duration_minutes < 1) {
            newErrors.estimated_duration_minutes = 'Duration must be positive';
        }
        
        if (formData.preferred_start_time && !/^([0-1]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$/.test(formData.preferred_start_time)) {
            newErrors.preferred_start_time = 'Time must be in HH:MM or HH:MM:SS format';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validateForm()) {
            const submitData = {
                ...formData,
                interval: parseInt(formData.interval),
                estimated_duration_minutes: formData.estimated_duration_minutes ? 
                    parseInt(formData.estimated_duration_minutes) : null
            };
            onSubmit(submitData);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-semibold mb-6">
                {initiative ? 'Edit Initiative' : 'New Initiative'}
            </h2>
            
            <div className="grid gap-6">
                {/* Title */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Title *
                    </label>
                    <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            errors.title ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="Enter initiative title"
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
                        placeholder="Describe the initiative"
                    />
                </div>

                {/* Frequency and Interval */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Frequency
                        </label>
                        <select
                            name="frequency"
                            value={formData.frequency}
                            onChange={handleChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="quarterly">Quarterly</option>
                            <option value="yearly">Yearly</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Interval *
                        </label>
                        <input
                            type="number"
                            name="interval"
                            value={formData.interval}
                            onChange={handleChange}
                            min="1"
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                errors.interval ? 'border-red-500' : 'border-gray-300'
                            }`}
                            placeholder="Every X periods"
                        />
                        {errors.interval && <p className="text-red-500 text-sm mt-1">{errors.interval}</p>}
                    </div>
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
                </div>

                {/* Schedule Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Preferred Start Time
                        </label>
                        <input
                            type="time"
                            name="preferred_start_time"
                            value={formData.preferred_start_time}
                            onChange={handleChange}
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                errors.preferred_start_time ? 'border-red-500' : 'border-gray-300'
                            }`}
                        />
                        {errors.preferred_start_time && <p className="text-red-500 text-sm mt-1">{errors.preferred_start_time}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Estimated Duration (minutes)
                        </label>
                        <input
                            type="number"
                            name="estimated_duration_minutes"
                            value={formData.estimated_duration_minutes}
                            onChange={handleChange}
                            min="1"
                            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                errors.estimated_duration_minutes ? 'border-red-500' : 'border-gray-300'
                            }`}
                            placeholder="Duration in minutes"
                        />
                        {errors.estimated_duration_minutes && <p className="text-red-500 text-sm mt-1">{errors.estimated_duration_minutes}</p>}
                    </div>
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

export default InitiativeForm;