"""
Meal schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from .base_schemas import BaseResponse

class MealDishAdd(BaseModel):
    """Schema for adding a dish to a meal"""
    dish_id: str
    servings: int = Field(1, ge=1)
    notes: Optional[str] = Field(None, max_length=500)

class MealCreate(BaseModel):
    """Schema for creating a meal"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    meal_type: str = Field("dinner")
    serves_count: int = Field(4, ge=1)
    planned_date: Optional[datetime] = None
    serve_time: Optional[datetime] = None
    event_id: Optional[str] = None
    dishes: Optional[List[MealDishAdd]] = None
    dietary_tags: Optional[List[str]] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    
    @validator('meal_type')
    def validate_meal_type(cls, v):
        valid_types = ["breakfast", "lunch", "dinner", "snack", "dessert"]
        if v not in valid_types:
            raise ValueError(f"Meal type must be one of {valid_types}")
        return v

class MealUpdate(BaseModel):
    """Schema for updating a meal"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    meal_type: Optional[str] = None
    status: Optional[str] = None
    serves_count: Optional[int] = Field(None, ge=1)
    planned_date: Optional[datetime] = None
    prep_start_time: Optional[datetime] = None
    cook_start_time: Optional[datetime] = None
    serve_time: Optional[datetime] = None
    dietary_tags: Optional[List[str]] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    
    @validator('meal_type')
    def validate_meal_type(cls, v):
        if v is not None:
            valid_types = ["breakfast", "lunch", "dinner", "snack", "dessert"]
            if v not in valid_types:
                raise ValueError(f"Meal type must be one of {valid_types}")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["planned", "shopping", "prepping", "cooking", "served", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class MealDishResponse(BaseModel):
    """Schema for meal-dish relationship response"""
    dish_id: str
    dish_title: str
    dish_type: str
    servings: int
    notes: Optional[str]
    prep_completed: bool
    cook_completed: bool

class MealResponse(BaseResponse):
    """Schema for meal response"""
    title: str
    description: Optional[str]
    meal_type: str
    status: str
    serves_count: int
    planned_date: Optional[datetime]
    prep_start_time: Optional[datetime]
    cook_start_time: Optional[datetime]
    serve_time: Optional[datetime]
    estimated_calories_per_serving: Optional[int]
    dietary_tags: Optional[List[str]]
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    event_id: Optional[str]
    dishes: List[MealDishResponse]
    
    class Config:
        orm_mode = True

class MealListResponse(BaseModel):
    """Schema for list of meals"""
    meals: List[MealResponse]
    total: int

class MealPrepTaskGenerate(BaseModel):
    """Schema for generating prep tasks from a meal"""
    meal_id: str
    generate_shopping_task: bool = Field(True)
    generate_prep_tasks: bool = Field(True)