#!/usr/bin/env python3
"""
Minimal test to debug initiative recursion issue
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models.initiative_model import InitiativeModel
from src.data.database import DATABASE_URL

def test_minimal_query():
    """Test minimal initiative query"""
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("Testing direct SQLAlchemy query...")
        
        # Basic count query
        count = db.query(InitiativeModel).count()
        print(f"Total initiatives: {count}")
        
        # Try basic select without relationships
        initiatives = db.query(InitiativeModel.id, InitiativeModel.title, InitiativeModel.status).limit(5).all()
        print(f"Basic query returned {len(initiatives)} initiatives")
        
        for initiative in initiatives:
            print(f"- {initiative.id}: {initiative.title} ({initiative.status})")
        
        # Try loading one full initiative
        print("\nTesting single initiative load...")
        first_initiative = db.query(InitiativeModel).first()
        if first_initiative:
            print(f"Loaded initiative: {first_initiative.id}")
            print(f"Title: {first_initiative.title}")
            print(f"Status: {first_initiative.status}")
            print(f"Created: {first_initiative.created_at}")
        else:
            print("No initiatives found")
        
        db.close()
        print("Test completed successfully")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal_query()