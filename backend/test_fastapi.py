#!/usr/bin/env python3
"""
Test FastAPI with initiatives routes in isolation
NO EMOJIS
"""
import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from data.database import get_db

app = FastAPI()

@app.get("/test")
def simple_test():
    """Simple test endpoint"""
    return {"message": "simple test works"}

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    """Test database connection"""
    try:
        result = db.execute(text("SELECT COUNT(*) FROM initiatives")).scalar()
        return {"initiatives_count": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/initiatives-raw")
def initiatives_raw(db: Session = Depends(get_db)):
    """Test raw SQL initiatives query"""
    try:
        result = db.execute(text("""
            SELECT id, title, description, status
            FROM initiatives
            LIMIT 1
        """))
        row = result.first()
        if row:
            return {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "status": row.status
            }
        else:
            return {"message": "no initiatives found"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("Starting test FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8002)