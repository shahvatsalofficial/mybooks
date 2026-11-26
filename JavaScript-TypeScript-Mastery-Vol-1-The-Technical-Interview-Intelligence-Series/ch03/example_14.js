import React, { useState, useEffect } from 'react';

// Vulnerable Dashboard: accumulating active listeners and closures
export function AnalyticsDashboard({ connectionUri }) {
    const [liveMetrics, setLiveMetrics] = useState([]);
    const [status, setStatus] = useState("DISCONNECTED");

    useEffect(() => {
        const socket = new WebSocket(connectionUri);
        
        socket.onopen = () => {
            setStatus("CONNECTED");
        };

        // VULNERABILITY 1: Every time connectionUri changes, a new WebSocket is created,
        // but the event listener below captures a closure referencing liveMetrics
        // and does not close the previous WebSocket.
        socket.onmessage = (event) => {
            const newMetric = JSON.parse(event.data);
            
            // VULNERABILITY 2: Stale closure trap.
            // Because this event handler is not re-registered when liveMetrics changes,
            // it continuously references the initial empty array,
            // preventing the garbage collector from reclaiming older metric payloads.
            setLiveMetrics([...liveMetrics, newMetric]);
        };

        // VULNERABILITY 3: Missing cleanup return function inside useEffect hook.
        // The WebSocket remains open, and its event listeners keep the component
        // context alive in memory after the component unmounts.
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
