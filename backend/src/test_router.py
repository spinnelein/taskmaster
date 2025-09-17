"""
Test router outside of routes directory
NO EMOJIS
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_test():
    """Test endpoint"""
    return {"message": "external test router works"}

@router.get("/simple")
def simple_test():
    """Simple test endpoint"""
    return {"message": "simple test works"}