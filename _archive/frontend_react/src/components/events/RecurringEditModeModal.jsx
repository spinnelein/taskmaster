// Recurring Event Edit Mode Selection Modal
// NO EMOJIS
import React from 'react';
import Modal from '../common/Modal';

function RecurringEditModeModal({ 
  isOpen, 
  onClose, 
  onModeSelect, 
  eventTitle,
  occurrenceDate 
}) {
  const modes = [
    {
      value: 'this_only',
      title: 'This occurrence only',
      description: `Edit only this occurrence on ${occurrenceDate}`,
      color: 'blue'
    },
    {
      value: 'this_and_future',
      title: 'This and future occurrences',
      description: `Edit this occurrence and all future ones (creates a new series)`,
      color: 'purple'
    },
    {
      value: 'all_in_series',
      title: 'All occurrences in the series',
      description: 'Edit the entire recurring series',
      color: 'green'
    }
  ];

  const handleModeClick = (mode) => {
    onModeSelect(mode);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="How do you want to edit this recurring event?">
      <div className="space-y-4">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {eventTitle}
          </h3>
          <p className="text-sm text-gray-600">
            This is a recurring event. Choose how you want to apply your changes:
          </p>
        </div>

        <div className="space-y-3">
          {modes.map((mode) => (
            <button
              key={mode.value}
              onClick={() => handleModeClick(mode.value)}
              className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-start space-x-3">
                <div className={`w-3 h-3 rounded-full bg-${mode.color}-500 mt-2`}></div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{mode.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{mode.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

export default RecurringEditModeModal;