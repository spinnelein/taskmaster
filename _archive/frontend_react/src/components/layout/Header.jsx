// Header component
// NO EMOJIS
import { Link } from 'react-router-dom';
import apiClient from '../../services/api';

function Header() {
  const restartServer = () => {
    console.log('To restart the server, run: python dev_restart.py');
    alert('To restart the server:\n1. Open terminal in project root\n2. Run: python dev_restart.py\n3. Or double-click restart.bat');
  };

  return (
    <header className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold">
            TaskMaster
          </Link>
          <nav className="flex items-center space-x-4">
            <Link to="/" className="hover:text-blue-200">Dashboard</Link>
            <Link to="/tasks" className="hover:text-blue-200">Tasks</Link>
            <Link to="/schedule" className="hover:text-blue-200">Schedule</Link>
            <Link to="/events" className="hover:text-blue-200">Events</Link>
            <button 
              onClick={restartServer}
              className="bg-red-500 hover:bg-red-600 px-3 py-1 rounded text-sm"
              title="Restart Backend Server"
            >
              Restart
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header;