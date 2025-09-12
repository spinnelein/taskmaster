// Modern Layout Component
// NO EMOJIS
import { Outlet } from 'react-router-dom';
import SidebarNav from './SidebarNav';
import ModernNav from './ModernNav';
import './ModernLayout.css';

function ModernLayout({ variant = 'sidebar' }) {
  // Two layout variants: 'sidebar' (desktop) and 'top-nav' (mobile/compact)
  
  if (variant === 'top-nav') {
    return (
      <div className="modern-layout top-nav">
        <ModernNav />
        <main className="main-content with-top-nav">
          <div className="content-wrapper">
            <Outlet />
          </div>
        </main>
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
    </div>
  );
}

export default ModernLayout;