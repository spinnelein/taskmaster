Milestone 5: Frontend Foundation
IMPORTANT: Clean State Setup
Commands to run FIRST from project root (NOT in backend folder):

cd .. (if you're in backend folder)
git checkout develop
git pull origin develop
git branch -D feature/frontend-setup (if it exists)
git checkout -b feature/frontend-setup

Objective
Set up React frontend with routing and basic layout
Step 1: Create React App with Vite
Commands to run from project root:

npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios react-router-dom
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

Files to Create in Order:
1. frontend/tailwind.config.js
Replace content with:
javascript/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
2. frontend/src/index.css
Replace content with:
css@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
3. frontend/vite.config.js
Replace content with:
javascriptimport { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
4. frontend/src/services/api.js
Create new file:
javascript// API service configuration
// NO EMOJIS
import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Handle specific error statuses
      if (error.response.status === 404) {
        console.error('Resource not found');
      } else if (error.response.status === 500) {
        console.error('Server error');
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
5. frontend/src/services/taskService.js
Create new file:
javascript// Task API service
// NO EMOJIS
import apiClient from './api';

const taskService = {
  // Get all tasks
  getTasks: async (status = null) => {
    const params = status ? { status } : {};
    const response = await apiClient.get('/tasks', { params });
    return response.data;
  },

  // Get single task
  getTask: async (id) => {
    const response = await apiClient.get(`/tasks/${id}`);
    return response.data;
  },

  // Create task
  createTask: async (taskData) => {
    const response = await apiClient.post('/tasks', taskData);
    return response.data;
  },

  // Update task
  updateTask: async (id, taskData) => {
    const response = await apiClient.put(`/tasks/${id}`, taskData);
    return response.data;
  },

  // Delete task
  deleteTask: async (id) => {
    const response = await apiClient.delete(`/tasks/${id}`);
    return response.data;
  },

  // Complete task
  completeTask: async (id) => {
    const response = await apiClient.post(`/tasks/${id}/complete`);
    return response.data;
  },

  // Get overdue tasks
  getOverdueTasks: async () => {
    const response = await apiClient.get('/tasks/overdue');
    return response.data;
  }
};

export default taskService;
6. frontend/src/services/eventService.js
Create new file:
javascript// Event API service
// NO EMOJIS
import apiClient from './api';

const eventService = {
  // Get all events
  getEvents: async (date = null) => {
    const params = date ? { date } : {};
    const response = await apiClient.get('/events', { params });
    return response.data;
  },

  // Get single event
  getEvent: async (id) => {
    const response = await apiClient.get(`/events/${id}`);
    return response.data;
  },

  // Create event
  createEvent: async (eventData) => {
    const response = await apiClient.post('/events', eventData);
    return response.data;
  },

  // Update event
  updateEvent: async (id, eventData) => {
    const response = await apiClient.put(`/events/${id}`, eventData);
    return response.data;
  },

  // Delete event
  deleteEvent: async (id) => {
    const response = await apiClient.delete(`/events/${id}`);
    return response.data;
  }
};

export default eventService;
7. frontend/src/components/layout/Header.jsx
Create new folders and file:
javascript// Header component
// NO EMOJIS
import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold">
            TaskMaster
          </Link>
          <nav className="flex space-x-4">
            <Link to="/" className="hover:text-blue-200">Dashboard</Link>
            <Link to="/tasks" className="hover:text-blue-200">Tasks</Link>
            <Link to="/schedule" className="hover:text-blue-200">Schedule</Link>
            <Link to="/events" className="hover:text-blue-200">Events</Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header;
8. frontend/src/components/layout/Layout.jsx
Create new file:
javascript// Layout wrapper component
// NO EMOJIS
import { Outlet } from 'react-router-dom';
import Header from './Header';

function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
9. frontend/src/pages/Dashboard.jsx
Create new folders and file:
javascript// Dashboard page
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
10. frontend/src/pages/Tasks.jsx
Create new file:
javascript// Tasks page
// NO EMOJIS
import { useState, useEffect } from 'react';
import taskService from '../services/taskService';

function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const data = await taskService.getTasks();
      setTasks(data.tasks);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (taskId) => {
    try {
      await taskService.completeTask(taskId);
      loadTasks(); // Reload tasks
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  };

  const handleDelete = async (taskId) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        await taskService.deleteTask(taskId);
        loadTasks(); // Reload tasks
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading tasks...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Tasks</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          New Task
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <p className="text-gray-500">No tasks yet. Create your first task!</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow">
          <ul className="divide-y">
            {tasks.map((task) => (
              <li key={task.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold">{task.title}</h3>
                    <p className="text-sm text-gray-500">
                      Duration: {task.duration} min | Urgency: {task.urgency}/10
                    </p>
                    {task.description && (
                      <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    {!task.is_completed && (
                      <button
                        onClick={() => handleComplete(task.id)}
                        className="text-green-600 hover:text-green-800"
                      >
                        Complete
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(task.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default Tasks;
11. frontend/src/App.jsx
Replace content with:
javascript// Main App component
// NO EMOJIS
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<Tasks />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
12. frontend/src/main.jsx
Replace content with:
javascript// Main entry point
// NO EMOJIS
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
Commands to Run:
In a NEW terminal (keep backend running):

cd frontend
npm run dev

Frontend should start on http://localhost:5173
Test the Frontend:

Open http://localhost:5173 in your browser
You should see the TaskMaster header
Dashboard should show stats (all zeros initially)
Tasks page should show "No tasks yet"
Navigation should work

Git Commands to Complete:
After frontend is working:

git add .
git commit -m "feat: frontend foundation - React setup with routing and basic pages"
git push origin feature/frontend-setup

Merge to develop:

git checkout develop
git merge feature/frontend-setup
git push origin develop
git branch -d feature/frontend-setup

Success Criteria:

Frontend runs on port 5173
Can navigate between Dashboard and Tasks
API calls work (check Network tab in browser)
Tailwind styling applied
No console errors