"""
Reminder API routes
NO EMOJIS
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from datetime import datetime

from ...data.database import get_db
from ...data.repositories.reminder_repo import ReminderRepository, ReminderTemplateRepository
from ...data.models.reminder_model import ReminderStatus, ReminderType
from ...services.reminder_service import ReminderService
from ...services.telegram_service import get_telegram_service
from ...workers.reminder_worker import get_reminder_worker
from ...schemas.reminder_schemas import (
    ReminderCreate, ReminderUpdate, ReminderResponse, ReminderListResponse,
    ReminderTemplateCreate, ReminderTemplateUpdate, ReminderTemplateResponse,
    ReminderTemplateListResponse, ChatIdRegister, TestReminderRequest
)

router = APIRouter(tags=["reminders"])

@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_data: ReminderCreate,
    db: Session = Depends(get_db)
):
    """Create a new reminder"""
    try:
        reminder_service = ReminderService(db)
        
        # Convert the data to a dict for repository
        reminder_dict = reminder_data.model_dump()
        reminder_dict["status"] = ReminderStatus.PENDING
        
        reminder_repo = ReminderRepository(db)
        reminder = reminder_repo.create(reminder_dict)
        
        return reminder
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating reminder: {str(e)}"
        )

@router.get("/", response_model=ReminderListResponse)
def get_reminders(
    status_filter: Optional[ReminderStatus] = None,
    chat_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get reminders with optional filters"""
    try:
        reminder_repo = ReminderRepository(db)
        
        if chat_id:
            reminders = reminder_repo.get_reminders_by_chat_id(chat_id, status_filter)
        else:
            query = db.query(reminder_repo.model)
            
            if status_filter:
                query = query.filter(reminder_repo.model.status == status_filter)
                
            reminders = query.order_by(
                reminder_repo.model.scheduled_time.desc()
            ).offset(offset).limit(limit).all()
        
        total = len(reminders)
        
        return ReminderListResponse(reminders=reminders, total=total)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching reminders: {str(e)}"
        )

@router.get("/pending", response_model=ReminderListResponse)
def get_pending_reminders(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all pending reminders"""
    try:
        reminder_repo = ReminderRepository(db)
        reminders = reminder_repo.get_pending_reminders(limit)
        
        return ReminderListResponse(reminders=reminders, total=len(reminders))
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pending reminders: {str(e)}"
        )

@router.get("/upcoming", response_model=ReminderListResponse)
def get_upcoming_reminders(
    hours_ahead: int = 24,
    db: Session = Depends(get_db)
):
    """Get upcoming reminders within specified hours"""
    try:
        reminder_repo = ReminderRepository(db)
        reminders = reminder_repo.get_upcoming_reminders(hours_ahead)
        
        return ReminderListResponse(reminders=reminders, total=len(reminders))
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching upcoming reminders: {str(e)}"
        )

@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific reminder by ID"""
    reminder_repo = ReminderRepository(db)
    reminder = reminder_repo.get(reminder_id)
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    return reminder

@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: str,
    reminder_data: ReminderUpdate,
    db: Session = Depends(get_db)
):
    """Update a reminder"""
    try:
        reminder_repo = ReminderRepository(db)
        
        # Get the existing reminder
        existing_reminder = reminder_repo.get(reminder_id)
        if not existing_reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        # Update with non-None values
        update_data = reminder_data.model_dump(exclude_unset=True)
        updated_reminder = reminder_repo.update(reminder_id, update_data)
        
        if not updated_reminder:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update reminder"
            )
        
        return updated_reminder
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating reminder: {str(e)}"
        )

@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: str,
    db: Session = Depends(get_db)
):
    """Delete a reminder"""
    reminder_repo = ReminderRepository(db)
    
    if not reminder_repo.get(reminder_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    
    success = reminder_repo.delete(reminder_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reminder"
        )
    
    return {"message": "Reminder deleted successfully"}

@router.post("/{reminder_id}/snooze")
def snooze_reminder(
    reminder_id: str,
    minutes: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Snooze a reminder for specified minutes"""
    try:
        reminder_repo = ReminderRepository(db)
        
        if not reminder_repo.get(reminder_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        success = reminder_repo.snooze_reminder(reminder_id, minutes)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to snooze reminder"
            )
        
        return {"message": f"Reminder snoozed for {minutes} minutes"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error snoozing reminder: {str(e)}"
        )

@router.post("/{reminder_id}/cancel")
def cancel_reminder(
    reminder_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a reminder"""
    try:
        reminder_repo = ReminderRepository(db)
        
        if not reminder_repo.get(reminder_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        success = reminder_repo.cancel_reminder(reminder_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel reminder"
            )
        
        return {"message": "Reminder cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling reminder: {str(e)}"
        )

@router.post("/register-chat")
def register_chat_id(
    chat_data: ChatIdRegister,
    db: Session = Depends(get_db)
):
    """Register a Telegram chat ID for receiving reminders"""
    try:
        telegram_service = get_telegram_service()
        if telegram_service:
            telegram_service.add_chat(str(chat_data.chat_id))
            return {
                "message": f"Chat ID {chat_data.chat_id} registered successfully",
                "chat_id": chat_data.chat_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram service not available"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering chat ID: {str(e)}"
        )

@router.post("/test-send")
async def test_send_reminder(
    test_data: TestReminderRequest,
    db: Session = Depends(get_db)
):
    """Send a test reminder immediately (for testing)"""
    try:
        worker = get_reminder_worker()
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Reminder worker not available"
            )
        
        success = await worker.send_test_reminder(test_data.reminder_id)
        
        if success:
            return {"message": "Test reminder sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test reminder"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending test reminder: {str(e)}"
        )

# Reminder Templates endpoints

@router.post("/templates", response_model=ReminderTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_reminder_template(
    template_data: ReminderTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new reminder template"""
    try:
        template_repo = ReminderTemplateRepository(db)
        
        # Check if name already exists
        existing = template_repo.get_by_name(template_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template with this name already exists"
            )
        
        template_dict = template_data.model_dump()
        template = template_repo.create(template_dict)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )

@router.get("/templates", response_model=ReminderTemplateListResponse)
def get_reminder_templates(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get reminder templates"""
    try:
        template_repo = ReminderTemplateRepository(db)
        
        if active_only:
            templates = template_repo.get_active_templates()
        else:
            templates = template_repo.get_all()
        
        return ReminderTemplateListResponse(templates=templates, total=len(templates))
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching templates: {str(e)}"
        )

@router.get("/templates/{template_id}", response_model=ReminderTemplateResponse)
def get_reminder_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific reminder template by ID"""
    template_repo = ReminderTemplateRepository(db)
    template = template_repo.get(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template

@router.put("/templates/{template_id}", response_model=ReminderTemplateResponse)
def update_reminder_template(
    template_id: str,
    template_data: ReminderTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a reminder template"""
    try:
        template_repo = ReminderTemplateRepository(db)
        
        if not template_repo.get(template_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        update_data = template_data.model_dump(exclude_unset=True)
        updated_template = template_repo.update(template_id, update_data)
        
        if not updated_template:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update template"
            )
        
        return updated_template
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating template: {str(e)}"
        )

@router.post("/templates/{template_id}/toggle")
def toggle_template_active(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Toggle the active status of a template"""
    try:
        template_repo = ReminderTemplateRepository(db)
        
        updated_template = template_repo.toggle_active(template_id)
        if not updated_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        return {
            "message": f"Template {'activated' if updated_template.is_active else 'deactivated'} successfully",
            "is_active": updated_template.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling template: {str(e)}"
        )

@router.get("/worker/status")
def get_worker_status():
    """Get the status of the reminder worker"""
    worker = get_reminder_worker()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reminder worker not available"
        )
    
    return worker.get_scheduler_status()

@router.get("/telegram/status")
async def get_telegram_status():
    """Get the status of the Telegram service"""
    telegram_service = get_telegram_service()
    if not telegram_service:
        return {"status": "not_initialized", "bot_available": False}
    
    # Get active chats
    active_chats = await telegram_service.get_active_chats()
    
    return {
        "status": "initialized",
        "bot_available": True,
        "active_chats_count": len(active_chats),
        "has_active_users": len(active_chats) > 0
    }