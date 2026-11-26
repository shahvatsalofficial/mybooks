import React, { useState, useEffect } from 'react';

interface MetricPayload {
    userId: string;
    action: string;
}

export const ActiveMetricsDashboard: React.FC<{ socket: any }> = ({ socket }) => {
    const [metrics, setMetrics] = useState<MetricPayload[]>([]);
    const [filterTag, setFilterTag] = useState<string>('all');

    useEffect(() => {
        socket.on('metric_update', (data: MetricPayload) => {
            // DANGER: The dependency array is empty [].
            // This closure captures the initial 'metrics' array (empty []) 
            // and the initial 'filterTag' ('all') from the first render.
            // Every time a WebSocket message arrives, this handler filters the data using the stale
            // 'filterTag' and replaces the state, overwriting previous metrics.
            if (filterTag === 'all' || data.action === filterTag) {
                const nextMetrics = [...metrics, data];
                setMetrics(nextMetrics);
            }
        });

        // DANGER: Omitted cleanup function! The socket listener is never removed when the component unmounts,
        // leaking memory and keeping the old component scopes alive in V8 heap memory.
    }, []); 

    return (
        <div>
            <h2>Filter: {filterTag}</h2>
            <button onClick={() => setFilterTag('purchase')}>Show Purchases Only</button>
            <ul>
                {metrics.map((m, idx) => <li key={idx}>{m.userId} - {m.action}</li>)}
            </ul>
        </div>
    );
};
