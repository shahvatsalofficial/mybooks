import React, { useState } from 'react';

interface Todo {
    id: number;
    text: string;
}

export const TodoListLegacy: React.FC = () => {
    const [todos, setTodos] = useState<Todo[]>([
        { id: 1, text: 'Master closures' },
        { id: 2, text: 'Profile memory leaks' }
    ]);
    
    const [selectedCount, setSelectedCount] = useState(0);

    return (
        <div>
            <h2>Selected Count: {selectedCount}</h2>
            {todos.map((todo) => {
                // DANGER: We are inline-allocating an event handler.
                // If this is passed to a child memoized component, it gets a new
                // handler closure reference on every render, breaking memoization.
                // More seriously, if this handler references stale outer variables,
                // it can perform operations on old todo items.
                const handleSelect = () => {
                    console.log(`Processing todo: ${todo.text}`);
                    setSelectedCount(selectedCount + 1);
                };

                return (
                    <div key={todo.id}>
                        <span>{todo.text}</span>
                        <button onClick={handleSelect}>Select</button>
                    </div>
                );
            })}
        </div>
    );
};
