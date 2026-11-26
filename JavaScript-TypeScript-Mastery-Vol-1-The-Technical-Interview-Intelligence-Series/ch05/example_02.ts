import React, { useState, useEffect } from 'react';

export const StaleCounterComponent: React.FC = () => {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const intervalId = setInterval(() => {
            // DANGER: The dependency array is empty [].
            // This closure captures the 'count' variable from the first render frame (where count = 0).
            // Every time the interval executes, it reads 'count' as 0 and calls setCount(1).
            console.log(`Interval active. Reading count value: ${count}`);
            setCount(count + 1);
        }, 1000);

        return () => clearInterval(intervalId);
    }, []); // Empty dependency array captures initial render values forever

    return (
        <div>
            <h1>Active Count: {count}</h1>
            <button onClick={() => setCount(count + 1)}>Increment</button>
        </div>
    );
};
