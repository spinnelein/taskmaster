# meals.py - Meal domain models: Dish, Meal, Recipe, MealDish
from .base import db, BaseModel, JSONFieldMixin


class Dish(BaseModel, JSONFieldMixin):
    __tablename__ = 'dishes'
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    dish_type = db.Column(db.String(9), nullable=False)  # breakfast, lunch, dinner, dessert, snack
    difficulty = db.Column(db.String(9), nullable=False)  # easy, medium, hard
    cuisine = db.Column(db.String(100))
    prep_time_minutes = db.Column(db.Integer)
    cook_time_minutes = db.Column(db.Integer)
    total_time_minutes = db.Column(db.Integer)
    advance_prep_hours = db.Column(db.Integer)
    advance_prep_description = db.Column(db.Text)
    default_servings = db.Column(db.Integer)
    calories_per_serving = db.Column(db.Integer)
    estimated_cost_per_serving = db.Column(db.Float)
    dietary_tags = db.Column(db.Text)  # JSON array
    recipe_id = db.Column(db.String(36))  # Foreign key to recipes table (if exists)
    
    def to_dict(self):
        dietary_tags = self.parse_json_field(self.dietary_tags)
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'dish_type': self.dish_type,
            'difficulty': self.difficulty,
            'cuisine': self.cuisine,
            'prep_time_minutes': self.prep_time_minutes,
            'cook_time_minutes': self.cook_time_minutes,
            'total_time_minutes': self.total_time_minutes,
            'advance_prep_hours': self.advance_prep_hours,
            'advance_prep_description': self.advance_prep_description,
            'default_servings': self.default_servings,
            'calories_per_serving': self.calories_per_serving,
            'estimated_cost_per_serving': self.estimated_cost_per_serving,
            'dietary_tags': dietary_tags,
            'recipe_id': self.recipe_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_recipe(self):
        """Get the associated recipe"""
        if self.recipe_id:
            return Recipe.query.get(self.recipe_id)
        return None
    
    def to_dict_with_recipe(self):
        """Get dish data with embedded recipe information"""
        dish_dict = self.to_dict()
        recipe = self.get_recipe()
        if recipe:
            dish_dict['recipe'] = recipe.to_dict()
        else:
            dish_dict['recipe'] = None
        return dish_dict
    
    def get_meals(self):
        """Get all meals that use this dish"""
        meal_dishes = MealDish.query.filter_by(dish_id=self.id).all()
        meals = []
        for meal_dish in meal_dishes:
            meal = Meal.query.get(meal_dish.meal_id)
            if meal:
                meals.append(meal)
        return meals


class Meal(BaseModel, JSONFieldMixin):
    __tablename__ = 'meals'
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    meal_type = db.Column(db.String(9), nullable=False)  # breakfast, lunch, dinner, snack
    status = db.Column(db.String(9), nullable=False)  # planned, in_progress, completed
    serves_count = db.Column(db.Integer)
    planned_date = db.Column(db.DateTime)
    prep_start_time = db.Column(db.DateTime)
    cook_start_time = db.Column(db.DateTime)
    serve_time = db.Column(db.DateTime)
    estimated_calories_per_serving = db.Column(db.Integer)
    dietary_tags = db.Column(db.Text)  # JSON array
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    event_id = db.Column(db.String(36))  # Foreign key to events table
    
    def to_dict(self):
        dietary_tags = self.parse_json_field(self.dietary_tags)
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'meal_type': self.meal_type,
            'status': self.status,
            'serves_count': self.serves_count,
            'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            'prep_start_time': self.prep_start_time.isoformat() if self.prep_start_time else None,
            'cook_start_time': self.cook_start_time.isoformat() if self.cook_start_time else None,
            'serve_time': self.serve_time.isoformat() if self.serve_time else None,
            'estimated_calories_per_serving': self.estimated_calories_per_serving,
            'dietary_tags': dietary_tags,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost,
            'event_id': self.event_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_dishes(self):
        """Get all dishes associated with this meal"""
        meal_dishes = MealDish.query.filter_by(meal_id=self.id).all()
        dishes = []
        for meal_dish in meal_dishes:
            dish = Dish.query.get(meal_dish.dish_id)
            if dish:
                dishes.append(dish)
        return dishes
    
    def to_dict_with_dishes(self):
        """Get meal data with embedded dishes information"""
        meal_dict = self.to_dict()
        dishes = self.get_dishes()
        meal_dict['dishes'] = [dish.to_dict() for dish in dishes]
        meal_dict['dish_count'] = len(dishes)
        return meal_dict
    
    def get_events(self):
        """Get all events (dinners) that use this meal"""
        from .core import Event
        return Event.query.filter_by(meal_id=self.id).all()
    
    def to_dict_with_events(self):
        """Get meal data with embedded events information"""
        meal_dict = self.to_dict_with_dishes()
        events = self.get_events()
        meal_dict['events'] = [event.to_dict() for event in events]
        meal_dict['event_count'] = len(events)
        return meal_dict


class MealDish(BaseModel):
    __tablename__ = 'meal_dishes'
    
    meal_id = db.Column(db.String(36), nullable=False)  # Foreign key to meals table
    dish_id = db.Column(db.String(36), nullable=False)  # Foreign key to dishes table
    servings = db.Column(db.Integer)  # Not used currently but kept for future
    notes = db.Column(db.Text)
    prep_completed = db.Column(db.Boolean, default=False)
    cook_completed = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'meal_id': self.meal_id,
            'dish_id': self.dish_id,
            'servings': self.servings,
            'notes': self.notes,
            'prep_completed': bool(self.prep_completed),
            'cook_completed': bool(self.cook_completed),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_meal(self):
        """Get the associated meal"""
        return Meal.query.get(self.meal_id)
    
    def get_dish(self):
        """Get the associated dish"""
        return Dish.query.get(self.dish_id)


class Recipe(BaseModel, JSONFieldMixin):
    __tablename__ = 'recipes'
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text, nullable=False)  # JSON array
    instructions = db.Column(db.Text, nullable=False)  # JSON array
    equipment = db.Column(db.Text)  # JSON array
    source = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(255))
    version = db.Column(db.String(20))
    parent_recipe_id = db.Column(db.String(36))  # Foreign key to recipes table for recipe versions
    
    def to_dict(self):
        # Parse JSON fields
        ingredients = self.parse_json_field(self.ingredients)
        instructions = self.parse_json_field(self.instructions)
        equipment = self.parse_json_field(self.equipment)
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'ingredients': ingredients,
            'instructions': instructions,
            'equipment': equipment,
            'source': self.source,
            'notes': self.notes,
            'created_by': self.created_by,
            'version': self.version,
            'parent_recipe_id': self.parent_recipe_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }