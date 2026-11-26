// HardenedLiveDashboard.test.tsx
// Diagnostic validation suite for memory-leak safety and subscription teardown

import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { HardenedLiveDashboard } from './HardenedLiveDashboard';

// Mock the global WebSocket object
class MockWebSocket {
    public url: string;
    public readyState: number = 0; // CONNECTING
    public addEventListener = jest.fn();
    public removeEventListener = jest.fn();
    public close = jest.fn();

    constructor(url: string) {
        this.url = url;
        // Automatically shift state to OPEN for testing
        this.readyState = 1; // OPEN
    }
}

global.WebSocket = MockWebSocket as any;

describe("HardenedLiveDashboard Diagnostics & Safety Audit", () => {
    let addEventSpy: jest.SpyInstance;
    let removeEventSpy: jest.SpyInstance;

    beforeEach(() => {
        jest.clearAllMocks();
        // Spy on global event listeners
        addEventSpy = jest.spyOn(window, 'addEventListener');
        removeEventSpy = jest.spyOn(window, 'removeEventListener');
    });

    afterEach(() => {
        addEventSpy.mockRestore();
        removeEventSpy.mockRestore();
    });

    test("Component should register event listeners and WebSocket subscriptions on mount", () => {
        const { unmount } = render(<HardenedLiveDashboard symbol="AAPL" />);

        expect(screen.getByText("Trading Telemetry: AAPL")).toBeInTheDocument();
        
        // Assert that the global resize listener was registered
        expect(addEventSpy).toHaveBeenCalledWith('resize', expect.any(Function));

        unmount();
    });

    test("Component must execute a complete teardown and close all active sockets on unmount", () => {
        let activeSocketInstance: any = null;

        // Spy on the WebSocket constructor to capture the created instance
        const originalWebSocket = global.WebSocket;
        global.WebSocket = jest.fn().mockImplementation((url) => {
            const instance = new MockWebSocket(url);
            activeSocketInstance = instance;
            return instance;
        }) as any;

        const { unmount } = render(<HardenedLiveDashboard symbol="TSLA" />);

        expect(activeSocketInstance).not.toBeNull();
        expect(activeSocketInstance.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));

        // Trigger unmount to initiate the cleanup hook
        unmount();

        // 1. Assert that the global window resize event listener was uninstalled
        expect(removeEventSpy).toHaveBeenCalledWith('resize', expect.any(Function));

        // 2. Assert that the WebSocket message listener was uninstalled
        expect(activeSocketInstance.removeEventListener).toHaveBeenCalledWith('message', expect.any(Function));

        // 3. Assert that the socket was explicitly closed
        expect(activeSocketInstance.close).toHaveBeenCalled();

        // Restore original WebSocket
        global.WebSocket = originalWebSocket;
    });
});
