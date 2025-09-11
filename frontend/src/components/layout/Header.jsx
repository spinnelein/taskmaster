// Header component
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