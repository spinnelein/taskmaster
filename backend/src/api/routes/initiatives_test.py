"""
Test initiatives routes in isolation
NO EMOJIS
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_initiatives():
    """Test initiatives endpoint"""
    return {
        "message": "test initiatives works",
        "initiatives": [],
        "total": 0
    }

@router.get("/test")
def test_endpoint():
    """Simple test endpoint"""
    return {"message": "initiatives test works"}