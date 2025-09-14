// Smart Notification System
// NO EMOJIS
import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { createPortal } from 'react-dom';
import './NotificationSystem.css';

// Notification Context
const NotificationContext = createContext();

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}

// Notification Types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  SMART_REMINDER: 'smart_reminder',
  CONFLICT_ALERT: 'conflict_alert'
};

// Individual Notification Component
function NotificationItem({ notification, onDismiss, onAction }) {
  const { id, type, title, message, actions, autoHide, duration, progress } = notification;

  useEffect(() => {
    if (autoHide && duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [autoHide, duration, id, onDismiss]);

  const getTypeIcon = (notificationType) => {
    const icons = {
      success: '✓',
      error: '✕',
      warning: '!',
      info: 'i',
      smart_reminder: '💡',
      conflict_alert: '⚠'
    };
    return icons[notificationType] || 'i';
  };

  const handleActionClick = (action) => {
    onAction(id, action);
    if (action.dismissOnClick !== false) {
      onDismiss(id);
    }
  };

  return (
    <div className={`notification notification-${type}`} role="alert">
      {/* Progress bar for timed notifications */}
      {autoHide && duration > 0 && (
        <div className="notification-progress">
          <div 
            className="notification-progress-bar"
            style={{ 
              animation: `progress ${duration}ms linear forwards` 
            }}
          />
        </div>
      )}

      <div className="notification-content">
        <div className="notification-icon">
          {getTypeIcon(type)}
        </div>
        
        <div className="notification-text">
          {title && (
            <div className="notification-title">{title}</div>
          )}
          <div className="notification-message">{message}</div>
        </div>

        <div className="notification-actions">
          {actions?.map((action, index) => (
            <button
              key={index}
              className={`notification-action ${action.variant || 'secondary'}`}
              onClick={() => handleActionClick(action)}
            >
              {action.label}
            </button>
          ))}
          
          <button
            className="notification-dismiss"
            onClick={() => onDismiss(id)}
            aria-label="Dismiss notification"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

// Notification Container
function NotificationContainer({ notifications, onDismiss, onAction }) {
  if (notifications.length === 0) return null;

  return createPortal(
    <div className="notification-container">
      <div className="notification-list">
        {notifications.map(notification => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onDismiss={onDismiss}
            onAction={onAction}
          />
        ))}
      </div>
    </div>,
    document.body
  );
}

// Notification Provider
export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      type: NOTIFICATION_TYPES.INFO,
      autoHide: true,
      duration: 5000,
      ...notification
    };

    setNotifications(prev => [...prev, newNotification]);
    return id;
  }, []);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const handleAction = useCallback((notificationId, action) => {
    if (action.callback) {
      action.callback();
    }
  }, []);

  // Convenience methods for different notification types
  const showSuccess = useCallback((message, options = {}) => {
    return addNotification({
      type: NOTIFICATION_TYPES.SUCCESS,
      message,
      ...options
    });
  }, [addNotification]);

  const showError = useCallback((message, options = {}) => {
    return addNotification({
      type: NOTIFICATION_TYPES.ERROR,
      message,
      autoHide: false, // Error messages should persist
      ...options
    });
  }, [addNotification]);

  const showWarning = useCallback((message, options = {}) => {
    return addNotification({
      type: NOTIFICATION_TYPES.WARNING,
      message,
      duration: 8000,
      ...options
    });
  }, [addNotification]);

  const showInfo = useCallback((message, options = {}) => {
    return addNotification({
      type: NOTIFICATION_TYPES.INFO,
      message,
      ...options
    });
  }, [addNotification]);

  const showSmartReminder = useCallback((message, actions = [], options = {}) => {
    return addNotification({
      type: NOTIFICATION_TYPES.SMART_REMINDER,
      message,
      actions,
      autoHide: false, // Smart reminders should persist
      ...options
    });
  }, [addNotification]);

  const showConflictAlert = useCallback((message, actions = [], options = {}) => {
    return addNotification({
      type: NOTIFICATION_TYPES.CONFLICT_ALERT,
      title: 'Schedule Conflict',
      message,
      actions,
      autoHide: false, // Conflicts should persist until resolved
      ...options
    });
  }, [addNotification]);

  const contextValue = {
    notifications,
    addNotification,
    removeNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showSmartReminder,
    showConflictAlert
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <NotificationContainer
        notifications={notifications}
        onDismiss={removeNotification}
        onAction={handleAction}
      />
    </NotificationContext.Provider>
  );
}

// Smart Notification Hooks
export function useTaskNotifications() {
  const { showSuccess, showSmartReminder } = useNotifications();

  const notifyTaskCompleted = useCallback((task) => {
    showSuccess(`Task "${task.title}" completed!`);
  }, [showSuccess]);

  const notifyDeadlineApproaching = useCallback((task, timeRemaining) => {
    showSmartReminder(
      `Task "${task.title}" is due in ${timeRemaining}`,
      [
        { label: 'Work on it', callback: () => console.log('Navigate to task') },
        { label: 'Snooze', callback: () => console.log('Snooze reminder') }
      ]
    );
  }, [showSmartReminder]);

  const notifyMealPrepTime = useCallback(() => {
    showSmartReminder(
      'You usually meal prep now',
      [
        { label: 'Start meal planning', callback: () => console.log('Navigate to meals') },
        { label: 'Not today', callback: () => console.log('Dismiss') }
      ]
    );
  }, [showSmartReminder]);

  return {
    notifyTaskCompleted,
    notifyDeadlineApproaching,
    notifyMealPrepTime
  };
}

export function useScheduleNotifications() {
  const { showConflictAlert, showWarning } = useNotifications();

  const notifyScheduleConflict = useCallback((conflictingEvents) => {
    const eventNames = conflictingEvents.map(e => e.title).join(' and ');
    showConflictAlert(
      `You have overlapping events: ${eventNames}`,
      [
        { label: 'Resolve', callback: () => console.log('Open conflict resolution') },
        { label: 'Ignore', callback: () => console.log('Ignore conflict') }
      ]
    );
  }, [showConflictAlert]);

  const notifyUpcomingEvent = useCallback((event, timeUntil) => {
    showWarning(
      `"${event.title}" starts in ${timeUntil}`,
      { duration: 10000 }
    );
  }, [showWarning]);

  return {
    notifyScheduleConflict,
    notifyUpcomingEvent
  };
}

export default NotificationProvider;