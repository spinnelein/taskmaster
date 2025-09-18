"""
Minimal initiatives route for testing
NO EMOJIS
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_initiatives():
    """Minimal test version"""
    return {"message": "Initiatives working!", "initiatives": [], "total": 0}

@router.get("/test")
def test_endpoint():
    """Test endpoint"""
    return {"message": "initiatives test works"}