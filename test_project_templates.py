#!/usr/bin/env python3
"""
Test script for Project Templates functionality
Tests model creation, API endpoints, and template instantiation
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta

# Add the flask_app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

def test_create_sample_template():
    """Create a sample project template via API"""
    
    # Sample template data for a "Marketing Campaign" project
    template_data = {
        "name": "Marketing Campaign Template",
        "description": "Standard marketing campaign process from planning to execution",
        "category": "Marketing",
        "estimated_duration_days": 90,
        "template_data": {
            "project": {
                "title": "Marketing Campaign",
                "description": "A comprehensive marketing campaign project",
                "priority": "HIGH",
                "estimated_duration_days": 90
            },
            "phases": [
                {
                    "title": "Planning Phase",
                    "description": "Initial planning and strategy development",
                    "order": 1,
                    "start_offset_days": 0,
                    "duration_days": 30,
                    "tasks": [
                        {
                            "title": "Market Research",
                            "description": "Conduct comprehensive market analysis",
                            "priority": "HIGH",
                            "estimated_hours": 20,
                            "start_offset_days": 0,
                            "is_divisible": True,
                            "min_chunk_size": 120,
                            "required_context": ["research", "analysis"]
                        },
                        {
                            "title": "Competitor Analysis",
                            "description": "Analyze key competitors and their strategies",
                            "priority": "MEDIUM",
                            "estimated_hours": 15,
                            "start_offset_days": 5,
                            "is_divisible": True,
                            "min_chunk_size": 90,
                            "required_context": ["research", "analysis"]
                        },
                        {
                            "title": "Campaign Strategy",
                            "description": "Develop overall campaign strategy and goals",
                            "priority": "HIGH",
                            "estimated_hours": 12,
                            "start_offset_days": 15,
                            "is_divisible": False,
                            "required_context": ["planning", "strategy"]
                        }
                    ]
                },
                {
                    "title": "Content Creation Phase",
                    "description": "Create all marketing materials and content",
                    "order": 2,
                    "start_offset_days": 30,
                    "duration_days": 45,
                    "tasks": [
                        {
                            "title": "Design Brand Assets",
                            "description": "Create logos, color schemes, and brand guidelines",
                            "priority": "HIGH",
                            "estimated_hours": 25,
                            "start_offset_days": 0,
                            "is_divisible": True,
                            "min_chunk_size": 180,
                            "required_context": ["design", "creative"]
                        },
                        {
                            "title": "Write Copy",
                            "description": "Write all marketing copy and content",
                            "priority": "HIGH",
                            "estimated_hours": 30,
                            "start_offset_days": 10,
                            "is_divisible": True,
                            "min_chunk_size": 60,
                            "required_context": ["writing", "creative"]
                        },
                        {
                            "title": "Create Video Content",
                            "description": "Produce promotional videos and animations",
                            "priority": "MEDIUM",
                            "estimated_hours": 40,
                            "start_offset_days": 20,
                            "is_divisible": True,
                            "min_chunk_size": 240,
                            "required_context": ["video", "creative"]
                        }
                    ]
                },
                {
                    "title": "Execution Phase",
                    "description": "Launch and monitor the campaign",
                    "order": 3,
                    "start_offset_days": 75,
                    "duration_days": 15,
                    "tasks": [
                        {
                            "title": "Launch Campaign",
                            "description": "Execute the campaign launch across all channels",
                            "priority": "HIGH",
                            "estimated_hours": 8,
                            "start_offset_days": 0,
                            "is_divisible": False,
                            "required_context": ["execution", "coordination"]
                        },
                        {
                            "title": "Monitor Performance",
                            "description": "Track and analyze campaign performance metrics",
                            "priority": "HIGH",
                            "estimated_hours": 20,
                            "start_offset_days": 2,
                            "is_divisible": True,
                            "min_chunk_size": 30,
                            "required_context": ["analysis", "monitoring"]
                        },
                        {
                            "title": "Optimize Campaign",
                            "description": "Make adjustments based on performance data",
                            "priority": "MEDIUM",
                            "estimated_hours": 15,
                            "start_offset_days": 7,
                            "is_divisible": True,
                            "min_chunk_size": 60,
                            "required_context": ["optimization", "analysis"]
                        }
                    ]
                }
            ]
        }
    }
    
    print("📋 Creating sample Marketing Campaign template...")
    print(f"Template: {template_data['name']}")
    print(f"Phases: {len(template_data['template_data']['phases'])}")
    
    total_tasks = sum(len(phase['tasks']) for phase in template_data['template_data']['phases'])
    print(f"Total tasks: {total_tasks}")
    
    return template_data

def test_create_second_template():
    """Create a second sample template for variety"""
    
    template_data = {
        "name": "Website Development Project",
        "description": "Complete website development from concept to launch",
        "category": "Development",
        "estimated_duration_days": 60,
        "template_data": {
            "project": {
                "title": "Website Development",
                "description": "Full-stack website development project",
                "priority": "HIGH",
                "estimated_duration_days": 60
            },
            "phases": [
                {
                    "title": "Discovery & Planning",
                    "description": "Requirements gathering and technical planning",
                    "order": 1,
                    "start_offset_days": 0,
                    "duration_days": 14,
                    "tasks": [
                        {
                            "title": "Requirements Analysis",
                            "description": "Gather and document all project requirements",
                            "priority": "HIGH",
                            "estimated_hours": 16,
                            "start_offset_days": 0,
                            "is_divisible": True,
                            "min_chunk_size": 120,
                            "required_context": ["analysis", "documentation"]
                        },
                        {
                            "title": "Technical Architecture",
                            "description": "Design system architecture and technology stack",
                            "priority": "HIGH",
                            "estimated_hours": 12,
                            "start_offset_days": 5,
                            "is_divisible": False,
                            "required_context": ["architecture", "planning"]
                        }
                    ]
                },
                {
                    "title": "Development",
                    "description": "Core development and implementation",
                    "order": 2,
                    "start_offset_days": 14,
                    "duration_days": 35,
                    "tasks": [
                        {
                            "title": "Frontend Development",
                            "description": "Build user interface and user experience",
                            "priority": "HIGH",
                            "estimated_hours": 80,
                            "start_offset_days": 0,
                            "is_divisible": True,
                            "min_chunk_size": 180,
                            "required_context": ["development", "frontend"]
                        },
                        {
                            "title": "Backend Development",
                            "description": "Implement server-side logic and APIs",
                            "priority": "HIGH",
                            "estimated_hours": 60,
                            "start_offset_days": 7,
                            "is_divisible": True,
                            "min_chunk_size": 180,
                            "required_context": ["development", "backend"]
                        },
                        {
                            "title": "Database Implementation",
                            "description": "Set up and configure database systems",
                            "priority": "MEDIUM",
                            "estimated_hours": 20,
                            "start_offset_days": 14,
                            "is_divisible": True,
                            "min_chunk_size": 120,
                            "required_context": ["database", "development"]
                        }
                    ]
                },
                {
                    "title": "Testing & Launch",
                    "description": "Quality assurance and deployment",
                    "order": 3,
                    "start_offset_days": 49,
                    "duration_days": 11,
                    "tasks": [
                        {
                            "title": "Testing & QA",
                            "description": "Comprehensive testing and quality assurance",
                            "priority": "HIGH",
                            "estimated_hours": 24,
                            "start_offset_days": 0,
                            "is_divisible": True,
                            "min_chunk_size": 120,
                            "required_context": ["testing", "qa"]
                        },
                        {
                            "title": "Deployment",
                            "description": "Deploy to production environment",
                            "priority": "HIGH",
                            "estimated_hours": 8,
                            "start_offset_days": 7,
                            "is_divisible": False,
                            "required_context": ["deployment", "production"]
                        }
                    ]
                }
            ]
        }
    }
    
    print("💻 Creating sample Website Development template...")
    print(f"Template: {template_data['name']}")
    print(f"Phases: {len(template_data['template_data']['phases'])}")
    
    total_tasks = sum(len(phase['tasks']) for phase in template_data['template_data']['phases'])
    print(f"Total tasks: {total_tasks}")
    
    return template_data

def test_api_endpoints():
    """Test the API endpoints with sample data"""
    
    base_url = "http://localhost:5000/api"
    
    print("\n🧪 Testing Project Templates API endpoints...")
    print("=" * 50)
    
    # Test health check first
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API health check passed")
        else:
            print("❌ API health check failed")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure Flask app is running: cd flask_app && python app.py")
        return False
    
    # Create templates
    templates = [
        test_create_sample_template(),
        test_create_second_template()
    ]
    
    template_ids = []
    
    for template_data in templates:
        try:
            print(f"\n📤 Creating template: {template_data['name']}")
            response = requests.post(f"{base_url}/project-templates", json=template_data, timeout=10)
            
            if response.status_code == 200:
                template = response.json()
                template_ids.append(template['id'])
                print(f"✅ Template created successfully")
                print(f"   ID: {template['id']}")
                print(f"   Summary: {template.get('summary', {})}")
            else:
                print(f"❌ Failed to create template: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error creating template: {e}")
    
    # Test getting templates
    try:
        print(f"\n📥 Fetching all templates...")
        response = requests.get(f"{base_url}/project-templates", timeout=5)
        
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Retrieved {len(templates)} templates")
            for template in templates:
                print(f"   - {template['name']} ({template['category']})")
        else:
            print(f"❌ Failed to fetch templates: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching templates: {e}")
    
    # Test template instantiation
    if template_ids:
        template_id = template_ids[0]  # Use first template
        due_date = (datetime.now() + timedelta(days=90)).date().isoformat()
        
        instantiation_data = {
            "due_date": due_date,
            "project_name": "Q4 Marketing Campaign 2025",
            "initiative_id": None
        }
        
        try:
            print(f"\n🚀 Testing template instantiation...")
            print(f"   Template ID: {template_id}")
            print(f"   Due date: {due_date}")
            
            response = requests.post(f"{base_url}/project-templates/{template_id}/instantiate", 
                                   json=instantiation_data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Template instantiated successfully")
                print(f"   Project ID: {result['project']['id']}")
                print(f"   Phases created: {result['phases_created']}")
                print(f"   Tasks created: {result['tasks_created']}")
            else:
                print(f"❌ Failed to instantiate template: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error instantiating template: {e}")
    
    # Test getting categories
    try:
        print(f"\n📂 Testing template categories...")
        response = requests.get(f"{base_url}/project-templates/categories", timeout=5)
        
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Retrieved categories: {categories['categories']}")
        else:
            print(f"❌ Failed to fetch categories: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching categories: {e}")
    
    print("\n✨ API testing completed!")
    return True

if __name__ == "__main__":
    print("🏗️  Project Templates Test Suite")
    print("=" * 50)
    
    # First show sample template structure
    print("\n📋 Sample Template Structure:")
    sample = test_create_sample_template()
    print(json.dumps(sample['template_data'], indent=2))
    
    # Test API endpoints
    test_api_endpoints()