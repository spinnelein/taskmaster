// Modern Dashboard Component
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import taskService from '../services/taskService';
import eventService from '../services/eventService';
import { parsePacificTime, isTodayPacific, formatPacificTime } from '../utils/timezone';
import './ModernDashboard.css';

function ModernDashboard() {
  const [greeting, setGreeting] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [stats, setStats] = useState({
    todayTasks: 0,
    completedTasks: 0,
    upcomingEvents: 0,
    timeSpent: '0h 0m'
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
      
      setStats({
        todayTasks: tasks.length,
        completedTasks: completedTasksCount,
        upcomingEvents: events.length,
        timeSpent: '3h 25m' // This would need time tracking to be real
      });

      // Update recentTasks with real data
      setRecentTasks(tasks.slice(0, 4).map(task => ({
        id: task.id,
        title: task.title,
        status: task.status || 'active',
        priority: task.priority || 'medium'
      })));

      // Update upcomingEvents with real data
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
      setUpcomingEvents(todayEvents);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const quickActions = [
    { icon: 'M12 4v16m8-8H4', label: 'New Task', color: 'primary', path: '/tasks/new' },
    { icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z', label: 'New Event', color: 'accent', path: '/events/new' },
    { icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', label: 'View Schedule', color: 'success', path: '/schedule' },
    { icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', label: 'Analytics', color: 'info', path: '/analytics' }
  ];

  const [upcomingEvents, setUpcomingEvents] = useState([]);

  const [recentTasks, setRecentTasks] = useState([]);

  const productivityData = [
    { day: 'Mon', hours: 6 },
    { day: 'Tue', hours: 8 },
    { day: 'Wed', hours: 7 },
    { day: 'Thu', hours: 9 },
    { day: 'Fri', hours: 5 },
    { day: 'Sat', hours: 3 },
    { day: 'Sun', hours: 2 }
  ];

  const maxHours = Math.max(...productivityData.map(d => d.hours));

  const toggleTaskCompletion = async (taskId) => {
    try {
      // Update task status via API
      await taskService.completeTask(taskId);
      
      // Update local state
      setRecentTasks(prevTasks => 
        prevTasks.map(task => {
          if (task.id === taskId) {
            const newStatus = task.status === 'completed' ? 'active' : 'completed';
            return { ...task, status: newStatus };
          }
          return task;
        })
      );

      // Update stats when task status changes
      setStats(prevStats => {
        const newCompletedCount = recentTasks.filter(task => 
          task.id === taskId ? task.status !== 'completed' : task.status === 'completed'
        ).length + (recentTasks.find(task => task.id === taskId)?.status !== 'completed' ? 1 : 0);
        
        return {
          ...prevStats,
          completedTasks: newCompletedCount
        };
      });
    } catch (error) {
      console.error('Failed to toggle task completion:', error);
    }
  };

  return (
    <div className="modern-dashboard">
      {/* Hero Section */}
      <section className="dashboard-hero">
        <div className="hero-content">
          <div className="hero-greeting">
            <h1>{greeting}, User!</h1>
            <p>Here's your productivity overview for today</p>
          </div>
          <div className="hero-time">
            <div className="current-time">
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div className="current-date">
              {currentTime.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </div>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon primary">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.todayTasks}</div>
            <div className="stat-label">Today's Tasks</div>
          </div>
          <div className="stat-trend up">+12%</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon success">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.completedTasks}</div>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat-progress">
            <div className="progress-bar" style={{width: `${(stats.completedTasks/stats.todayTasks) * 100}%`}}></div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon accent">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.upcomingEvents}</div>
            <div className="stat-label">Upcoming Events</div>
          </div>
          <div className="stat-trend">Today</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon info">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.timeSpent}</div>
            <div className="stat-label">Time Tracked</div>
          </div>
          <div className="stat-trend down">-8%</div>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          {quickActions.map((action, index) => (
            <Link key={index} to={action.path} className={`action-card ${action.color}`}>
              <div className="action-icon">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={action.icon} />
                </svg>
              </div>
              <span>{action.label}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Upcoming Events */}
        <section className="dashboard-card events-card">
          <div className="card-header">
            <h3>Today's Schedule</h3>
            <Link to="/schedule" className="card-action">View All</Link>
          </div>
          <div className="events-list">
            {upcomingEvents.map(event => (
              <div key={event.id} className={`event-item ${event.type}`}>
                <div className="event-time">
                  <span>{event.time}</span>
                  <span className="event-duration">{event.duration}</span>
                </div>
                <div className="event-details">
                  <h4>{event.title}</h4>
                  <span className={`event-badge ${event.type}`}>{event.type}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Recent Tasks */}
        <section className="dashboard-card tasks-card">
          <div className="card-header">
            <h3>Recent Tasks</h3>
            <Link to="/tasks" className="card-action">View All</Link>
          </div>
          <div className="tasks-list">
            {recentTasks.map(task => (
              <div key={task.id} className="task-item">
                <input 
                  type="checkbox" 
                  checked={task.status === 'completed'}
                  onChange={() => toggleTaskCompletion(task.id)} 
                  className="task-checkbox"
                />
                <div className="task-content">
                  <h4 className={task.status === 'completed' ? 'completed' : ''}>
                    {task.title}
                  </h4>
                  <div className="task-meta">
                    <span className={`task-status ${task.status}`}>{task.status}</span>
                    <span className={`task-priority ${task.priority}`}>{task.priority}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Productivity Chart */}
        <section className="dashboard-card productivity-card">
          <div className="card-header">
            <h3>Weekly Productivity</h3>
            <span className="card-subtitle">Hours tracked per day</span>
          </div>
          <div className="chart-container">
            <div className="bar-chart">
              {productivityData.map((data, index) => (
                <div key={index} className="chart-bar-wrapper">
                  <div className="chart-bar-container">
                    <div 
                      className="chart-bar"
                      style={{ height: `${(data.hours / maxHours) * 100}%` }}
                    >
                      <span className="bar-value">{data.hours}h</span>
                    </div>
                  </div>
                  <span className="chart-label">{data.day}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default ModernDashboard;