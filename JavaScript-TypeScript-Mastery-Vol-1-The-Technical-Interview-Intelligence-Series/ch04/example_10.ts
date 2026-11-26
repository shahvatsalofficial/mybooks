import React, { Suspense, lazy } from 'react';

// Lazily import the federated remote component
const RemoteCheckoutComponent = lazy(() => import('checkout_mfe/CheckoutModule'));

class MfeErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
    state = { hasError: false };

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('Remote MFE failed to mount:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return <div className="p-4 border-red-500 bg-red-950 text-white">Service temporarily unavailable.</div>;
        }
        return this.props.children;
    }
}

export const FederatedCheckout: React.FC = () => {
    return (
        <MfeErrorBoundary>
            <Suspense fallback={<div className="animate-spin text-purple-600">Loading modules...</div>}>
                <RemoteCheckoutComponent />
            </Suspense>
        </MfeErrorBoundary>
    );
};
