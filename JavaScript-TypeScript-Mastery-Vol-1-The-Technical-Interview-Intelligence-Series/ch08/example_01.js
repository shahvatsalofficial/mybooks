// Monolithic build-time configuration (Brittle & Rigid)
new ModuleFederationPlugin({
    name: "host_app",
    remotes: {
        payment_service: "payment_service@https://cdn.enterprise.io/payments/v1/remoteEntry.js"
    }
});
