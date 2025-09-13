"""
Meal database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class MealType(enum.Enum):
    """Types of meals"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"

class MealStatus(enum.Enum):
    """Status of meal preparation"""
    PLANNED = "planned"
    SHOPPING = "shopping"
    PREPPING = "prepping"
    COOKING = "cooking"
    SERVED = "served"
    CANCELLED = "cancelled"

class MealModel(BaseModel):
    """Meal table model - 1:1 with dinner events"""
    __tablename__ = "meals"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Meal details
    meal_type = Column(SQLEnum(MealType), nullable=False, default=MealType.DINNER)
    status = Column(SQLEnum(MealStatus), nullable=False, default=MealStatus.PLANNED)
    serves_count = Column(Integer, default=4)  # Number of servings
    
    # Timeline
    planned_date = Column(DateTime, nullable=True)
    prep_start_time = Column(DateTime, nullable=True)  # When to start prep
    cook_start_time = Column(DateTime, nullable=True)  # When to start cooking
    serve_time = Column(DateTime, nullable=True)       # When to serve
    
    # Nutrition estimates (optional)
    estimated_calories_per_serving = Column(Integer, nullable=True)
    dietary_tags = Column(JSON, nullable=True)  # ["vegetarian", "gluten-free", etc.]
    
    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Relationships
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True)  # Associated dinner event
    dishes = relationship("DishModel", secondary="meal_dishes", back_populates="meals")
    event = relationship("EventModel", back_populates="meal", foreign_keys=[event_id])
    generated_tasks = relationship("TaskModel", back_populates="meal")  # Prep tasks generated from dishes
    
    def __repr__(self):
        return f"<Meal(id={self.id}, title='{self.title}', meal_type={self.meal_type.value})>"

class MealDishModel(BaseModel):
    """Join table for meals and dishes with serving info"""
    __tablename__ = "meal_dishes"
    
    meal_id = Column(String(36), ForeignKey("meals.id"), nullable=False)
    dish_id = Column(String(36), ForeignKey("dishes.id"), nullable=False)
    
    # Serving details for this meal
    servings = Column(Integer, default=1)  # How many servings of this dish
    notes = Column(Text, nullable=True)    # Special notes for this instance
    
    # Status tracking
    prep_completed = Column(Boolean, default=False)
    cook_completed = Column(Boolean, default=False)
    
    # Relationships
    meal = relationship("MealModel", overlaps="dishes")
    dish = relationship("DishModel", overlaps="meals")
    
    def __repr__(self):
        return f"<MealDish(meal_id={self.meal_id}, dish_id={self.dish_id}, servings={self.servings})>"