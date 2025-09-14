// Event Form Modal wrapper - demonstrates the new modal system
// NO EMOJIS
import Modal from '../common/Modal';
import EventFormEnhanced from './EventFormEnhanced';

function EventFormModal({ isOpen, onClose, event, onSubmit }) {
  const handleSubmit = (formData) => {
    onSubmit?.(formData);
    onClose?.();
  };

  const handleCancel = () => {
    onClose?.();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={event ? 'Edit Event' : 'Create New Event'}
      maxWidth="800px"
      maxHeight="90vh"
      scrollable={true}
      closeOnEscape={true}
      closeOnBackdrop={true}
      responsive={true}
    >
      <EventFormEnhanced
        event={event}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
      />
    </Modal>
  );
}

export default EventFormModal;