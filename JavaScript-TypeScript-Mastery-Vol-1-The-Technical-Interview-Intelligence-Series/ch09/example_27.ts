// SafeRemoteWrapper.tsx
// High-resilience remote module loading wrapper with error boundaries and timeouts

import React, { Component, ReactNode, Suspense } from 'react';
import { loadDynamicRemote } from './DynamicRemoteLoader';

interface Props {
    url: string;
    scope: string;
    module: string;
    fallbackUI: ReactNode;
    children: (Component: React.ComponentType<any>) => ReactNode;
}

interface State {
    hasError: boolean;
    LoadedComponent: React.ComponentType<any> | null;
}

export class SafeRemoteWrapper extends Component<Props, State> {
    public state: State = {
        hasError: false,
        LoadedComponent: null
    };

    public static getDerivedStateFromError(_: Error): Partial<State> {
        return { hasError: true };
    }

    public async componentDidMount() {
        try {
            // Force a 5-second dynamic network timeout
            const loaderPromise = loadDynamicRemote(this.props.url, this.props.scope, this.props.module);
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error("Network timeout exceeded")), 5000)
            );

            // Race the loader promise against the network timeout
            const resolvedModule = await Promise.race([loaderPromise, timeoutPromise]) as any;
            
            this.setState({ LoadedComponent: resolvedModule.default });
        } catch (err) {
            console.error(`[Wrapper] Failed to resolve remote container: ${this.props.scope}`, err);
            this.setState({ hasError: true });
        }
    }

    public render() {
        if (this.state.hasError) {
            return this.props.fallbackUI;
        }

        const { LoadedComponent } = this.state;
        if (!LoadedComponent) {
            return <div>Establishing secure dynamic link...</div>;
        }

        return (
            <Suspense fallback={<div>Loading visual components...</div>}>
                {this.props.children(LoadedComponent)}
            </Suspense>
        );
    }
}
