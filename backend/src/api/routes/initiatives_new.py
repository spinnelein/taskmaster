"""
Fresh initiative API routes
NO EMOJIS
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_initiatives():
    """Get all initiatives"""
    return {
        "initiatives": [],
        "total": 0
    }

@router.get("/test")
def test_endpoint():
    """Test endpoint"""
    return {"message": "initiatives test works"}