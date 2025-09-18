"""
Meal API routes
NO EMOJIS
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ...data.database import get_db
from ...data.repositories.meal_repo import MealRepository
from ...schemas.meal_schemas import (
    MealCreate, MealUpdate, MealResponse, MealListResponse,
    MealDishAdd, MealPrepTaskGenerate
)
from ...schemas.task_schemas import TaskResponse

router = APIRouter()

def get_meal_repo(db: Session = Depends(get_db)) -> MealRepository:
    return MealRepository(db)

@router.post("/", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(
    meal: MealCreate,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Create a new meal"""
    try:
        meal_data = meal.dict(exclude={"dishes"})
        new_meal = repo.create(meal_data)
        
        if not new_meal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create meal"
            )
        
        # Add dishes if provided
        if meal.dishes:
            for dish_data in meal.dishes:
                repo.add_dish(
                    new_meal.id,
                    dish_data.dish_id,
                    dish_data.servings,
                    dish_data.notes
                )
        
        # Return meal with dishes
        return repo.get_with_dishes(new_meal.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=MealListResponse)
def get_meals(
    skip: int = 0,
    limit: int = 100,
    upcoming_days: int = None,
    start_date: datetime = None,
    end_date: datetime = None,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Get meals with optional filtering"""
    try:
        if upcoming_days:
            meals = repo.get_upcoming(upcoming_days)
        elif start_date and end_date:
            meals = repo.get_by_date_range(start_date, end_date)
        else:
            meals = repo.get_all()
        
        # Apply pagination
        total = len(meals)
        meals = meals[skip:skip + limit]
        
        return MealListResponse(
            meals=meals,
            total=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/upcoming", response_model=MealListResponse)
def get_upcoming_meals(
    days: int = 7,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Get upcoming meals for the next N days"""
    try:
        meals = repo.get_upcoming(days)
        return MealListResponse(
            meals=meals,
            total=len(meals)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{meal_id}", response_model=MealResponse)
def get_meal(
    meal_id: str,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Get a specific meal with dishes"""
    meal = repo.get_with_dishes(meal_id)
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found"
        )
    return meal

@router.put("/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: str,
    meal: MealUpdate,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Update a meal"""
    existing = repo.get(meal_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found"
        )
    
    try:
        updated = repo.update(meal_id, meal.dict(exclude_unset=True))
        return repo.get_with_dishes(updated.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: str,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Delete a meal"""
    existing = repo.get(meal_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found"
        )
    
    try:
        repo.delete(meal_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Dish management routes
@router.post("/{meal_id}/dishes")
def add_dish_to_meal(
    meal_id: str,
    dish_data: MealDishAdd,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Add a dish to a meal"""
    try:
        meal_dish = repo.add_dish(
            meal_id,
            dish_data.dish_id,
            dish_data.servings,
            dish_data.notes
        )
        
        if not meal_dish:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal or dish not found"
            )
        
        return {"message": "Dish added successfully", "meal_dish_id": meal_dish.id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{meal_id}/dishes/{dish_id}")
def remove_dish_from_meal(
    meal_id: str,
    dish_id: str,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Remove a dish from a meal"""
    try:
        success = repo.remove_dish(meal_id, dish_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal-dish association not found"
            )
        
        return {"message": "Dish removed successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Meal prep and event management
@router.post("/{meal_id}/generate-prep-tasks", response_model=List[TaskResponse])
def generate_prep_tasks(
    meal_id: str,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Generate prep tasks for all dishes in a meal"""
    try:
        tasks = repo.generate_prep_tasks(meal_id)
        return tasks
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{meal_id}/create-event")
def create_meal_event(
    meal_id: str,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Create a dinner event for a meal"""
    try:
        event = repo.create_meal_event(meal_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create event - meal may not have serve time"
            )
        
        return {"message": "Event created successfully", "event_id": event.id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{meal_id}/nutrition")
def get_meal_nutrition(
    meal_id: str,
    repo: MealRepository = Depends(get_meal_repo)
):
    """Get nutritional information for a meal"""
    try:
        nutrition = repo.calculate_nutrition(meal_id)
        return nutrition
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )