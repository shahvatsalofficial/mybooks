// HardenedMicroFrontendGrid.test.tsx
// High-availability validation suite for fault-tolerant micro-frontend grids

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { HardenedMicroFrontendGrid } from './HardenedMicroFrontendGrid';
import { loadDynamicRemote } from './DynamicRemoteLoader';

// Mock the Dynamic Remote Loader to simulate remote success and failure scenarios
jest.mock('./DynamicRemoteLoader', () => ({
    loadDynamicRemote: jest.fn()
}));

describe("HardenedMicroFrontendGrid Resiliency Audit", () => {
    beforeEach(() => {
        jest.clearAllMocks();
        // Prevent console.error output from polluting the test console during error boundary catches
        jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        (console.error as jest.Mock).mockRestore();
    });

    test("Dashboard must load successfully, displaying payment grid when both remotes resolve normally", async () => {
        // Configure mocks to return valid mock components
        (loadDynamicRemote as jest.Mock).mockImplementation((_, scope) => {
            if (scope === "payment_service") {
                return Promise.resolve({ default: () => <div>MOCK_PAYMENT_LEDGER</div> });
            }
            if (scope === "chat_service") {
                return Promise.resolve({ default: () => <div>MOCK_SUPPORT_CHAT</div> });
            }
            return Promise.reject(new Error("Unknown scope"));
        });

        render(<HardenedMicroFrontendGrid />);

        expect(screen.getByText("ENTERPRISE OPERATIONS CENTRAL")).toBeInTheDocument();

        // Verify both mock remote widgets load successfully
        await waitFor(() => {
            expect(screen.getByText("MOCK_PAYMENT_LEDGER")).toBeInTheDocument();
            expect(screen.getByText("MOCK_SUPPORT_CHAT")).toBeInTheDocument();
        });
    });

    test("Dashboard must isolate failure and display SupportFallbackCard when the Support Chat remote fails to load", async () => {
        // Configure mocks: Payment resolves normally, but Support Chat crashes due to a network timeout
        (loadDynamicRemote as jest.Mock).mockImplementation((_, scope) => {
            if (scope === "payment_service") {
                return Promise.resolve({ default: () => <div>MOCK_PAYMENT_LEDGER</div> });
            }
            if (scope === "chat_service") {
                return Promise.reject(new Error("Network timeout: CDN unreachable"));
            }
            return Promise.reject(new Error("Unknown scope"));
        });

        render(<HardenedMicroFrontendGrid />);

        // Verify critical transaction widget loads successfully
        await waitFor(() => {
            expect(screen.getByText("MOCK_PAYMENT_LEDGER")).toBeInTheDocument();
        });

        // Verify that the Support Chat remote failed gracefully, catching the error
        // and rendering the fallback card instead of crashing the host shell.
        await waitFor(() => {
            expect(screen.getByText("Support Chat Offline")).toBeInTheDocument();
            expect(screen.queryByText("MOCK_SUPPORT_CHAT")).toBeNull();
        });

        // Verify the host shell header remains active and responsive
        expect(screen.getByText("ENTERPRISE OPERATIONS CENTRAL")).toBeInTheDocument();
    });
});
