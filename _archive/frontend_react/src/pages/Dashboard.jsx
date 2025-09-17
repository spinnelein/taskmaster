// Dashboard page
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import taskService from '../services/taskService';
import eventService from '../services/eventService';

function Dashboard() {
  const [stats, setStats] = useState({
    totalTasks: 0,
    pendingTasks: 0,
    todayEvents: 0,
    overdueTasks: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Get tasks
      const tasksData = await taskService.getTasks();
      const pendingData = await taskService.getTasks('pending');
      const overdueData = await taskService.getOverdueTasks();
      
      // Get today's events
      const today = new Date().toISOString().split('T')[0];
      const eventsData = await eventService.getEvents(today);
      
      setStats({
        totalTasks: tasksData.total,
        pendingTasks: pendingData.total,
        todayEvents: eventsData.total,
        overdueTasks: overdueData.total
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Total Tasks</h3>
          <p className="text-2xl font-bold">{stats.totalTasks}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Pending Tasks</h3>
          <p className="text-2xl font-bold text-blue-600">{stats.pendingTasks}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Today's Events</h3>
          <p className="text-2xl font-bold text-green-600">{stats.todayEvents}</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Overdue Tasks</h3>
          <p className="text-2xl font-bold text-red-600">{stats.overdueTasks}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Link to="/tasks/new" className="block w-full text-center bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
              Create New Task
            </Link>
            <Link to="/events/new" className="block w-full text-center bg-green-600 text-white py-2 rounded hover:bg-green-700">
              Create New Event
            </Link>
            <Link to="/schedule" className="block w-full text-center bg-purple-600 text-white py-2 rounded hover:bg-purple-700">
              View Today's Schedule
            </Link>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <p className="text-gray-500">No recent activity</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;