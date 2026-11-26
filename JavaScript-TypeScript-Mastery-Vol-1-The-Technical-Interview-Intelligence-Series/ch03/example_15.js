import React, { useState, useEffect } from 'react';

export function CleanAnalyticsDashboard({ connectionUri }) {
    const [liveMetrics, setLiveMetrics] = useState([]);
    const [status, setStatus] = useState("DISCONNECTED");

    useEffect(() => {
        let active = true;
        const socket = new WebSocket(connectionUri);

        const handleOpen = () => {
            if (active) setStatus("CONNECTED");
        };

        const handleMessage = (event) => {
            if (!active) return;
            
            const newMetric = JSON.parse(event.data);
            
            // RESOLVED: Use functional state updater.
            // This decouples the state update from the outer closure,
            // preventing stale references and memory traps.
            setLiveMetrics((prevMetrics) => {
                const updatedMetrics = [...prevMetrics, newMetric];
                // Limit array size in memory to prevent unbounded memory growth
                return updatedMetrics.slice(-100); 
            });
        };

        const handleClose = () => {
            if (active) setStatus("DISCONNECTED");
        };

        socket.addEventListener('open', handleOpen);
        socket.addEventListener('message', handleMessage);
        socket.addEventListener('close', handleClose);

        // RESOLVED: Explicit cleanup return function
        return () => {
            active = false;
            
            socket.removeEventListener('open', handleOpen);
            socket.removeEventListener('message', handleMessage);
            socket.removeEventListener('close', handleClose);
            
            socket.close();
            console.log("WebSocket connection successfully closed and garbage collected.");
        };
    }, [connectionUri]); 

    return (
        <div className="dashboard">
            <span className="status-label">Status: {status}</span>
            <div className="metrics-grid">
                {liveMetrics.slice(-10).map((m, i) => (
                    <div key={i} className="metric-card">{m.value}</div>
                ))}
            </div>
        </div>
    );
}
