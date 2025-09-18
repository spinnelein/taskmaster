# Event Exceptions Test Routes
# NO EMOJIS

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from ...data.repositories.event_exception_repo import EventExceptionRepository
from ..dependencies import get_db

router = APIRouter(tags=["event-exceptions"])

@router.get("/event-exceptions/test/{event_id}")
def test_exceptions(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Test endpoint to verify exception loading"""
    exception_repo = EventExceptionRepository(db)
    exceptions = exception_repo.get_exceptions_for_event(event_id)
    
    return {
        "event_id": event_id,
        "exception_count": len(exceptions),
        "exceptions": [
            {
                "date": str(ex.occurrence_date),
                "cancelled": ex.is_cancelled,
                "rescheduled": ex.is_rescheduled,
                "new_start": str(ex.new_start) if ex.new_start else None,
                "custom_title": ex.custom_title
            }
            for ex in exceptions
        ]
    }