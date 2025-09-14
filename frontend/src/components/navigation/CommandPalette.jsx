// Command Palette - Keyboard-first navigation
// NO EMOJIS
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Modal from '../common/Modal';
import './CommandPalette.css';

const COMMANDS = [
  // Navigation Commands
  { id: 'nav-dashboard', label: 'Go to Dashboard', icon: 'HOME', shortcut: 'D', action: 'navigate', target: '/' },
  { id: 'nav-tasks', label: 'Go to Tasks', icon: 'TASK', shortcut: 'T', action: 'navigate', target: '/tasks' },
  { id: 'nav-events', label: 'Go to Events', icon: 'CAL', shortcut: 'E', action: 'navigate', target: '/events' },
  { id: 'nav-schedule', label: 'Go to Schedule', icon: 'SCHED', shortcut: 'S', action: 'navigate', target: '/schedule' },
  { id: 'nav-projects', label: 'Go to Projects', icon: 'PROJ', shortcut: 'P', action: 'navigate', target: '/projects' },
  { id: 'nav-initiatives', label: 'Go to Initiatives', icon: 'INIT', shortcut: 'I', action: 'navigate', target: '/initiatives' },
  
  // Creation Commands
  { id: 'create-task', label: 'Create New Task', icon: 'ADD', shortcut: 'Shift+T', action: 'create', target: 'task' },
  { id: 'create-event', label: 'Create New Event', icon: 'ADD', shortcut: 'Shift+E', action: 'create', target: 'event' },
  { id: 'create-project', label: 'Create New Project', icon: 'ADD', shortcut: 'Shift+P', action: 'create', target: 'project' },
  { id: 'create-initiative', label: 'Create New Initiative', icon: 'ADD', shortcut: 'Shift+I', action: 'create', target: 'initiative' },
  
  // Quick Actions
  { id: 'quick-search', label: 'Search Everything', icon: 'SEARCH', shortcut: '/', action: 'search', target: 'global' },
  { id: 'toggle-theme', label: 'Toggle Dark Mode', icon: 'THEME', shortcut: 'Shift+D', action: 'toggle', target: 'theme' },
  { id: 'keyboard-shortcuts', label: 'View Keyboard Shortcuts', icon: 'HELP', shortcut: '?', action: 'show', target: 'shortcuts' },
  
  // Demo & Testing
  { id: 'ui-demo', label: 'View UI Demo', icon: 'DEMO', shortcut: 'Shift+U', action: 'navigate', target: '/ui-demo' },
  { id: 'phase2-demo', label: 'View Phase 2 Demo', icon: 'DEMO', shortcut: 'Shift+2', action: 'navigate', target: '/phase2-demo' }
];

function CommandPalette({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filteredCommands, setFilteredCommands] = useState(COMMANDS);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Filter commands based on query
  useEffect(() => {
    if (!query.trim()) {
      setFilteredCommands(COMMANDS);
    } else {
      const filtered = COMMANDS.filter(command =>
        command.label.toLowerCase().includes(query.toLowerCase()) ||
        command.shortcut.toLowerCase().includes(query.toLowerCase()) ||
        command.action.toLowerCase().includes(query.toLowerCase())
      );
      setFilteredCommands(filtered);
    }
    setSelectedIndex(0);
  }, [query]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          executeCommand(filteredCommands[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
      default:
        break;
    }
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  // Execute selected command
  const executeCommand = useCallback((command) => {
    switch (command.action) {
      case 'navigate':
        navigate(command.target);
        break;
      case 'create':
        // Would open create modals
        console.log(`Create ${command.target}`);
        break;
      case 'search':
        // Would open search interface
        console.log('Open global search');
        break;
      case 'toggle':
        if (command.target === 'theme') {
          // Would toggle theme
          console.log('Toggle theme');
        }
        break;
      case 'show':
        if (command.target === 'shortcuts') {
          // Would show shortcuts help
          console.log('Show keyboard shortcuts');
        }
        break;
      default:
        console.log(`Execute: ${command.label}`);
    }
    onClose();
  }, [navigate, onClose]);

  // Handle command click
  const handleCommandClick = useCallback((command, index) => {
    setSelectedIndex(index);
    executeCommand(command);
  }, [executeCommand]);

  // Global keyboard listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const getCommandIcon = (iconType) => {
    const icons = {
      HOME: 'H',
      TASK: 'T',
      CAL: 'C',
      SCHED: 'S',
      PROJ: 'P',
      INIT: 'I',
      ADD: '+',
      SEARCH: '?',
      THEME: 'TH',
      HELP: 'H',
      DEMO: 'D'
    };
    return icons[iconType] || '•';
  };

  const formatShortcut = (shortcut) => {
    return shortcut
      .replace('Shift+', '⇧')
      .replace('Cmd+', '⌘')
      .replace('Ctrl+', '⌃')
      .replace('Alt+', '⌥');
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title=""
      maxWidth="600px"
      maxHeight="60vh"
      scrollable={false}
      closeOnEscape={true}
      closeOnBackdrop={true}
      className="command-palette-modal"
    >
      <div className="command-palette">
        {/* Search Input */}
        <div className="command-search">
          <div className="command-search-icon">
            {getCommandIcon('SEARCH')}
          </div>
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="command-input"
            autoComplete="off"
            spellCheck="false"
          />
          <div className="command-search-hint">
            <kbd>↑</kbd> <kbd>↓</kbd> to navigate <kbd>⏎</kbd> to select <kbd>esc</kbd> to cancel
          </div>
        </div>

        {/* Command List */}
        <div className="command-list">
          {filteredCommands.length > 0 ? (
            <>
              {/* Group commands by category */}
              {getCommandGroups(filteredCommands).map(group => (
                <div key={group.category} className="command-group">
                  <div className="command-group-header">
                    {group.category}
                  </div>
                  {group.commands.map((command, index) => {
                    const globalIndex = filteredCommands.indexOf(command);
                    return (
                      <div
                        key={command.id}
                        className={`command-item ${globalIndex === selectedIndex ? 'selected' : ''}`}
                        onClick={() => handleCommandClick(command, globalIndex)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                      >
                        <div className="command-icon">
                          {getCommandIcon(command.icon)}
                        </div>
                        <div className="command-content">
                          <div className="command-label">
                            {highlightQuery(command.label, query)}
                          </div>
                          {command.description && (
                            <div className="command-description">
                              {command.description}
                            </div>
                          )}
                        </div>
                        <div className="command-shortcut">
                          <kbd>{formatShortcut(command.shortcut)}</kbd>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </>
          ) : (
            <div className="command-empty">
              <div className="command-empty-icon">?</div>
              <div className="command-empty-text">
                No commands found for "{query}"
              </div>
              <div className="command-empty-hint">
                Try searching for "task", "event", or "project"
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="command-footer">
          <div className="command-footer-text">
            Press <kbd>?</kbd> anytime to open this palette
          </div>
        </div>
      </div>
    </Modal>
  );
}

// Helper function to group commands
function getCommandGroups(commands) {
  const groups = {
    'Navigation': [],
    'Create': [],
    'Actions': [],
    'Demo': []
  };

  commands.forEach(command => {
    if (command.action === 'navigate' && !command.target.includes('demo')) {
      groups.Navigation.push(command);
    } else if (command.action === 'create') {
      groups.Create.push(command);
    } else if (command.target.includes('demo')) {
      groups.Demo.push(command);
    } else {
      groups.Actions.push(command);
    }
  });

  return Object.entries(groups)
    .filter(([_, commands]) => commands.length > 0)
    .map(([category, commands]) => ({ category, commands }));
}

// Helper function to highlight search query
function highlightQuery(text, query) {
  if (!query.trim()) return text;
  
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);
  
  return parts.map((part, index) => 
    regex.test(part) ? <mark key={index}>{part}</mark> : part
  );
}

export default CommandPalette;