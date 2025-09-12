"""
Dish and Recipe schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from .base_schemas import BaseResponse

class IngredientItem(BaseModel):
    """Schema for an ingredient in a recipe"""
    name: str
    quantity: float
    unit: str
    notes: Optional[str] = None

class InstructionStep(BaseModel):
    """Schema for a recipe instruction step"""
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None
    temperature: Optional[str] = None

class PrepTaskTemplateCreate(BaseModel):
    """Schema for creating a prep task template"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    hours_before_serve: int = Field(0, ge=0)
    minutes_before_serve: int = Field(0, ge=0)
    estimated_duration_minutes: int = Field(10, ge=1)
    requires_attention: bool = Field(False)
    weather_dependent: bool = Field(False)
    equipment_required: Optional[List[str]] = None

class RecipeCreate(BaseModel):
    """Schema for creating a recipe"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    ingredients: List[IngredientItem]
    instructions: List[InstructionStep]
    equipment: Optional[List[str]] = None
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    prep_tasks: Optional[List[PrepTaskTemplateCreate]] = None

class DishCreate(BaseModel):
    """Schema for creating a dish"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    dish_type: str = Field("main")
    difficulty: str = Field("medium")
    cuisine: Optional[str] = Field(None, max_length=100)
    prep_time_minutes: int = Field(0, ge=0)
    cook_time_minutes: int = Field(0, ge=0)
    total_time_minutes: int = Field(0, ge=0)
    advance_prep_hours: int = Field(0, ge=0)
    advance_prep_description: Optional[str] = None
    default_servings: int = Field(4, ge=1)
    calories_per_serving: Optional[int] = Field(None, ge=0)
    estimated_cost_per_serving: Optional[float] = Field(None, ge=0)
    dietary_tags: Optional[List[str]] = None
    recipe: Optional[RecipeCreate] = None
    
    @validator('dish_type')
    def validate_dish_type(cls, v):
        valid_types = ["main", "side", "appetizer", "dessert", "beverage", "sauce", "bread"]
        if v not in valid_types:
            raise ValueError(f"Dish type must be one of {valid_types}")
        return v
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        valid_difficulties = ["very_easy", "easy", "medium", "hard", "expert"]
        if v not in valid_difficulties:
            raise ValueError(f"Difficulty must be one of {valid_difficulties}")
        return v

class DishUpdate(BaseModel):
    """Schema for updating a dish"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    dish_type: Optional[str] = None
    difficulty: Optional[str] = None
    cuisine: Optional[str] = Field(None, max_length=100)
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    total_time_minutes: Optional[int] = Field(None, ge=0)
    advance_prep_hours: Optional[int] = Field(None, ge=0)
    advance_prep_description: Optional[str] = None
    default_servings: Optional[int] = Field(None, ge=1)
    calories_per_serving: Optional[int] = Field(None, ge=0)
    estimated_cost_per_serving: Optional[float] = Field(None, ge=0)
    dietary_tags: Optional[List[str]] = None

class PrepTaskTemplateResponse(BaseResponse):
    """Schema for prep task template response"""
    recipe_id: str
    title: str
    description: Optional[str]
    hours_before_serve: int
    minutes_before_serve: int
    estimated_duration_minutes: int
    requires_attention: bool
    weather_dependent: bool
    equipment_required: Optional[List[str]]
    
    class Config:
        orm_mode = True

class RecipeResponse(BaseResponse):
    """Schema for recipe response"""
    title: str
    description: Optional[str]
    ingredients: List[Dict[str, Any]]
    instructions: List[Dict[str, Any]]
    equipment: Optional[List[str]]
    source: Optional[str]
    notes: Optional[str]
    version: str
    prep_tasks_template: List[PrepTaskTemplateResponse]
    
    class Config:
        orm_mode = True

class DishResponse(BaseResponse):
    """Schema for dish response"""
    title: str
    description: Optional[str]
    dish_type: str
    difficulty: str
    cuisine: Optional[str]
    prep_time_minutes: int
    cook_time_minutes: int
    total_time_minutes: int
    advance_prep_hours: int
    advance_prep_description: Optional[str]
    default_servings: int
    calories_per_serving: Optional[int]
    estimated_cost_per_serving: Optional[float]
    dietary_tags: Optional[List[str]]
    recipe: Optional[RecipeResponse]
    
    class Config:
        orm_mode = True

class DishListResponse(BaseModel):
    """Schema for list of dishes"""
    dishes: List[DishResponse]
    total: int

class IngredientResponse(BaseResponse):
    """Schema for ingredient response"""
    name: str
    category: Optional[str]
    storage_location: Optional[str]
    shelf_life_days: Optional[int]
    calories_per_unit: Optional[float]
    default_unit: Optional[str]
    average_cost_per_unit: Optional[float]
    preferred_brand: Optional[str]
    
    class Config:
        orm_mode = True