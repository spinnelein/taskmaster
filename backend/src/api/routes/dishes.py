"""
Dish API routes
NO EMOJIS
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session

from ...data.database import get_db
from ...data.repositories.dish_repo import DishRepository
from ...schemas.dish_schemas import (
    DishCreate, DishUpdate, DishResponse, DishListResponse,
    RecipeCreate, RecipeResponse, IngredientResponse
)

router = APIRouter()

def get_dish_repo(db: Session = Depends(get_db)) -> DishRepository:
    return DishRepository(db)

@router.post("/", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    dish: DishCreate,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Create a new dish"""
    try:
        dish_data = dish.dict(exclude={"recipe"})
        new_dish = repo.create(dish_data)
        
        if not new_dish:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create dish"
            )
        
        # Create recipe if provided
        if dish.recipe:
            recipe = repo.create_recipe(new_dish.id, dish.recipe.dict())
            if not recipe:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create recipe"
                )
        
        # Return dish with recipe
        return repo.get_with_recipe(new_dish.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=DishListResponse)
def get_dishes(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search dishes by title or description"),
    dish_type: str = Query(None, description="Filter by dish type"),
    dietary_tags: List[str] = Query(None, description="Filter by dietary tags"),
    quick_only: bool = Query(False, description="Only show quick dishes (<=30 min)"),
    repo: DishRepository = Depends(get_dish_repo)
):
    """Get dishes with optional filtering"""
    try:
        if search:
            dishes = repo.search(search)
        elif dish_type:
            from ...data.models.dish_model import DishType
            dish_type_enum = DishType(dish_type)
            dishes = repo.get_by_type(dish_type_enum)
        elif dietary_tags:
            dishes = repo.get_by_dietary_tags(dietary_tags)
        elif quick_only:
            dishes = repo.get_quick_dishes(30)
        else:
            dishes = repo.get_all()
        
        # Apply pagination
        total = len(dishes)
        dishes = dishes[skip:skip + limit]
        
        return DishListResponse(
            dishes=dishes,
            total=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search", response_model=DishListResponse)
def search_dishes(
    q: str = Query(..., description="Search query"),
    repo: DishRepository = Depends(get_dish_repo)
):
    """Search dishes by title, description, or cuisine"""
    try:
        dishes = repo.search(q)
        return DishListResponse(
            dishes=dishes,
            total=len(dishes)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/quick", response_model=DishListResponse)
def get_quick_dishes(
    max_minutes: int = Query(30, ge=1, le=180, description="Maximum total time in minutes"),
    repo: DishRepository = Depends(get_dish_repo)
):
    """Get dishes that can be made quickly"""
    try:
        dishes = repo.get_quick_dishes(max_minutes)
        return DishListResponse(
            dishes=dishes,
            total=len(dishes)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{dish_id}", response_model=DishResponse)
def get_dish(
    dish_id: str,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Get a specific dish with recipe"""
    dish = repo.get_with_recipe(dish_id)
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found"
        )
    return dish

@router.put("/{dish_id}", response_model=DishResponse)
def update_dish(
    dish_id: str,
    dish: DishUpdate,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Update a dish"""
    existing = repo.get(dish_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found"
        )
    
    try:
        updated = repo.update(dish_id, dish.dict(exclude_unset=True))
        return repo.get_with_recipe(updated.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dish(
    dish_id: str,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Delete a dish"""
    existing = repo.get(dish_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found"
        )
    
    try:
        repo.delete(dish_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Recipe management routes
@router.post("/{dish_id}/recipe", response_model=RecipeResponse)
def create_recipe_for_dish(
    dish_id: str,
    recipe: RecipeCreate,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Create a recipe for a dish"""
    try:
        new_recipe = repo.create_recipe(dish_id, recipe.dict())
        if not new_recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dish not found"
            )
        return new_recipe
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: str,
    recipe: RecipeCreate,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Update a recipe"""
    try:
        updated_recipe = repo.update_recipe(recipe_id, recipe.dict())
        if not updated_recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found"
            )
        return updated_recipe
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/recipes/{recipe_id}/variations", response_model=RecipeResponse)
def create_recipe_variation(
    recipe_id: str,
    variation: RecipeCreate,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Create a variation of an existing recipe"""
    try:
        new_variation = repo.create_recipe_variation(recipe_id, variation.dict())
        if not new_variation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent recipe not found"
            )
        return new_variation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Shopping list generation
@router.post("/shopping-list")
def generate_shopping_list(
    meal_ids: List[str],
    repo: DishRepository = Depends(get_dish_repo)
):
    """Generate shopping list for multiple meals"""
    try:
        shopping_list = repo.get_shopping_list(meal_ids)
        return shopping_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Ingredient management
@router.post("/ingredients", response_model=IngredientResponse)
def create_ingredient(
    name: str,
    category: str = None,
    repo: DishRepository = Depends(get_dish_repo)
):
    """Find or create an ingredient"""
    try:
        ingredient = repo.find_or_create_ingredient(name, category)
        return ingredient
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )