"""
Dish and Recipe database models
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class DishType(enum.Enum):
    """Types of dishes"""
    MAIN = "main"
    SIDE = "side"
    APPETIZER = "appetizer"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    SAUCE = "sauce"
    BREAD = "bread"

class DifficultyLevel(enum.Enum):
    """Cooking difficulty levels"""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class DishModel(BaseModel):
    """Dish table model"""
    __tablename__ = "dishes"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Classification
    dish_type = Column(SQLEnum(DishType), nullable=False, default=DishType.MAIN)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, default=DifficultyLevel.MEDIUM)
    cuisine = Column(String(100), nullable=True)  # "Italian", "Mexican", etc.
    
    # Timing
    prep_time_minutes = Column(Integer, default=0)
    cook_time_minutes = Column(Integer, default=0)
    total_time_minutes = Column(Integer, default=0)  # Including wait times
    
    # Advance preparation requirements
    advance_prep_hours = Column(Integer, default=0)  # Hours needed in advance (e.g., marinating)
    advance_prep_description = Column(Text, nullable=True)  # What needs to be done in advance
    
    # Serving info
    default_servings = Column(Integer, default=4)
    calories_per_serving = Column(Integer, nullable=True)
    
    # Cost and tags
    estimated_cost_per_serving = Column(Float, nullable=True)
    dietary_tags = Column(JSON, nullable=True)  # ["vegetarian", "dairy-free", etc.]
    
    # Recipe content
    recipe_id = Column(String(36), ForeignKey("recipes.id"), nullable=True)
    
    # Relationships
    recipe = relationship("RecipeModel", back_populates="dishes")
    meals = relationship("MealModel", secondary="meal_dishes", back_populates="dishes")
    
    def __repr__(self):
        return f"<Dish(id={self.id}, title='{self.title}', dish_type={self.dish_type.value})>"

class RecipeModel(BaseModel):
    """Recipe table model"""
    __tablename__ = "recipes"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Recipe content
    ingredients = Column(JSON, nullable=False)  # Array of ingredient objects
    instructions = Column(JSON, nullable=False)  # Array of instruction objects
    equipment = Column(JSON, nullable=True)     # Array of required equipment
    
    # Metadata
    source = Column(String(500), nullable=True)  # URL, book, person, etc.
    notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)  # User who added the recipe
    
    # Versioning
    version = Column(String(20), default="1.0")
    parent_recipe_id = Column(String(36), ForeignKey("recipes.id"), nullable=True)  # If this is a variation
    
    # Relationships
    dishes = relationship("DishModel", back_populates="recipe")
    variations = relationship("RecipeModel", remote_side="RecipeModel.parent_recipe_id")
    prep_tasks_template = relationship("PrepTaskTemplateModel", back_populates="recipe")
    
    def __repr__(self):
        return f"<Recipe(id={self.id}, title='{self.title}')>"

class IngredientModel(BaseModel):
    """Ingredient master table"""
    __tablename__ = "ingredients"
    
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=True)  # "produce", "dairy", "meat", etc.
    
    # Storage info
    storage_location = Column(String(100), nullable=True)  # "pantry", "fridge", "freezer"
    shelf_life_days = Column(Integer, nullable=True)
    
    # Nutritional info (optional)
    calories_per_unit = Column(Float, nullable=True)
    default_unit = Column(String(20), nullable=True)  # "cup", "lb", "piece", etc.
    
    # Cost tracking
    average_cost_per_unit = Column(Float, nullable=True)
    preferred_brand = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<Ingredient(id={self.id}, name='{self.name}')>"

class PrepTaskTemplateModel(BaseModel):
    """Template for generating prep tasks from recipes"""
    __tablename__ = "prep_task_templates"
    
    recipe_id = Column(String(36), ForeignKey("recipes.id"), nullable=False)
    
    # Task details
    title = Column(String(255), nullable=False)  # e.g., "Take rolls out to rise"
    description = Column(Text, nullable=True)
    
    # Timing relative to serve time
    hours_before_serve = Column(Integer, default=0)  # How many hours before serving
    minutes_before_serve = Column(Integer, default=0)  # Additional minutes
    
    # Task properties
    estimated_duration_minutes = Column(Integer, default=10)
    requires_attention = Column(Boolean, default=False)  # Does this need active monitoring?
    
    # Conditions
    weather_dependent = Column(Boolean, default=False)
    equipment_required = Column(JSON, nullable=True)  # Array of required equipment
    
    # Relationships
    recipe = relationship("RecipeModel", back_populates="prep_tasks_template")
    
    def __repr__(self):
        return f"<PrepTaskTemplate(id={self.id}, title='{self.title}', hours_before={self.hours_before_serve})>"