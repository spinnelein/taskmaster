"""
Dish repository
NO EMOJIS
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from .base import BaseRepository
from ..models.dish_model import DishModel, RecipeModel, IngredientModel, PrepTaskTemplateModel, DishType
from ..models.meal_model import MealDishModel

class DishRepository(BaseRepository[DishModel]):
    """Repository for dish data operations"""
    
    def __init__(self, db: Session):
        super().__init__(DishModel, db)
    
    def get_with_recipe(self, dish_id: str) -> Optional[DishModel]:
        """Get dish with recipe loaded"""
        return self.db.query(self.model).options(
            joinedload(self.model.recipe)
        ).filter(
            self.model.id == dish_id
        ).first()
    
    def search(self, query: str) -> List[DishModel]:
        """Search dishes by title or description"""
        search_term = f"%{query}%"
        return self.db.query(self.model).filter(
            or_(
                self.model.title.ilike(search_term),
                self.model.description.ilike(search_term),
                self.model.cuisine.ilike(search_term)
            )
        ).all()
    
    def get_by_type(self, dish_type: DishType) -> List[DishModel]:
        """Get dishes by type"""
        return self.db.query(self.model).filter(
            self.model.dish_type == dish_type
        ).all()
    
    def get_by_dietary_tags(self, tags: List[str]) -> List[DishModel]:
        """Get dishes that match all dietary tags"""
        query = self.db.query(self.model)
        
        for tag in tags:
            query = query.filter(
                self.model.dietary_tags.contains([tag])
            )
        
        return query.all()
    
    def get_quick_dishes(self, max_minutes: int = 30) -> List[DishModel]:
        """Get dishes that can be made quickly"""
        return self.db.query(self.model).filter(
            self.model.total_time_minutes <= max_minutes
        ).all()
    
    def create_recipe(self, dish_id: str, recipe_data: Dict[str, Any]) -> Optional[RecipeModel]:
        """Create a recipe for a dish"""
        dish = self.get(dish_id)
        if not dish:
            return None
        
        recipe = RecipeModel(
            title=recipe_data.get("title", dish.title),
            description=recipe_data.get("description"),
            ingredients=recipe_data.get("ingredients", []),
            instructions=recipe_data.get("instructions", []),
            equipment=recipe_data.get("equipment"),
            source=recipe_data.get("source"),
            notes=recipe_data.get("notes")
        )
        
        self.db.add(recipe)
        self.db.flush()
        
        # Link recipe to dish
        dish.recipe_id = recipe.id
        
        # Create prep task templates if provided
        prep_tasks = recipe_data.get("prep_tasks", [])
        for task_data in prep_tasks:
            prep_task = PrepTaskTemplateModel(
                recipe_id=recipe.id,
                title=task_data.get("title"),
                description=task_data.get("description"),
                hours_before_serve=task_data.get("hours_before_serve", 0),
                minutes_before_serve=task_data.get("minutes_before_serve", 0),
                estimated_duration_minutes=task_data.get("estimated_duration_minutes", 10),
                requires_attention=task_data.get("requires_attention", False),
                weather_dependent=task_data.get("weather_dependent", False),
                equipment_required=task_data.get("equipment_required")
            )
            self.db.add(prep_task)
        
        self.db.commit()
        self.db.refresh(recipe)
        
        return recipe
    
    def update_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]) -> Optional[RecipeModel]:
        """Update a recipe"""
        recipe = self.db.query(RecipeModel).filter(
            RecipeModel.id == recipe_id
        ).first()
        
        if not recipe:
            return None
        
        # Update recipe fields
        for key, value in recipe_data.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(recipe, key):
                setattr(recipe, key, value)
        
        # Increment version
        current_version = recipe.version.split(".")
        minor_version = int(current_version[1]) + 1
        recipe.version = f"{current_version[0]}.{minor_version}"
        
        self.db.commit()
        self.db.refresh(recipe)
        
        return recipe
    
    def create_recipe_variation(self, parent_recipe_id: str, variation_data: Dict[str, Any]) -> Optional[RecipeModel]:
        """Create a variation of an existing recipe"""
        parent_recipe = self.db.query(RecipeModel).filter(
            RecipeModel.id == parent_recipe_id
        ).first()
        
        if not parent_recipe:
            return None
        
        # Create new recipe based on parent
        variation = RecipeModel(
            title=variation_data.get("title", f"{parent_recipe.title} - Variation"),
            description=variation_data.get("description", parent_recipe.description),
            ingredients=variation_data.get("ingredients", parent_recipe.ingredients),
            instructions=variation_data.get("instructions", parent_recipe.instructions),
            equipment=variation_data.get("equipment", parent_recipe.equipment),
            notes=variation_data.get("notes"),
            parent_recipe_id=parent_recipe_id,
            version="1.0"
        )
        
        self.db.add(variation)
        self.db.commit()
        self.db.refresh(variation)
        
        return variation
    
    def find_or_create_ingredient(self, name: str, category: Optional[str] = None) -> IngredientModel:
        """Find existing ingredient or create new one"""
        # Normalize name
        normalized_name = name.strip().lower()
        
        ingredient = self.db.query(IngredientModel).filter(
            func.lower(IngredientModel.name) == normalized_name
        ).first()
        
        if not ingredient:
            ingredient = IngredientModel(
                name=name.strip(),
                category=category
            )
            self.db.add(ingredient)
            self.db.commit()
            self.db.refresh(ingredient)
        
        return ingredient
    
    def get_shopping_list(self, meal_ids: List[str]) -> Dict[str, Any]:
        """Generate shopping list for multiple meals"""
        ingredients_needed = {}
        
        # Get all dishes for the meals
        meal_dishes = self.db.query(MealDishModel).filter(
            MealDishModel.meal_id.in_(meal_ids)
        ).all()
        
        for meal_dish in meal_dishes:
            dish = self.get_with_recipe(meal_dish.dish_id)
            if not dish or not dish.recipe:
                continue
            
            # Process each ingredient in the recipe
            for ingredient_data in dish.recipe.ingredients:
                ingredient_name = ingredient_data.get("name", "Unknown")
                quantity = ingredient_data.get("quantity", 0) * meal_dish.servings
                unit = ingredient_data.get("unit", "units")
                
                key = f"{ingredient_name}|{unit}"
                if key in ingredients_needed:
                    ingredients_needed[key]["quantity"] += quantity
                else:
                    ingredients_needed[key] = {
                        "name": ingredient_name,
                        "quantity": quantity,
                        "unit": unit
                    }
        
        # Convert to list and sort by ingredient name
        shopping_list = sorted(
            ingredients_needed.values(),
            key=lambda x: x["name"]
        )
        
        return {
            "items": shopping_list,
            "total_items": len(shopping_list)
        }