// n8n Custom Code Node: Working Memory State Reducer
interface AgentWorkingMemory {
  goal: string;
  subtasks: Array<{ id: string; title: string; status: 'pending' | 'in_progress' | 'completed' | 'failed' }>;
  scratchpad: Record<string, any>;
  execution_logs: string[];
}

export function updateWorkingMemory(
  currentState: AgentWorkingMemory, 
  actionResult: { taskId: string; output: any; status: 'completed' | 'failed'; logMessage: string }
): AgentWorkingMemory {
  const updatedSubtasks = currentState.subtasks.map(task => {
    if (task.id === actionResult.taskId) {
      return { ...task, status: actionResult.status };
    }
    return task;
  });

  return {
    ...currentState,
    subtasks: updatedSubtasks,
    scratchpad: {
      ...currentState.scratchpad,
      [actionResult.taskId]: actionResult.output
    },
    execution_logs: [
      ...currentState.execution_logs,
      `[${new Date().toISOString()}] Task ${actionResult.taskId} finished with ${actionResult.status}: ${actionResult.logMessage}`
    ]
  };
}
