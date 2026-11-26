// host-app/webpack.config.js
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');

module.exports = {
    output: {
        publicPath: 'auto',
        uniqueName: 'host_shell_app',
    },
    plugins: [
        new ModuleFederationPlugin({
            name: 'host_shell_app',
            remotes: {
                // Dynamically resolve the remote checkout entry point at runtime
                checkout_mfe: 'checkout_mfe@http://localhost:3001/remoteEntry.js',
                analytics_mfe: 'analytics_mfe@http://localhost:3002/remoteEntry.js',
            },
            shared: {
                react: { singleton: true, requiredVersion: '^18.2.0', eager: true },
                'react-dom': { singleton: true, requiredVersion: '^18.2.0', eager: true },
            },
        }),
    ],
};
