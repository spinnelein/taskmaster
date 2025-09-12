"""
Meal repository
NO EMOJIS
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.meal_model import MealModel, MealDishModel, MealStatus, MealType
from ..models.dish_model import DishModel, PrepTaskTemplateModel
from ..models.task_model import TaskModel
from ..models.event_model import EventModel, EventType

class MealRepository(BaseRepository[MealModel]):
    """Repository for meal data operations"""
    
    def __init__(self, db: Session):
        super().__init__(MealModel, db)
    
    def get_with_dishes(self, meal_id: str) -> Optional[MealModel]:
        """Get meal with all dishes loaded"""
        return self.db.query(self.model).options(
            joinedload(self.model.dishes)
        ).filter(
            self.model.id == meal_id
        ).first()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[MealModel]:
        """Get meals in a date range"""
        return self.db.query(self.model).filter(
            and_(
                self.model.planned_date >= start_date,
                self.model.planned_date <= end_date
            )
        ).all()
    
    def get_upcoming(self, days: int = 7) -> List[MealModel]:
        """Get upcoming meals for the next N days"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)
        return self.get_by_date_range(start_date, end_date)
    
    def add_dish(self, meal_id: str, dish_id: str, servings: int = 1, notes: Optional[str] = None) -> Optional[MealDishModel]:
        """Add a dish to a meal"""
        # Check if meal and dish exist
        meal = self.get(meal_id)
        dish = self.db.query(DishModel).filter(DishModel.id == dish_id).first()
        
        if not meal or not dish:
            return None
        
        # Check if dish already in meal
        existing = self.db.query(MealDishModel).filter(
            and_(
                MealDishModel.meal_id == meal_id,
                MealDishModel.dish_id == dish_id
            )
        ).first()
        
        if existing:
            # Update servings
            existing.servings = servings
            existing.notes = notes
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new meal-dish association
        meal_dish = MealDishModel(
            meal_id=meal_id,
            dish_id=dish_id,
            servings=servings,
            notes=notes
        )
        
        self.db.add(meal_dish)
        self.db.commit()
        self.db.refresh(meal_dish)
        
        return meal_dish
    
    def remove_dish(self, meal_id: str, dish_id: str) -> bool:
        """Remove a dish from a meal"""
        meal_dish = self.db.query(MealDishModel).filter(
            and_(
                MealDishModel.meal_id == meal_id,
                MealDishModel.dish_id == dish_id
            )
        ).first()
        
        if not meal_dish:
            return False
        
        self.db.delete(meal_dish)
        self.db.commit()
        return True
    
    def generate_prep_tasks(self, meal_id: str) -> List[TaskModel]:
        """Generate prep tasks for all dishes in a meal"""
        meal = self.get_with_dishes(meal_id)
        if not meal or not meal.serve_time:
            return []
        
        generated_tasks = []
        
        # Get all meal dishes with their associated dish data
        meal_dishes = self.db.query(MealDishModel).filter(
            MealDishModel.meal_id == meal_id
        ).all()
        
        for meal_dish in meal_dishes:
            dish = self.db.query(DishModel).filter(
                DishModel.id == meal_dish.dish_id
            ).first()
            
            if not dish or not dish.recipe_id:
                continue
            
            # Get prep task templates for this dish's recipe
            prep_templates = self.db.query(PrepTaskTemplateModel).filter(
                PrepTaskTemplateModel.recipe_id == dish.recipe_id
            ).all()
            
            for template in prep_templates:
                # Calculate task due time
                task_due = meal.serve_time - timedelta(
                    hours=template.hours_before_serve,
                    minutes=template.minutes_before_serve
                )
                
                # Create task
                task = TaskModel(
                    title=f"{template.title} - {meal.title}",
                    description=template.description or f"Prep task for {dish.title}",
                    duration=template.estimated_duration_minutes,
                    urgency=8,  # High urgency for meal prep
                    due_date=task_due.date(),
                    due_time=task_due.time(),
                    meal_id=meal_id,
                    required_weather="any",
                    is_divisible=False
                )
                
                if template.equipment_required:
                    task.equipment_needed = template.equipment_required
                
                self.db.add(task)
                generated_tasks.append(task)
        
        # Create shopping task if needed
        if meal.status == MealStatus.PLANNED:
            shopping_due = meal.serve_time.date() - timedelta(days=1)
            shopping_task = TaskModel(
                title=f"Shop for {meal.title}",
                description=f"Buy ingredients for {meal.title}",
                duration=45,
                urgency=9,
                due_date=shopping_due,
                meal_id=meal_id,
                required_weather="any",
                is_divisible=False
            )
            self.db.add(shopping_task)
            generated_tasks.append(shopping_task)
        
        if generated_tasks:
            self.db.commit()
            for task in generated_tasks:
                self.db.refresh(task)
        
        return generated_tasks
    
    def create_meal_event(self, meal_id: str) -> Optional[EventModel]:
        """Create a dinner event for a meal"""
        meal = self.get(meal_id)
        if not meal or not meal.serve_time:
            return None
        
        # Check if event already exists
        if meal.event_id:
            return self.db.query(EventModel).filter(
                EventModel.id == meal.event_id
            ).first()
        
        # Create event
        event_duration = 60  # Default 1 hour for dinner
        event = EventModel(
            title=meal.title,
            description=f"Dinner: {meal.description}" if meal.description else "Dinner",
            start_time=meal.serve_time,
            end_time=meal.serve_time + timedelta(minutes=event_duration),
            event_type=EventType.MEAL,
            is_blocking=True,
            meal_id=meal_id
        )
        
        self.db.add(event)
        self.db.flush()
        
        # Update meal with event ID
        meal.event_id = event.id
        
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def calculate_nutrition(self, meal_id: str) -> Dict[str, Any]:
        """Calculate nutritional information for a meal"""
        meal_dishes = self.db.query(MealDishModel).filter(
            MealDishModel.meal_id == meal_id
        ).all()
        
        total_calories = 0
        dietary_tags = set()
        
        for meal_dish in meal_dishes:
            dish = self.db.query(DishModel).filter(
                DishModel.id == meal_dish.dish_id
            ).first()
            
            if dish:
                if dish.calories_per_serving:
                    total_calories += dish.calories_per_serving * meal_dish.servings
                
                if dish.dietary_tags:
                    dietary_tags.update(dish.dietary_tags)
        
        meal = self.get(meal_id)
        if meal:
            meal.estimated_calories_per_serving = total_calories // meal.serves_count if meal.serves_count > 0 else 0
            meal.dietary_tags = list(dietary_tags)
            self.db.commit()
        
        return {
            "total_calories": total_calories,
            "calories_per_serving": total_calories // meal.serves_count if meal and meal.serves_count > 0 else 0,
            "dietary_tags": list(dietary_tags)
        }