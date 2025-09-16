// Series Management Modal
// NO EMOJIS
import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import eventService from '../../services/eventService';
import { format, parseISO } from 'date-fns';

function SeriesManagementModal({ 
  isOpen, 
  onClose, 
  masterEventId,
  eventTitle,
  onSeriesDeleted 
}) {
  const [occurrences, setOccurrences] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && masterEventId) {
      loadOccurrences();
    }
  }, [isOpen, masterEventId]);

  const loadOccurrences = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get occurrences for the next 3 months
      const today = new Date();
      const threeMonthsFromNow = new Date();
      threeMonthsFromNow.setMonth(today.getMonth() + 3);
      
      const expansionData = await eventService.getEventOccurrences(
        masterEventId,
        format(today, 'yyyy-MM-dd'),
        format(threeMonthsFromNow, 'yyyy-MM-dd'),
        100 // Max 100 occurrences
      );
      
      setOccurrences(expansionData.occurrences || []);
      
    } catch (err) {
      setError('Failed to load series occurrences');
      console.error('Error loading occurrences:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSeries = async () => {
    if (!window.confirm('Are you sure you want to delete the entire recurring series? This cannot be undone.')) {
      return;
    }

    try {
      await eventService.deleteRecurringEvent(masterEventId, 'all_in_series');
      
      // Notify parent component that series was deleted so it can reload
      if (onSeriesDeleted) {
        onSeriesDeleted();
      }
      
      onClose();
    } catch (err) {
      setError('Failed to delete series');
      console.error('Error deleting series:', err);
    }
  };

  const handleRemoveException = async (occurrenceDate) => {
    // TODO: Implement remove exception functionality
    console.log('Remove exception for:', occurrenceDate);
  };

  const formatOccurrenceDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM d, yyyy');
    } catch {
      return dateStr;
    }
  };

  const formatOccurrenceTime = (dateTimeStr) => {
    try {
      return format(parseISO(dateTimeStr), 'h:mm a');
    } catch {
      return '';
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Manage Series: ${eventTitle}`} size="large">
      <div className="space-y-6">
        {/* Series Overview */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">Series Overview</h3>
          <div className="text-sm text-gray-600">
            <div>Total occurrences shown: {occurrences.length}</div>
            <div>Exceptions: {occurrences.filter(occ => occ.is_exception).length}</div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="text-gray-600">Loading occurrences...</div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-red-800">{error}</div>
            <button
              onClick={loadOccurrences}
              className="mt-2 text-sm text-red-600 hover:text-red-800"
            >
              Try again
            </button>
          </div>
        )}

        {/* Occurrences List */}
        {!loading && !error && (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            <h3 className="font-medium text-gray-900 sticky top-0 bg-white py-2">
              Upcoming Occurrences
            </h3>
            {occurrences.map((occurrence, index) => (
              <div
                key={occurrence.id}
                className={`flex items-center justify-between p-3 border rounded-lg ${
                  occurrence.is_exception 
                    ? 'border-orange-200 bg-orange-50' 
                    : 'border-gray-200'
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <div className="font-medium">
                      {formatOccurrenceDate(occurrence.occurrence_date)}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatOccurrenceTime(occurrence.start)}
                    </div>
                    {occurrence.is_exception && (
                      <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                        Modified
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    {occurrence.title}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {occurrence.is_exception && (
                    <button
                      onClick={() => handleRemoveException(occurrence.occurrence_date)}
                      className="text-sm text-orange-600 hover:text-orange-800"
                    >
                      Reset
                    </button>
                  )}
                  <button
                    onClick={() => console.log('Edit occurrence:', occurrence.id)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                </div>
              </div>
            ))}
            
            {occurrences.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                No upcoming occurrences found
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center pt-4 border-t border-gray-200">
          <button
            onClick={handleDeleteSeries}
            className="px-4 py-2 text-sm font-medium text-red-700 bg-red-100 border border-red-300 rounded-md hover:bg-red-200"
          >
            Delete Entire Series
          </button>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

export default SeriesManagementModal;