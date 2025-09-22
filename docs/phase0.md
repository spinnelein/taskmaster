PHASE 0: BRANCH AND BASELINE
Step 0.1: Create Feature Branch
bashgit checkout -b feature/advanced-scheduling-with-claude
git push -u origin feature/advanced-scheduling-with-claude
Step 0.2: Document Current System
Create docs/current_system_baseline.md documenting:

Current assignment logic
Current priority scoring (simple linear)
Current task creation process
Current API endpoints
Performance benchmarks with current system

Step 0.3: Test and Document Current Behavior
bash# Test current assignment
curl -X POST http://localhost:5000/api/assignments/bulk-assign > docs/current_bulk_assign_output.json

# Test current task queue
curl http://localhost:5000/api/tasks/queue > docs/current_queue_output.json

# Document response times
time curl http://localhost:5000/api/assignments/bulk-assign
