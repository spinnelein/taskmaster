"""
Meals and Dishes API Routes

Handles meal planning functionality including dish management,
meal creation, and meal-event integration.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db, Dish, Recipe, Meal, MealDish, Event
import uuid
import json
import logging

logger = logging.getLogger(__name__)
meals_bp = Blueprint('meals', __name__)


@meals_bp.route('/dishes', methods=['GET'])
def get_dishes():
    """Get all dishes with recipe data"""
    try:
        dishes = Dish.query.order_by(Dish.title).all()
        return jsonify([dish.to_dict_with_recipe() for dish in dishes])
    except Exception as e:
        logger.error(f"Error getting dishes: {e}")
        return jsonify({'error': f"Failed to get dishes: {str(e)}"}), 500


@meals_bp.route('/dishes/<dish_id>', methods=['GET'])
def get_dish(dish_id):
    """Get a specific dish with recipe data"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        return jsonify(dish.to_dict_with_recipe())
    except Exception as e:
        logger.error(f"Error getting dish {dish_id}: {e}")
        return jsonify({'error': f"Failed to get dish: {str(e)}"}), 500


@meals_bp.route('/dishes', methods=['POST'])
def create_dish():
    """Create a new dish"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('dish_type'):
            return jsonify({'error': 'Dish type is required'}), 400
        if not data.get('difficulty'):
            return jsonify({'error': 'Difficulty is required'}), 400
        if not data.get('ingredients') or len(data.get('ingredients', [])) == 0:
            return jsonify({'error': 'Ingredients are required'}), 400
        if not data.get('instructions') or len(data.get('instructions', [])) == 0:
            return jsonify({'error': 'Instructions are required'}), 400
        
        # Handle dietary tags
        dietary_tags = data.get('dietary_tags', [])
        if isinstance(dietary_tags, list):
            dietary_tags_json = json.dumps(dietary_tags)
        else:
            dietary_tags_json = None
        
        # Create recipe first
        recipe_id = str(uuid.uuid4())
        recipe = Recipe(
            id=recipe_id,
            title=data['title'] + " Recipe",
            description=data.get('description', ''),
            ingredients=json.dumps(data['ingredients']),
            instructions=json.dumps(data['instructions']),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        dish = Dish(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data.get('description'),
            dish_type=data['dish_type'],
            difficulty=data['difficulty'],
            cuisine=data.get('cuisine'),
            prep_time_minutes=data.get('prep_time_minutes'),
            cook_time_minutes=data.get('cook_time_minutes'),
            total_time_minutes=data.get('total_time_minutes'),
            advance_prep_hours=data.get('advance_prep_hours'),
            advance_prep_description=data.get('advance_prep_description'),
            default_servings=data.get('default_servings'),
            calories_per_serving=data.get('calories_per_serving'),
            estimated_cost_per_serving=data.get('estimated_cost_per_serving'),
            dietary_tags=dietary_tags_json,
            recipe_id=recipe_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(recipe)
        db.session.add(dish)
        db.session.commit()
        
        return jsonify(dish.to_dict_with_recipe()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating dish: {e}")
        return jsonify({'error': f"Failed to create dish: {str(e)}"}), 500


@meals_bp.route('/dishes/<dish_id>', methods=['PUT'])
def update_dish(dish_id):
    """Update a dish"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        data = request.json
        
        # Update dish fields
        if 'title' in data:
            dish.title = data['title']
        if 'description' in data:
            dish.description = data['description']
        if 'dish_type' in data:
            dish.dish_type = data['dish_type']
        if 'difficulty' in data:
            dish.difficulty = data['difficulty']
        if 'cuisine' in data:
            dish.cuisine = data['cuisine']
        if 'prep_time_minutes' in data:
            dish.prep_time_minutes = data['prep_time_minutes']
        if 'cook_time_minutes' in data:
            dish.cook_time_minutes = data['cook_time_minutes']
        if 'total_time_minutes' in data:
            dish.total_time_minutes = data['total_time_minutes']
        if 'advance_prep_hours' in data:
            dish.advance_prep_hours = data['advance_prep_hours']
        if 'advance_prep_description' in data:
            dish.advance_prep_description = data['advance_prep_description']
        if 'default_servings' in data:
            dish.default_servings = data['default_servings']
        if 'calories_per_serving' in data:
            dish.calories_per_serving = data['calories_per_serving']
        if 'estimated_cost_per_serving' in data:
            dish.estimated_cost_per_serving = data['estimated_cost_per_serving']
        
        # Handle dietary tags
        if 'dietary_tags' in data:
            dietary_tags = data['dietary_tags']
            if isinstance(dietary_tags, list):
                dish.dietary_tags = json.dumps(dietary_tags)
            else:
                dish.dietary_tags = None
        
        # Update recipe if recipe data is provided
        if dish.recipe and ('ingredients' in data or 'instructions' in data):
            recipe = dish.recipe
            if 'ingredients' in data:
                recipe.ingredients = json.dumps(data['ingredients'])
            if 'instructions' in data:
                recipe.instructions = json.dumps(data['instructions'])
            recipe.updated_at = datetime.utcnow()
        
        dish.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(dish.to_dict_with_recipe())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating dish {dish_id}: {e}")
        return jsonify({'error': f"Failed to update dish: {str(e)}"}), 500


@meals_bp.route('/dishes/<dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    """Delete a dish"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        
        # Also delete the associated recipe
        if dish.recipe:
            db.session.delete(dish.recipe)
        
        db.session.delete(dish)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Dish deleted'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting dish {dish_id}: {e}")
        return jsonify({'error': f"Failed to delete dish: {str(e)}"}), 500


@meals_bp.route('/meals', methods=['GET'])
def get_meals():
    """Get all meals with dish data, optionally filtered by tags"""
    try:
        # Get query parameters for filtering
        tags_param = request.args.get('tags', '').strip()
        
        # Start with base query
        query = Meal.query
        
        # Apply tag filtering if tags are specified
        if tags_param:
            # Split tags by comma and clean them
            requested_tags = [tag.strip() for tag in tags_param.split(',') if tag.strip()]
            
            if requested_tags:
                # Filter meals that have any of the requested tags
                filtered_meals = []
                all_meals = query.all()
                
                for meal in all_meals:
                    # Parse the meal's dietary tags
                    meal_tags = []
                    if meal.dietary_tags:
                        try:
                            meal_tags = json.loads(meal.dietary_tags)
                            if not isinstance(meal_tags, list):
                                meal_tags = []
                        except:
                            meal_tags = []
                    
                    # Check if any requested tag matches (case-insensitive)
                    meal_tags_lower = [tag.lower() for tag in meal_tags]
                    for requested_tag in requested_tags:
                        if requested_tag.lower() in meal_tags_lower:
                            filtered_meals.append(meal)
                            break
                
                # Return filtered results
                return jsonify([meal.to_dict_with_dishes() for meal in filtered_meals])
        
        # No filtering - return all meals
        meals = query.order_by(Meal.title).all()
        return jsonify([meal.to_dict_with_dishes() for meal in meals])
        
    except Exception as e:
        logger.error(f"Error getting meals: {e}")
        return jsonify({'error': f"Failed to get meals: {str(e)}"}), 500


@meals_bp.route('/meals/<meal_id>', methods=['GET'])
def get_meal(meal_id):
    """Get a specific meal with dish data"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        return jsonify(meal.to_dict_with_dishes())
    except Exception as e:
        logger.error(f"Error getting meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to get meal: {str(e)}"}), 500


@meals_bp.route('/meals', methods=['POST'])
def create_meal():
    """Create a new meal"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('meal_type'):
            return jsonify({'error': 'Meal type is required'}), 400
        
        # Handle dietary tags (used for categorization like Mexican, Italian, Bowl)
        dietary_tags = data.get('dietary_tags', [])
        if isinstance(dietary_tags, list):
            dietary_tags_json = json.dumps(dietary_tags)
        else:
            dietary_tags_json = None
        
        meal = Meal(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data.get('description'),
            meal_type=data['meal_type'],
            status=data.get('status', 'planned'),  # Default to planned
            serves_count=data.get('serves_count', 1),
            estimated_cost=data.get('estimated_cost'),
            dietary_tags=dietary_tags_json,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(meal)
        db.session.commit()
        
        return jsonify(meal.to_dict_with_dishes()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating meal: {e}")
        return jsonify({'error': f"Failed to create meal: {str(e)}"}), 500


@meals_bp.route('/meals/<meal_id>', methods=['PUT'])
def update_meal(meal_id):
    """Update a meal"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        data = request.json
        
        # Update fields if provided
        if 'title' in data:
            meal.title = data['title']
        if 'description' in data:
            meal.description = data['description']
        if 'meal_type' in data:
            meal.meal_type = data['meal_type']
        if 'status' in data:
            meal.status = data['status']
        if 'serves_count' in data:
            meal.serves_count = data['serves_count']
        if 'estimated_cost' in data:
            meal.estimated_cost = data['estimated_cost']
        
        # Handle dietary tags update
        if 'dietary_tags' in data:
            dietary_tags = data['dietary_tags']
            if isinstance(dietary_tags, list):
                meal.dietary_tags = json.dumps(dietary_tags)
            else:
                meal.dietary_tags = None
        
        meal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(meal.to_dict_with_dishes())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to update meal: {str(e)}"}), 500


@meals_bp.route('/meals/<meal_id>', methods=['DELETE'])
def delete_meal(meal_id):
    """Delete a meal"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        db.session.delete(meal)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Meal deleted'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to delete meal: {str(e)}"}), 500


@meals_bp.route('/meals/<meal_id>/dishes', methods=['POST'])
def add_dish_to_meal(meal_id):
    """Add a dish to a meal"""
    try:
        data = request.json
        
        if not data.get('dish_id'):
            return jsonify({'error': 'dish_id is required'}), 400
        
        # Validate meal and dish exist
        meal = Meal.query.get_or_404(meal_id)
        dish = Dish.query.get_or_404(data['dish_id'])
        
        # Check if dish is already in meal
        existing = MealDish.query.filter_by(meal_id=meal_id, dish_id=data['dish_id']).first()
        if existing:
            return jsonify({'error': 'Dish is already in this meal'}), 400
        
        meal_dish = MealDish(
            id=str(uuid.uuid4()),
            meal_id=meal_id,
            dish_id=data['dish_id'],
            servings_multiplier=data.get('servings_multiplier', 1.0),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(meal_dish)
        db.session.commit()
        
        return jsonify({'status': 'success', 'meal_dish': meal_dish.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding dish to meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to add dish to meal: {str(e)}"}), 500


@meals_bp.route('/meals/<meal_id>/dishes/<dish_id>', methods=['DELETE'])
def remove_dish_from_meal(meal_id, dish_id):
    """Remove a dish from a meal"""
    try:
        meal_dish = MealDish.query.filter_by(meal_id=meal_id, dish_id=dish_id).first_or_404()
        
        db.session.delete(meal_dish)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Dish removed from meal'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing dish {dish_id} from meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to remove dish from meal: {str(e)}"}), 500


@meals_bp.route('/meals/<meal_id>/events', methods=['GET'])
def get_meal_events(meal_id):
    """Get all events associated with a meal"""
    try:
        events = Event.query.filter_by(meal_id=meal_id).all()
        return jsonify([event.to_dict_with_meal() for event in events])
    except Exception as e:
        logger.error(f"Error getting events for meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to get meal events: {str(e)}"}), 500