// EventBroker.ts
// Decoupled global messaging channel with namespace isolation

export interface EventMessage<P = any> {
    namespace: string;
    payload: P;
}

export class EnterpriseEventBroker {
    private static channelName = "ENTERPRISE_MFE_COMMUNICATION_BUS";

    public static publish<T>(namespace: string, payload: T) {
        const message: EventMessage<T> = { namespace, payload };
        const event = new CustomEvent(this.channelName, { detail: message });
        window.dispatchEvent(event);
    }

    public static subscribe<T>(namespace: string, callback: (payload: T) => void): () => void {
        const handler = (event: Event) => {
            const message = (event as CustomEvent).detail as EventMessage<T>;
            if (message.namespace === namespace) {
                callback(message.payload);
            }
        };

        window.addEventListener(this.channelName, handler);
        
        // Return unsubscription hook for clean cleanup during unmount phases
        return () => window.removeEventListener(this.channelName, handler);
    }
}
