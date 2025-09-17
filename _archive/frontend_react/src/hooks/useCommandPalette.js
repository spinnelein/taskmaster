// Global Command Palette Hook
// NO EMOJIS
import { useState, useEffect, useCallback } from 'react';

export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  const openPalette = useCallback(() => setIsOpen(true), []);
  const closePalette = useCallback(() => setIsOpen(false), []);
  const togglePalette = useCallback(() => setIsOpen(prev => !prev), []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      // Cmd+K (Mac) or Ctrl+K (Windows/Linux)
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        togglePalette();
        return;
      }

      // Question mark for help
      if (event.key === '?' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        // Only if not in an input field
        const activeElement = document.activeElement;
        const isInInput = activeElement && (
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          activeElement.contentEditable === 'true'
        );
        
        if (!isInInput) {
          event.preventDefault();
          openPalette();
        }
        return;
      }

      // Escape to close
      if (event.key === 'Escape' && isOpen) {
        event.preventDefault();
        closePalette();
        return;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, togglePalette, openPalette, closePalette]);

  return {
    isOpen,
    openPalette,
    closePalette,
    togglePalette
  };
}