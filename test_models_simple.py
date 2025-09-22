#!/usr/bin/env python3
"""
Simple test to verify ProjectTemplate model is working
"""

import sys
import os
import json

# Add the flask_app directory to Python path
flask_app_path = os.path.join(os.path.dirname(__file__), 'flask_app')
sys.path.insert(0, flask_app_path)

def test_model_import():
    """Test basic model import and functionality"""
    try:
        print("🔍 Testing ProjectTemplate model import...")
        
        # Test basic import
        from models.projects import ProjectTemplate
        print("✅ ProjectTemplate model imported successfully")
        
        # Test model methods
        sample_data = {
            "project": {
                "title": "Test Project",
                "description": "A test project",
                "priority": "HIGH"
            },
            "phases": [
                {
                    "title": "Phase 1",
                    "description": "First phase",
                    "order": 1,
                    "duration_days": 14,
                    "tasks": [
                        {
                            "title": "Task 1",
                            "description": "First task",
                            "priority": "HIGH",
                            "estimated_hours": 8
                        }
                    ]
                }
            ]
        }
        
        # Create template instance (without database)
        template = ProjectTemplate()
        template.name = "Test Template"
        template.description = "A test template"
        template.category = "Testing"
        template.estimated_duration_days = 30
        template.is_active = True
        template.usage_count = 0
        
        # Test template data methods
        template.set_template_data(sample_data)
        retrieved_data = template.get_template_data()
        
        print("✅ Template data methods working")
        print(f"   Phase count: {template.get_phase_count()}")
        print(f"   Task count: {template.get_task_count()}")
        print(f"   Summary: {template.get_summary()}")
        
        # Test to_dict method
        template_dict = template.to_dict()
        print("✅ to_dict method working")
        print(f"   Keys: {list(template_dict.keys())}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_import():
    """Test API blueprint import"""
    try:
        print("\n🔍 Testing API blueprint import...")
        
        from routes.api.projects import projects_bp
        print("✅ Projects API blueprint imported successfully")
        
        # Check blueprint registration
        print(f"   Blueprint name: {projects_bp.name}")
        print(f"   URL prefix: {projects_bp.url_prefix}")
        
        return True
        
    except ImportError as e:
        print(f"❌ API import error: {e}")
        return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False

def test_model_registry():
    """Test that ProjectTemplate is properly registered in models package"""
    try:
        print("\n🔍 Testing model registry...")
        
        from models import ProjectTemplate, db
        print("✅ ProjectTemplate imported from models package")
        
        # Test that it's a proper SQLAlchemy model
        print(f"   Table name: {ProjectTemplate.__tablename__}")
        print(f"   Columns: {[col.name for col in ProjectTemplate.__table__.columns]}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Model registry error: {e}")
        return False
    except Exception as e:
        print(f"❌ Model registry error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Project Templates Model Test")
    print("=" * 50)
    
    success = True
    
    # Test model import and functionality
    success &= test_model_import()
    
    # Test API import
    success &= test_api_import()
    
    # Test model registry
    success &= test_model_registry()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Project Templates implementation is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\n📝 Next steps:")
    print("1. Start Flask app: cd flask_app && python app.py")
    print("2. Test API endpoints: python test_project_templates.py")
    print("3. Add frontend UI components")