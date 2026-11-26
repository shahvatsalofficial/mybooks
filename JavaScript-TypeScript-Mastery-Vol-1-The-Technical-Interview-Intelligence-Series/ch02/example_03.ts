// Express application context extension: augmenting 'express' module types
import express from 'express';

declare module 'express' {
    interface Request {
        correlationId: string;
        userPayload?: {
            userId: string;
            accountLevel: 'enterprise' | 'standard';
            permissions: string[];
        };
    }
    
    interface Response {
        sendAuditLog(event: string): void;
    }
}

// Augmenting global window objects inside micro-frontends sandboxes
declare global {
    interface Window {
        __federated_sandbox_router__: {
            dispatchSandboxEvent(event: string, payload: any): void;
        };
    }
}
