// Modern Sidebar Navigation Component
// NO EMOJIS
import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import taskService from '../../services/taskService';
import eventService from '../../services/eventService';
import './SidebarNav.css';

function SidebarNav() {
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState(['main']);
  const [taskCount, setTaskCount] = useState(0);
  const [eventCount, setEventCount] = useState(0);

  useEffect(() => {
    loadCounts();
  }, []);

  const loadCounts = async () => {
    try {
      const [tasksResponse, eventsResponse] = await Promise.all([
        taskService.getTasks(),
        eventService.getEvents()
      ]);
      setTaskCount(tasksResponse.tasks?.length || 0);
      setEventCount(eventsResponse.events?.length || 0);
    } catch (error) {
      console.error('Failed to load counts:', error);
    }
  };

  const menuItems = [
    {
      group: 'main',
      items: [
        { 
          path: '/', 
          label: 'Dashboard', 
          icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
          badge: null
        },
        { 
          path: '/schedule', 
          label: 'Schedule', 
          icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
          badge: { type: 'info', count: 5 }
        },
        { 
          path: '/tasks', 
          label: 'Tasks', 
          icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
          badge: taskCount > 0 ? { type: 'warning', count: taskCount } : null
        },
        { 
          path: '/events', 
          label: 'Events', 
          icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
          badge: eventCount > 0 ? { type: 'info', count: eventCount } : null
        }
      ]
    },
    {
      group: 'organize',
      label: 'Organize',
      items: [
        { 
          path: '/projects', 
          label: 'Projects', 
          icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z',
          badge: null
        },
        { 
          path: '/tags', 
          label: 'Tags', 
          icon: 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z',
          badge: null
        },
        { 
          path: '/archive', 
          label: 'Archive', 
          icon: 'M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4',
          badge: null
        }
      ]
    },
    {
      group: 'analytics',
      label: 'Analytics',
      items: [
        { 
          path: '/reports', 
          label: 'Reports', 
          icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
          badge: null
        },
        { 
          path: '/insights', 
          label: 'Insights', 
          icon: 'M13 10V3L4 14h7v7l9-11h-7z',
          badge: { type: 'success', count: 'New' }
        }
      ]
    }
  ];

  const bottomItems = [
    { 
      path: '/settings', 
      label: 'Settings', 
      icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
    },
    { 
      path: '/help', 
      label: 'Help', 
      icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    }
  ];

  const handleRestartServer = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/restart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        // Show success message briefly
        const button = document.querySelector('.restart-server-btn');
        const originalText = button.textContent;
        button.textContent = 'Restarting...';
        button.disabled = true;
        
        // Reset button after delay
        setTimeout(() => {
          if (button) {
            button.textContent = originalText;
            button.disabled = false;
          }
        }, 3000);
      } else {
        console.error('Failed to restart server');
      }
    } catch (error) {
      console.error('Error restarting server:', error);
    }
  };

  const toggleGroup = (group) => {
    setExpandedGroups(prev => 
      prev.includes(group) 
        ? prev.filter(g => g !== group)
        : [...prev, group]
    );
  };

  return (
    <aside className={`modern-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Logo */}
      <div className="sidebar-header">
        <Link to="/" className="sidebar-logo">
          <div className="logo-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="4" width="24" height="24" rx="6" fill="url(#sidegradient)" />
              <path d="M11 16L14 19L21 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <defs>
                <linearGradient id="sidegradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#a855f7" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          {!isCollapsed && <span className="logo-text">TaskMaster</span>}
        </Link>
        
        <button 
          className="collapse-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
              d={isCollapsed ? "M13 5l7 7-7 7M5 5l7 7-7 7" : "M11 19l-7-7 7-7m8 14l-7-7 7-7"} />
          </svg>
        </button>
      </div>

      {/* Search */}
      {!isCollapsed && (
        <div className="sidebar-search">
          <svg className="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input 
            type="text" 
            placeholder="Search..." 
            className="search-input"
          />
        </div>
      )}

      {/* Menu */}
      <nav className="sidebar-menu">
        {menuItems.map((section) => (
          <div key={section.group} className="menu-section">
            {section.label && !isCollapsed && (
              <div 
                className="section-header"
                onClick={() => toggleGroup(section.group)}
              >
                <span>{section.label}</span>
                <svg 
                  className={`section-arrow ${expandedGroups.includes(section.group) ? 'expanded' : ''}`}
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            )}
            
            {(expandedGroups.includes(section.group) || isCollapsed) && (
              <ul className="menu-items">
                {section.items.map((item) => (
                  <li key={item.path}>
                    <Link 
                      to={item.path} 
                      className={`menu-item ${location.pathname === item.path ? 'active' : ''}`}
                      title={isCollapsed ? item.label : ''}
                    >
                      <svg className="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                      </svg>
                      {!isCollapsed && (
                        <>
                          <span className="menu-label">{item.label}</span>
                          {item.badge && (
                            <span className={`menu-badge ${item.badge.type}`}>
                              {item.badge.count}
                            </span>
                          )}
                        </>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </nav>

      {/* Bottom Items */}
      <div className="sidebar-bottom">
        {bottomItems.map((item) => (
          <Link 
            key={item.path}
            to={item.path} 
            className={`menu-item ${location.pathname === item.path ? 'active' : ''}`}
            title={isCollapsed ? item.label : ''}
          >
            <svg className="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
            </svg>
            {!isCollapsed && <span className="menu-label">{item.label}</span>}
          </Link>
        ))}
        
        {/* Development Tools */}
        {process.env.NODE_ENV === 'development' && (
          <button 
            className="menu-item restart-server-btn dev-button"
            onClick={handleRestartServer}
            title={isCollapsed ? 'Restart Server' : ''}
          >
            <svg className="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {!isCollapsed && <span className="menu-label">Restart Server</span>}
          </button>
        )}
        
        {/* User Profile */}
        <div className="user-profile">
          <img 
            src="https://ui-avatars.com/api/?name=User&background=3b82f6&color=fff" 
            alt="Profile" 
            className="user-avatar"
          />
          {!isCollapsed && (
            <div className="user-info">
              <span className="user-name">John Doe</span>
              <span className="user-email">john@example.com</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

export default SidebarNav;