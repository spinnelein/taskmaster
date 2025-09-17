import React from 'react';
import { Task } from '../../types';
import { useDrag } from 'react-dnd';

interface DraggableTaskProps {
  task: Task;
}

const DraggableTask: React.FC<DraggableTaskProps> = ({ task }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'task',
    item: { id: task.id },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  });

  const urgencyColor = task.urgency >= 8 ? 'border-red-400' : 
                       task.urgency >= 5 ? 'border-yellow-400' : 
                       'border-gray-300';

  return (
    <div
      ref={drag}
      className={`p-3 bg-white rounded border-l-4 ${urgencyColor} shadow-sm cursor-move hover:shadow-md transition-shadow ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="font-medium text-sm">{task.title}</div>
      <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
        <span>{task.duration} min</span>
        <span>Urgency: {task.urgency}</span>
      </div>
    </div>
  );
};

interface TaskQueueProps {
  tasks: Task[];
  title?: string;
}

const TaskQueue: React.FC<TaskQueueProps> = ({ tasks, title = "Unscheduled Tasks" }) => {
  const pendingTasks = tasks.filter(t => t.completion_status === 'pending');
  
  return (
    <div className="w-64 bg-gray-50 p-4 h-full overflow-y-auto">
      <h3 className="font-semibold mb-4">{title}</h3>
      <div className="space-y-2">
        {pendingTasks.length === 0 ? (
          <p className="text-gray-500 text-sm">No pending tasks</p>
        ) : (
          pendingTasks.map(task => (
            <DraggableTask key={task.id} task={task} />
          ))
        )}
      </div>
    </div>
  );
};

export default TaskQueue;