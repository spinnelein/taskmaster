/**
 * Meals page component
 * NO EMOJIS
 */
import React, { useState, useEffect } from 'react';
import { mealService } from '../services/mealService';

const Meals = () => {
    const [meals, setMeals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('upcoming'); // 'upcoming', 'all'

    useEffect(() => {
        loadMeals();
    }, [viewMode]);

    const loadMeals = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = viewMode === 'upcoming' 
                ? await mealService.getUpcoming(7)
                : await mealService.getAll();
                
            setMeals(response.meals || []);
        } catch (err) {
            setError('Failed to load meals: ' + (err.response?.data?.detail || err.message));
            console.error('Error loading meals:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Not scheduled';
        return new Date(dateString).toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getMealTypeColor = (type) => {
        switch (type) {
            case 'breakfast': return 'bg-yellow-100 text-yellow-800';
            case 'lunch': return 'bg-blue-100 text-blue-800';
            case 'dinner': return 'bg-purple-100 text-purple-800';
            case 'snack': return 'bg-green-100 text-green-800';
            case 'dessert': return 'bg-pink-100 text-pink-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'planned': return 'bg-blue-100 text-blue-800';
            case 'shopping': return 'bg-yellow-100 text-yellow-800';
            case 'prepping': return 'bg-orange-100 text-orange-800';
            case 'cooking': return 'bg-red-100 text-red-800';
            case 'served': return 'bg-green-100 text-green-800';
            case 'cancelled': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="p-6">Loading meals...</div>;
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                    {error}
                </div>
                <button 
                    onClick={loadMeals}
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
                <h1 className="text-2xl font-bold">Meals</h1>
                <div className="flex items-center gap-4">
                    <div className="flex bg-gray-200 rounded-lg p-1">
                        <button
                            onClick={() => setViewMode('upcoming')}
                            className={`px-4 py-2 rounded-md transition-colors ${
                                viewMode === 'upcoming' 
                                    ? 'bg-white text-blue-600 shadow-sm' 
                                    : 'text-gray-600 hover:text-gray-900'
                            }`}
                        >
                            Upcoming
                        </button>
                        <button
                            onClick={() => setViewMode('all')}
                            className={`px-4 py-2 rounded-md transition-colors ${
                                viewMode === 'all' 
                                    ? 'bg-white text-blue-600 shadow-sm' 
                                    : 'text-gray-600 hover:text-gray-900'
                            }`}
                        >
                            All
                        </button>
                    </div>
                    <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                        Plan New Meal
                    </button>
                </div>
            </div>

            {meals.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                    {viewMode === 'upcoming' 
                        ? 'No upcoming meals planned. Plan your next meal!' 
                        : 'No meals found. Start planning your meals!'
                    }
                </div>
            ) : (
                <div className="space-y-4">
                    {meals.map((meal) => (
                        <div key={meal.id} className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                        {meal.title}
                                    </h3>
                                    <div className="flex items-center gap-3 text-sm">
                                        <span className={`px-2 py-1 rounded-full ${getMealTypeColor(meal.meal_type)}`}>
                                            {meal.meal_type}
                                        </span>
                                        <span className={`px-2 py-1 rounded-full ${getStatusColor(meal.status)}`}>
                                            {meal.status}
                                        </span>
                                        <span className="text-gray-500">
                                            Serves {meal.serves_count}
                                        </span>
                                    </div>
                                </div>
                                <div className="text-right text-sm text-gray-500">
                                    <div>Planned: {formatDate(meal.planned_date)}</div>
                                    {meal.serve_time && (
                                        <div>Serve: {formatDate(meal.serve_time)}</div>
                                    )}
                                </div>
                            </div>

                            {meal.description && (
                                <p className="text-gray-600 mb-4">{meal.description}</p>
                            )}

                            {meal.dishes && meal.dishes.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="font-medium text-gray-900 mb-2">Dishes:</h4>
                                    <div className="flex flex-wrap gap-2">
                                        {meal.dishes.map((dish, index) => (
                                            <span 
                                                key={index}
                                                className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm"
                                            >
                                                {dish.dish_title} ({dish.servings}x)
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {meal.dietary_tags && meal.dietary_tags.length > 0 && (
                                <div className="mb-4">
                                    <div className="flex flex-wrap gap-1">
                                        {meal.dietary_tags.map((tag, index) => (
                                            <span 
                                                key={index}
                                                className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs"
                                            >
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-between items-center">
                                <div className="text-sm text-gray-500">
                                    {meal.estimated_calories_per_serving && (
                                        <span>{meal.estimated_calories_per_serving} cal/serving</span>
                                    )}
                                    {meal.estimated_cost && (
                                        <span className="ml-4">${meal.estimated_cost.toFixed(2)} estimated</span>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <button className="text-blue-600 hover:text-blue-800 text-sm">
                                        View Details
                                    </button>
                                    <button className="text-green-600 hover:text-green-800 text-sm">
                                        Generate Prep Tasks
                                    </button>
                                    <button className="text-gray-600 hover:text-gray-800 text-sm">
                                        Edit
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Meals;