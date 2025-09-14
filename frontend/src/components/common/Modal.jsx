// Modern Modal component with auto-sizing and responsive design
// NO EMOJIS
import { useEffect, useRef } from 'react';
import './Modal.css';

function Modal({ 
  isOpen = true,
  onClose,
  title,
  children,
  maxWidth = '600px',
  maxHeight = '90vh',
  scrollable = true,
  closeOnEscape = true,
  closeOnBackdrop = true,
  responsive = true
}) {
  const modalRef = useRef();
  const contentRef = useRef();

  // Handle escape key
  useEffect(() => {
    if (!closeOnEscape) return;

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        onClose?.();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      return () => document.removeEventListener('keydown', handleEscapeKey);
    }
  }, [isOpen, closeOnEscape, onClose]);

  // Handle backdrop click
  const handleBackdropClick = (event) => {
    if (closeOnBackdrop && event.target === modalRef.current) {
      onClose?.();
    }
  };

  // Focus trap
  useEffect(() => {
    if (!isOpen) return;

    const modal = modalRef.current;
    if (!modal) return;

    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (event) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    };

    modal.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => modal.removeEventListener('keydown', handleTabKey);
  }, [isOpen]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div 
      ref={modalRef}
      className="modal-backdrop"
      onClick={handleBackdropClick}
      style={{
        '--modal-max-width': maxWidth,
        '--modal-max-height': maxHeight
      }}
    >
      <div 
        ref={contentRef}
        className={`modal-content ${responsive ? 'modal-responsive' : ''} ${scrollable ? 'modal-scrollable' : ''}`}
      >
        {title && (
          <div className="modal-header">
            <h2 className="modal-title">{title}</h2>
            {onClose && (
              <button 
                className="modal-close-btn"
                onClick={onClose}
                aria-label="Close modal"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path 
                    d="M18 6L6 18M6 6L18 18" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            )}
          </div>
        )}
        
        <div className={`modal-body ${scrollable ? 'modal-body-scrollable' : ''}`}>
          {children}
        </div>
      </div>
    </div>
  );
}

export default Modal;