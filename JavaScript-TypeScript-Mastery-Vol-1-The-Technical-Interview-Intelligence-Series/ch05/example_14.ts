import React, { useState, useEffect, useRef } from 'react';

interface MetricPayload {
    userId: string;
    action: string;
}

export const ActiveMetricsDashboardHardened: React.FC<{ socket: any }> = ({ socket }) => {
    const [metrics, setMetrics] = useState<MetricPayload[]>([]);
    const [filterTag, setFilterTag] = useState<string>('all');

    // 1. Maintain live mutable references to variables referenced in the WebSocket callback
    const metricsRef = useRef<MetricPayload[]>(metrics);
    const filterTagRef = useRef<string>(filterTag);

    // Sync refs on every render
    useEffect(() => {
        metricsRef.current = metrics;
        filterTagRef.current = filterTag;
    });

    useEffect(() => {
        const handleMetricUpdate = (data: MetricPayload) => {
            // Read values from the mutable references, avoiding stale closures
            const currentFilter = filterTagRef.current;
            const currentMetrics = metricsRef.current;

            if (currentFilter === 'all' || data.action === currentFilter) {
                const nextMetrics = [...currentMetrics, data];
                setMetrics(nextMetrics);
            }
        };

        // Subscribe to the WebSocket updates
        socket.on('metric_update', handleMetricUpdate);

        // CLEANUP: Unsubscribe from the WebSocket when the component unmounts
        // or before this effect runs again. This frees memory and prevents leaks.
        return () => {
            socket.off('metric_update', handleMetricUpdate);
        };
    }, [socket]); // Re-subscribe only if the socket instance changes

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
