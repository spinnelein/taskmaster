// Hook for series management operations
// NO EMOJIS
import { useState } from 'react';

export function useSeriesManagement() {
  const [isSeriesModalOpen, setIsSeriesModalOpen] = useState(false);
  const [selectedSeries, setSelectedSeries] = useState(null);

  const openSeriesModal = (event) => {
    // Determine the master event ID
    const masterEventId = event.master_event_id || 
                         (event.is_recurring ? event.id : null);
    
    if (masterEventId) {
      setSelectedSeries({
        masterEventId,
        title: event.title,
        originalEvent: event
      });
      setIsSeriesModalOpen(true);
    } else {
      console.warn('Cannot open series modal for non-recurring event');
    }
  };

  const closeSeriesModal = () => {
    setIsSeriesModalOpen(false);
    setSelectedSeries(null);
  };

  return {
    isSeriesModalOpen,
    selectedSeries,
    openSeriesModal,
    closeSeriesModal
  };
}