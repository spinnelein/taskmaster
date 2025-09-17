// Modern Layout Component
// NO EMOJIS
import { Outlet } from 'react-router-dom';
import { useState, createContext, useContext } from 'react';
import SidebarNav from './SidebarNav';
import ModernNav from './ModernNav';
import CommandPalette from '../navigation/CommandPalette';
import { NotificationProvider } from '../notifications/NotificationSystem';
import { useCommandPalette } from '../../hooks/useCommandPalette';
import './ModernLayout.css';

// Context for sidebar state
const SidebarContext = createContext();

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};

function ModernLayoutContent({ variant = 'sidebar' }) {
  const { isOpen, closePalette } = useCommandPalette();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  if (variant === 'top-nav') {
    return (
      <div className="modern-layout top-nav">
        <ModernNav />
        <main className="main-content with-top-nav">
          <div className="content-wrapper">
            <Outlet />
          </div>
        </main>
        
        {/* Global Command Palette */}
        <CommandPalette 
          isOpen={isOpen} 
          onClose={closePalette} 
        />
      </div>
    );
  }

  return (
    <SidebarContext.Provider value={{ isSidebarCollapsed, setIsSidebarCollapsed }}>
      <div className={`modern-layout sidebar-layout ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <SidebarNav />
        <main className="main-content with-sidebar">
          <div className="content-wrapper">
            <Outlet />
          </div>
        </main>
        
        {/* Global Command Palette */}
        <CommandPalette 
          isOpen={isOpen} 
          onClose={closePalette} 
        />
      </div>
    </SidebarContext.Provider>
  );
}

function ModernLayout(props) {
  return (
    <NotificationProvider>
      <ModernLayoutContent {...props} />
    </NotificationProvider>
  );
}

export default ModernLayout;