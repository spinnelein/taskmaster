// Main App component - UPDATED
// NO EMOJIS
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import NewTask from './pages/NewTask';
import Events from './pages/Events';
import NewEvent from './pages/NewEvent';
import SchedulePage from './pages/SchedulePage';

function App() {
  return (
    <>
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="tasks/new" element={<NewTask />} />
            <Route path="events" element={<Events />} />
            <Route path="events/new" element={<NewEvent />} />
            <Route path="schedule" element={<SchedulePage />} />
          </Route>
        </Routes>
      </Router>
      <Toaster position="top-right" />
    </>
  );
}

export default App;
