// HardenedLiveDashboard.tsx
// Fully sanitized, memory-safe trading telemetry component

import React, { useState, useEffect, useRef } from 'react';

export interface TelemetryData {
    price: number;
    timestamp: number;
}

export interface HeavyConfig {
    metadata: string[];
    timestamp: number;
}

const createHeavyConfig = (): HeavyConfig => {
    return {
        metadata: new Array(500000).fill("METRIC_PAYLOAD_TOKEN"),
        timestamp: Date.now()
    };
};

export const HardenedLiveDashboard: React.FC<{ symbol: string }> = ({ symbol }) => {
    const [streamData, setStreamData] = useState<TelemetryData[]>([]);
    const [heavyConfig] = useState<HeavyConfig>(createHeavyConfig);
    
    // Using explicit typing for the socket ref
    const socketRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        console.log(`[Dashboard] Initializing telemetry stream for symbol: ${symbol}`);
        
        // Establish connection inside the safe boundary
        const socket = new WebSocket(`wss://api.mockfinance.io/stream/${symbol}`);
        socketRef.current = socket;

        // Establish the handler as a named function reference to ensure clean dereferencing
        const handleWebSocketMessage = (event: MessageEvent) => {
            try {
                const rawData: TelemetryData = JSON.parse(event.data);
                
                // Secure logging accessing config values safely
                console.log(`[Telemetry] Active stream verification. Config: ${heavyConfig.timestamp}`);

                // Prevent state setters from capturing outer variables directly
                setStreamData((prev) => {
                    const updated = [...prev, rawData];
                    return updated.slice(-100);
                });
            } catch (err) {
                console.error("[Telemetry] Failed to parse message payload:", err);
            }
        };

        // Attach listeners using strict event handler definitions
        socket.addEventListener('message', handleWebSocketMessage);

        const handleResize = () => {
            // Safe, read-only window measurement callback
            console.log(`[Layout] Workspace resize detected. Active config timestamp: ${heavyConfig.timestamp}`);
        };

        window.addEventListener('resize', handleResize);

        // Return a complete, explicit teardown routine
        return () => {
            console.log(`[Dashboard] Tearing down telemetry channel for symbol: ${symbol}`);
            
            // 1. Unbind global window event listeners
            window.removeEventListener('resize', handleResize);

            // 2. Unbind WebSocket event listeners and close connection
            if (socket) {
                socket.removeEventListener('message', handleWebSocketMessage);
                
                // Verify socket state before triggering termination
                if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
                    socket.close();
                }
            }

            // 3. Nullify mutable references to break all remaining heap pointer chains
            socketRef.current = null;
        };
    }, [symbol, heavyConfig]); // Config remains stable, preventing redundant rebuild cycles

    return (
        <div id="analytics-panel" style={{ padding: '20px', color: '#FFFFFF', backgroundColor: '#050505' }}>
            <h2 style={{ color: '#8B5CF6', fontFamily: 'Outfit, sans-serif' }}>Trading Telemetry: {symbol}</h2>
            <div className="metrics-grid" style={{ marginTop: '20px' }}>
                <p>Telemetry Buffers Active: {streamData.length} entries</p>
                <div style={{ height: '300px', overflowY: 'auto', border: '1px solid #1E293B', marginTop: '10px' }}>
                    {streamData.map((data, idx) => (
                        <div key={idx} style={{ padding: '8px', borderBottom: '1px solid #1E293B', display: 'flex', justifyContent: 'space-between' }}>
                            <span>Price Alert: ${data.price.toFixed(2)}</span>
                            <span style={{ color: '#A0AEC0', fontSize: '0.85em' }}>
                                {new Date(data.timestamp).toLocaleTimeString()}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
