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
import InitiativesContainer from './pages/InitiativesContainer';
import Projects from './pages/Projects';
import InitiativeDetail from './pages/InitiativeDetail';
import InitiativeTasks from './pages/InitiativeTasks';
import ProjectDetail from './pages/ProjectDetail';
import NewInitiative from './pages/NewInitiative';
import EditInitiative from './pages/EditInitiative';

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
          <Route path="initiatives" element={<InitiativesContainer />} />
          <Route path="initiatives/new" element={<NewInitiative />} />
          <Route path="initiatives/:id" element={<InitiativeDetail />} />
          <Route path="initiatives/:id/edit" element={<EditInitiative />} />
          <Route path="initiatives/:id/tasks" element={<InitiativeTasks />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
