// Modern TaskMaster App
// NO EMOJIS
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ModernLayout from './components/layout/ModernLayout';
import ModernDashboard from './pages/ModernDashboard';
import Tasks from './pages/Tasks';
import NewTask from './pages/NewTask';
import Events from './pages/Events';
import NewEvent from './pages/NewEvent';
import SchedulePage from './pages/SchedulePage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ModernLayout />}>
          <Route index element={<ModernDashboard />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="tasks/new" element={<NewTask />} />
          <Route path="events" element={<Events />} />
          <Route path="events/new" element={<NewEvent />} />
          <Route path="schedule" element={<SchedulePage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
