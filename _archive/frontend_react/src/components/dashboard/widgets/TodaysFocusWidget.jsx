// Today's Focus Widget - Shows priority tasks for today
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import taskService from '../../../services/taskService';
import '../widgets.css';

function TodaysFocusWidget({ widgetId, size = 'medium' }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await taskService.getTasks();
      // Handle both old format (array) and new format (object with tasks array)
      const tasksArray = Array.isArray(response) ? response : response.tasks || [];
      // Get top 5 high priority active tasks
      const priorityTasks = tasksArray
        .filter(task => task.status === 'active')
        .sort((a, b) => (b.urgency || 0) - (a.urgency || 0))
        .slice(0, 5);
      setTasks(priorityTasks);
    } catch (err) {
      console.error('Failed to load tasks:', err);
      setError('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleTaskComplete = async (taskId) => {
    try {
      await taskService.completeTask(taskId);
      await loadTasks(); // Reload to update list
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  const getPriorityColor = (urgency) => {
    if (urgency >= 8) return 'bg-red-100 text-red-800';
    if (urgency >= 6) return 'bg-yellow-100 text-yellow-800';
    if (urgency >= 4) return 'bg-blue-100 text-blue-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getPriorityLabel = (urgency) => {
    if (urgency >= 8) return 'High';
    if (urgency >= 6) return 'Med';
    if (urgency >= 4) return 'Low';
    return 'None';
  };

  if (loading) {
    return (
      <div className="widget-loading">
        <div className="loading-spinner">Loading today's focus...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="widget-error">
        <p>Error loading tasks</p>
        <button onClick={loadTasks} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="todays-focus-widget">
      <div className="widget-header">
        <h3 className="widget-title">Today's Focus</h3>
        <Link to="/tasks" className="view-all-link">
          View All
        </Link>
      </div>

      <div className="widget-body">
        {tasks.length === 0 ? (
          <div className="empty-state">
            <p>No active tasks</p>
            <Link to="/tasks/new" className="add-task-btn">
              Create your first task
            </Link>
          </div>
        ) : (
          <div className="task-list">
            {tasks.map(task => (
              <div key={task.id} className="task-item">
                <div className="task-content">
                  <div className="task-header">
                    <span className="task-title">{task.title}</span>
                    <span className={`priority-badge ${getPriorityColor(task.urgency)}`}>
                      {getPriorityLabel(task.urgency)}
                    </span>
                  </div>
                  {task.project && (
                    <div className="task-project">
                      {task.project.name || task.project}
                    </div>
                  )}
                  {task.due_date && (
                    <div className="task-due">
                      Due: {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleTaskComplete(task.id)}
                  className="complete-btn"
                  title="Mark as complete"
                >
                  ✓
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default TodaysFocusWidget;