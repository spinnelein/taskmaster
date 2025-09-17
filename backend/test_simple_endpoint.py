#!/usr/bin/env python3
"""
Test simple initiative endpoint directly
"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.data.database import get_db, SessionLocal
from src.data.models.initiative_model import InitiativeModel

app = FastAPI()

@app.get("/test-initiatives")
def test_initiatives():
    """Simple test endpoint"""
    db = SessionLocal()
    try:
        # Very basic query
        initiatives = db.query(
            InitiativeModel.id,
            InitiativeModel.title,
            InitiativeModel.description,
            InitiativeModel.status,
            InitiativeModel.is_template,
            InitiativeModel.target_completion_count,
            InitiativeModel.current_completion_count,
            InitiativeModel.created_at,
            InitiativeModel.updated_at
        ).limit(10).all()
        
        result = []
        for initiative in initiatives:
            result.append({
                "id": initiative.id,
                "title": initiative.title,
                "description": initiative.description,
                "status": initiative.status.value if hasattr(initiative.status, 'value') else str(initiative.status),
                "is_template": initiative.is_template,
                "target_completion_count": initiative.target_completion_count,
                "current_completion_count": initiative.current_completion_count,
                "created_at": initiative.created_at.isoformat() if initiative.created_at else None,
                "updated_at": initiative.updated_at.isoformat() if initiative.updated_at else None,
                "task_count": 0  # Hardcoded to avoid task query
            })
        
        return {
            "initiatives": result,
            "total": len(result)
        }
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)