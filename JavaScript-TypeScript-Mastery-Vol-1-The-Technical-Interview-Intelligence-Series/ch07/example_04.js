// VulnerableLiveDashboard.js
// Dynamic real-time telemetry dashboard with multiple memory leaks

import React, { useState, useEffect, useRef } from 'react';

// Simulated heavy configuration to accelerate heap depletion
const createHeavyConfig = () => {
    return {
        metadata: new Array(500000).fill("METRIC_PAYLOAD_TOKEN"),
        timestamp: Date.now()
    };
};

export const VulnerableLiveDashboard = ({ symbol }) => {
    const [streamData, setStreamData] = useState([]);
    const [heavyConfig] = useState(createHeavyConfig());
    const socketRef = useRef(null);

    useEffect(() => {
        console.log(`Establishing real-time connection for symbol: ${symbol}`);
        
        // Leak 1: WebSocket connection is opened but never closed on unmount
        const socket = new WebSocket(`wss://api.mockfinance.io/stream/${symbol}`);
        socketRef.current = socket;

        socket.onmessage = (event) => {
            const rawData = JSON.parse(event.data);
            
            // Leak 2: Closure retains the 'heavyConfig' instance
            // The handler captures 'heavyConfig' from the outer lexical scope.
            // Because the socket event listener is never cleaned up, this reference is pinned.
            console.log(`Data received under config timestamp: ${heavyConfig.timestamp}`);

            setStreamData((prev) => {
                const updated = [...prev, rawData];
                // Keep only the latest 100 entries to prevent display bloat
                return updated.slice(-100);
            });
        };

        // Leak 3: Attaching an event listener to the global window object without cleanup
        window.addEventListener('resize', () => {
            console.log(`Dashboard panel resized. Config holds ${heavyConfig.metadata.length} items.`);
        });

        // Fatal Error: Missing return cleanup function!
        // No socket.close(), no window.removeEventListener(), no reference unlinking.
    }, [symbol]);

    return (
        <div id="analytics-panel" style={{ padding: '20px', color: '#FFF', background: '#050505' }}>
            <h2 style={{ color: '#8B5CF6' }}>Trading Telemetry: {symbol}</h2>
            <div className="metrics-grid">
                <p>Telemetry Buffers Active: {streamData.length} entries</p>
                <div style={{ height: '300px', overflowY: 'auto', border: '1px solid #1e293b' }}>
                    {streamData.map((data, idx) => (
                        <div key={idx} style={{ padding: '5px', borderBottom: '1px solid #1e293b' }}>
                            <span>Price Alert: ${data.price}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
