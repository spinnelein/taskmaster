"""
Base schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None