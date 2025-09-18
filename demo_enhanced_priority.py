#!/usr/bin/env python3
"""
Demo script showing ProjectAwarePriorityService in action
Run this to see the enhanced priority scoring working with real data
"""

import sys
import os
from datetime import datetime

# Add flask_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_app'))

def demo_enhanced_priority():
    """Demonstrate enhanced priority scoring with real TaskMaster data"""
    print("TaskMaster YOLO Enhanced Priority Service Demo")
    print("=" * 50)
    
    try:
        # Import Flask app and services
        from flask_app.app import create_app
        from flask_app.services.enhanced_task_queue_service import get_enhanced_task_queue_service
        from flask_app.task_queue_service import get_task_queue_service
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Get both services
            enhanced_service = get_enhanced_task_queue_service()
            baseline_service = get_task_queue_service()
            
            print("[DATA] Comparing Baseline vs Enhanced Priority Scoring")
            print("-" * 50)
            
            # Get queues from both services
            baseline_queue = baseline_service.get_all_tasks_queue(limit=8)
            enhanced_queue = enhanced_service.get_enhanced_task_queue(limit=8)
            
            print("\n[TOP] TOP TASKS BY ENHANCED SCORING:")
            print("Rank | Task Name                     | Enhanced Score | Components")
            print("-" * 75)
            
            for i, task in enumerate(enhanced_queue[:5], 1):
                title = task.get('title', 'Unknown')[:25]
                score = task.get('enhanced_priority_score', 0)
                
                # Get detailed context for this task
                context = enhanced_service.get_task_context_analysis(task['id'])
                components = context.get('priority_analysis', {}).get('components', {})
                
                # Show top 2 contributing components
                sorted_components = sorted(components.items(), key=lambda x: x[1], reverse=True)
                top_components = []
                for name, value in sorted_components[:2]:
                    if value > 0:
                        short_name = name.replace('_', ' ').title()
                        top_components.append(f"{short_name}({value:.0f})")
                
                components_str = ", ".join(top_components[:2]) if top_components else "None"
                
                print(f" {i:2}  | {title:<25} | {score:>10.1f}     | {components_str}")
            
            print("\n[COMPARE] BASELINE vs ENHANCED COMPARISON:")
            print("Task Name                     | Baseline | Enhanced | Difference")
            print("-" * 70)
            
            # Compare first 5 tasks
            for i in range(min(5, len(baseline_queue), len(enhanced_queue))):
                baseline_task = baseline_queue[i]
                enhanced_task = enhanced_queue[i]
                
                # Find corresponding tasks (may be in different order)
                baseline_title = baseline_task.get('title', 'Unknown')[:25]
                enhanced_title = enhanced_task.get('title', 'Unknown')[:25]
                
                baseline_score = baseline_task.get('priority_score', 0)
                enhanced_score = enhanced_task.get('enhanced_priority_score', 0)
                
                difference = enhanced_score - baseline_score
                diff_str = f"+{difference:.0f}" if difference >= 0 else f"{difference:.0f}"
                
                print(f"{enhanced_title:<25} | {baseline_score:>8.0f} | {enhanced_score:>8.0f} | {diff_str:>10}")
            
            print("\n[DETAIL] DETAILED ANALYSIS - TOP TASK:")
            print("-" * 50)
            
            if enhanced_queue:
                top_task = enhanced_queue[0]
                context = enhanced_service.get_task_context_analysis(top_task['id'])
                
                print(f"Task: {top_task.get('title', 'Unknown')}")
                print(f"Total Enhanced Score: {top_task.get('enhanced_priority_score', 0):.1f} points")
                print(f"Due Date: {top_task.get('due_date', 'None')}")
                print(f"Urgency: {top_task.get('urgency', 'N/A')}")
                
                if context.get('priority_analysis'):
                    components = context['priority_analysis']['components']
                    print("\nScore Breakdown:")
                    for name, value in components.items():
                        if value > 0:
                            display_name = name.replace('_', ' ').title()
                            print(f"  • {display_name}: {value:.1f} points")
                    
                    top_factors = context['priority_analysis'].get('top_factors', [])
                    if top_factors:
                        print(f"\nTop Contributing Factors: {', '.join(top_factors)}")
            
            print("\n[FEATURES] ENHANCED FEATURES DEMONSTRATION:")
            print("-" * 50)
            
            # Show task comparison
            if len(enhanced_queue) >= 3:
                task_ids = [task['id'] for task in enhanced_queue[:3]]
                comparisons = enhanced_service.compare_task_priorities(task_ids)
                
                print("Task Priority Comparison:")
                for comp in comparisons:
                    title = comp.get('title', 'Unknown')[:30]
                    score = comp.get('total_score', 0)
                    factors = ', '.join(comp.get('top_factors', [])[:2])
                    print(f"  • {title}: {score:.0f}pts ({factors})")
            
            # Show available tasks
            available_queue = enhanced_service.get_available_enhanced_queue(limit=3)
            print(f"\nAvailable for Scheduling: {len(available_queue)} tasks")
            for task in available_queue:
                title = task.get('title', 'Unknown')[:30]
                score = task.get('enhanced_priority_score', 0)
                print(f"  • {title}: {score:.0f} points")
            
            print("\n[COMPLETE] DEMO COMPLETE!")
            print("Enhanced Priority Service is working correctly with real data.")
            print("\nAPI Endpoints Available:")
            print("• GET /api/task-queue/enhanced")
            print("• GET /api/task-queue/enhanced/available") 
            print("• GET /api/task-queue/enhanced/context/{task_id}")
            print("• POST /api/task-queue/enhanced/compare")
            
    except Exception as e:
        print(f"[FAIL] Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_enhanced_priority()