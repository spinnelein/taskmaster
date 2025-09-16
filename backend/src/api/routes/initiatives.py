"""
Initiative API routes - MINIMAL TEST VERSION
NO EMOJIS
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_endpoint():
    """Test endpoint"""
    return {"message": "initiatives test works"}

@router.get("/")
def get_initiatives():
    """Get all active initiatives - minimal test version"""
    return {
        "initiatives": [
            {
                "id": "test-123",
                "title": "Test Initiative",
                "description": "Test Description",
                "is_active": True,
                "task_templates": [],
                "task_count": 0,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
        ],
        "total": 1
    }

@router.get("/{initiative_id}")
def get_initiative(initiative_id: str, db: Session = Depends(get_db)):
    """Get a specific initiative by ID"""
    try:
        result = db.execute(text("""
            SELECT 
                id, title, description, is_active, task_templates,
                created_at, updated_at
            FROM initiatives 
            WHERE id = :initiative_id
        """), {"initiative_id": initiative_id})
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Initiative not found")
        
        # Get tasks for this initiative
        tasks_result = db.execute(text("""
            SELECT id, title, duration, status, is_recurring
            FROM tasks 
            WHERE initiative_id = :initiative_id
            ORDER BY created_at DESC
        """), {"initiative_id": initiative_id})
        
        tasks = [
            {
                "id": task.id,
                "title": task.title,
                "duration": task.duration,
                "status": task.status,
                "is_recurring": task.is_recurring
            }
            for task in tasks_result
        ]
        
        return {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "is_active": row.is_active,
            "task_templates": row.task_templates or [],
            "tasks": tasks,
            "task_count": len(tasks),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/")
def create_initiative(
    data: Dict[str, Any] = Body(...)
):
    """Create a new initiative with task templates"""
    db = next(get_db())
    try:
        initiative_id = str(uuid.uuid4())
        
        # Extract data
        title = data.get("title")
        description = data.get("description", "")
        task_templates = data.get("task_templates", [])
        
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        
        # Validate task templates
        for template in task_templates:
            if "title" not in template or "recurrence_days" not in template:
                raise HTTPException(
                    status_code=400, 
                    detail="Each task template must have 'title' and 'recurrence_days'"
                )
        
        # Create initiative
        db.execute(text("""
            INSERT INTO initiatives (
                id, title, description, is_active, task_templates,
                created_at, updated_at
            ) VALUES (
                :id, :title, :description, true, :templates,
                :now, :now
            )
        """), {
            "id": initiative_id,
            "title": title,
            "description": description,
            "templates": str(task_templates),  # Convert to JSON string
            "now": datetime.utcnow()
        })
        
        # Create initial tasks from templates
        for template in task_templates:
            task_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO tasks (
                    id, title, description, duration, 
                    initiative_id, is_recurring, recurrence_days,
                    status, created_at, updated_at
                ) VALUES (
                    :id, :title, :description, :duration,
                    :initiative_id, true, :recurrence_days,
                    'active', :now, :now
                )
            """), {
                "id": task_id,
                "title": template["title"],
                "description": template.get("description", ""),
                "duration": template.get("duration", 30),
                "initiative_id": initiative_id,
                "recurrence_days": template["recurrence_days"],
                "now": datetime.utcnow()
            })
        
        db.commit()
        
        return {
            "id": initiative_id,
            "title": title,
            "description": description,
            "is_active": True,
            "task_templates": task_templates,
            "message": f"Initiative created with {len(task_templates)} recurring tasks"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating initiative: {str(e)}")
    finally:
        db.close()

@router.delete("/{initiative_id}")
def delete_initiative(initiative_id: str, db: Session = Depends(get_db)):
    """Delete an initiative and its tasks"""
    try:
        # Check if exists
        result = db.execute(text("""
            SELECT id FROM initiatives WHERE id = :initiative_id
        """), {"initiative_id": initiative_id})
        
        if not result.first():
            raise HTTPException(status_code=404, detail="Initiative not found")
        
        # Delete tasks first
        db.execute(text("""
            DELETE FROM tasks WHERE initiative_id = :initiative_id
        """), {"initiative_id": initiative_id})
        
        # Delete initiative
        db.execute(text("""
            DELETE FROM initiatives WHERE id = :initiative_id
        """), {"initiative_id": initiative_id})
        
        db.commit()
        
        return {"message": "Initiative and associated tasks deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting initiative: {str(e)}")