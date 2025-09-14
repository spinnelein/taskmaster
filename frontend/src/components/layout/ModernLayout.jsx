// Modern Layout Component
// NO EMOJIS
import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import SidebarNav from './SidebarNav';
import ModernNav from './ModernNav';
import CommandPalette from '../navigation/CommandPalette';
import { NotificationProvider } from '../notifications/NotificationSystem';
import { useCommandPalette } from '../../hooks/useCommandPalette';
import './ModernLayout.css';

function ModernLayoutContent({ variant = 'sidebar' }) {
  const { isOpen, closePalette } = useCommandPalette();

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
    <div className="modern-layout sidebar-layout">
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