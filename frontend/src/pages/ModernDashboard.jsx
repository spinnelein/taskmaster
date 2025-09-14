// Modern Dashboard Component
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardGrid from '../components/dashboard/DashboardGrid';
import TodaysFocusWidget from '../components/dashboard/widgets/TodaysFocusWidget';
import CalendarSnapshotWidget from '../components/dashboard/widgets/CalendarSnapshotWidget';
import taskService from '../services/taskService';
import eventService from '../services/eventService';
import { parsePacificTime, isTodayPacific, formatPacificTime } from '../utils/timezone';
import './ModernDashboard.css';

function ModernDashboard() {
  const [greeting, setGreeting] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [dashboardData, setDashboardData] = useState({
    tasks: [],
    events: [],
    stats: {
      todayTasks: 0,
      completedTasks: 0,
      upcomingEvents: 0,
      timeSpent: '0h 0m'
    }
  });

  useEffect(() => {
    const hours = new Date().getHours();
    if (hours < 12) setGreeting('Good morning');
    else if (hours < 18) setGreeting('Good afternoon');
    else setGreeting('Good evening');

    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    loadDashboardData();

    return () => clearInterval(timer);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [tasksResponse, eventsResponse] = await Promise.all([
        taskService.getTasks(),
        eventService.getEvents()
      ]);
      
      const tasks = tasksResponse.tasks || [];
      const events = eventsResponse.events || [];
      
      const completedTasksCount = tasks.filter(task => task.status === 'completed').length;
      
      // Process today's events
      const todayEvents = events.filter(event => {
        return isTodayPacific(event.start_time);
      }).slice(0, 5).map(event => ({
        id: event.id,
        title: event.title,
        time: formatPacificTime(event.start_time),
        type: event.type || 'event',
        duration: event.end_time ? 
          Math.round((parsePacificTime(event.end_time) - parsePacificTime(event.start_time)) / (1000 * 60)) + 'm' : 
          '30m'
      }));

      // Update dashboard data
      setDashboardData({
        tasks: tasks.slice(0, 6), // Top 6 tasks for widget
        events: todayEvents,
        stats: {
          todayTasks: tasks.length,
          completedTasks: completedTasksCount,
          upcomingEvents: events.length,
          timeSpent: '3h 25m' // This would need time tracking to be real
        }
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const handleLayoutChange = (newLayout) => {
    console.log('Dashboard layout changed:', newLayout);
    // Here you could save layout preferences to localStorage or API
  };

  const handleTaskComplete = async (taskId) => {
    try {
      await taskService.completeTask(taskId);
      // Reload data to reflect changes
      loadDashboardData();
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  };

  return (
    <div className="modern-dashboard">
      {/* Hero Section - Simplified */}
      <section className="dashboard-hero mb-6">
        <div className="hero-content">
          <div className="hero-greeting">
            <h1 className="text-3xl font-bold text-gray-900">{greeting}, User!</h1>
            <p className="text-gray-600 mt-2">Here's your productivity overview for today</p>
          </div>
          <div className="hero-time">
            <div className="current-time text-2xl font-semibold text-blue-600">
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div className="current-date text-gray-500">
              {currentTime.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </div>
          </div>
        </div>
      </section>

      {/* Enhanced Dashboard Grid with Widget System */}
      <DashboardGrid 
        onLayoutChange={handleLayoutChange}
        customizable={true}
      >
        {/* Pass real data to widgets through context or props */}
        <TodaysFocusWidget 
          tasks={dashboardData.tasks}
          onTaskComplete={handleTaskComplete}
        />
        <CalendarSnapshotWidget 
          events={dashboardData.events}
          stats={dashboardData.stats}
        />
      </DashboardGrid>
    </div>
  );
}

export default ModernDashboard;