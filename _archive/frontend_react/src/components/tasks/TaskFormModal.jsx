// Task Form Modal wrapper - demonstrates the new modal system
// NO EMOJIS
import Modal from '../common/Modal';
import TaskForm from './TaskForm';

function TaskFormModal({ isOpen, onClose, task, onSubmit }) {
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
      title={task ? 'Edit Task' : 'Create New Task'}
      maxWidth="700px"
      maxHeight="90vh"
      scrollable={true}
      closeOnEscape={true}
      closeOnBackdrop={true}
      responsive={true}
    >
      <TaskForm
        task={task}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
      />
    </Modal>
  );
}

export default TaskFormModal;