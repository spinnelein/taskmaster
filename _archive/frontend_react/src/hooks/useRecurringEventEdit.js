// Hook for handling recurring event editing
// NO EMOJIS
import { useState } from 'react';
import eventService from '../services/eventService';

export function useRecurringEventEdit() {
  const [isEditModeModalOpen, setIsEditModeModalOpen] = useState(false);
  const [pendingEdit, setPendingEdit] = useState(null);

  const initiateEdit = (event, updates, occurrenceDate = null) => {
    // Check if this is a recurring event
    if (event.is_recurring || event.master_event_id) {
      // Store the edit details and show the mode selection modal
      setPendingEdit({
        event,
        updates,
        occurrenceDate: occurrenceDate || (event.occurrence_date || event.start_time?.split('T')[0])
      });
      setIsEditModeModalOpen(true);
    } else {
      // Non-recurring event, edit directly
      return executeEdit(event.id, updates, 'single');
    }
  };

  const executeEdit = async (eventId, updates, mode, occurrenceDate = null) => {
    try {
      if (mode === 'single') {
        // Regular event update
        return await eventService.updateEvent(eventId, updates);
      } else {
        // Recurring event update
        const editRequest = {
          edit_mode: mode,
          original_date: occurrenceDate ? `${occurrenceDate}T00:00:00` : null,
          event_data: updates
        };
        
        return await eventService.updateRecurringEvent(eventId, editRequest);
      }
    } catch (error) {
      console.error('Failed to update event:', error);
      throw error;
    }
  };

  const handleModeSelect = async (mode) => {
    if (!pendingEdit) return;

    const { event, updates, occurrenceDate } = pendingEdit;
    
    try {
      const result = await executeEdit(event.id, updates, mode, occurrenceDate);
      
      // Clear pending edit
      setPendingEdit(null);
      setIsEditModeModalOpen(false);
      
      return result;
    } catch (error) {
      // Keep modal open on error so user can try again or cancel
      throw error;
    }
  };

  const cancelEdit = () => {
    setPendingEdit(null);
    setIsEditModeModalOpen(false);
  };

  return {
    isEditModeModalOpen,
    pendingEdit,
    initiateEdit,
    handleModeSelect,
    cancelEdit
  };
}