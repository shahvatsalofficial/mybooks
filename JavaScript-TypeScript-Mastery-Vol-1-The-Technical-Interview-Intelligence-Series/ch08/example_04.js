// VulnerableHostShell.js
// Brittle Host Shell with zero fault isolation or timeout safeguards

import React, { Suspense } from 'react';

// Static Module Federation Imports (Vulnerable)
// Webpack expects 'payment_service' and 'chat_service' to be resolved immediately at startup.
// If either script is offline, this file fails to execute entirely, crashing the app.
const PaymentTransactionGrid = React.lazy(() => import('payment_service/TransactionGrid'));
const LiveSupportChat = React.lazy(() => import('chat_service/LiveChat'));

export const VulnerableHostShell = () => {
    return (
        <div style={{ padding: '20px', background: '#050505', color: '#FFF', minHeight: '100vh' }}>
            <header style={{ borderBottom: '2px solid #8B5CF6', paddingBottom: '10px' }}>
                <h1>Enterprise Financial Workspace</h1>
                <p>Status: Synchronous Mode</p>
            </header>

            <main style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginTop: '20px' }}>
                <section className="primary-panel">
                    <h2>Account Overview & Transactions</h2>
                    {/* Vulnerable Load: A single unhandled promise rejection here crashes the entire grid */}
                    <Suspense fallback={<div>Loading transaction logs...</div>}>
                        <PaymentTransactionGrid />
                    </Suspense>
                </section>

                <aside className="sidebar-panel">
                    <h2>Support Terminal</h2>
                    {/* Vulnerable Load: If the Support Chat CDN is down, the entire workspace crashes */}
                    <Suspense fallback={<div>Loading support terminal...</div>}>
                        <LiveSupportChat />
                    </Suspense>
                </aside>
            </main>
        </div>
    );
};
