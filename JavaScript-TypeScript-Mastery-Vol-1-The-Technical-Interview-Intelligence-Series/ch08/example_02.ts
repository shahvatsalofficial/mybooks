// DynamicRemoteLoader.ts
// Runtime dynamic resolution and dependency injection system

declare const __webpack_init_sharing__: (scope: string) => Promise<void>;
declare const __webpack_share_scopes__: { default: any };

export interface RemoteContainer {
    init: (shareScope: any) => Promise<void>;
    get: (module: string) => Promise<() => any>;
}

export const loadDynamicRemote = async (
    remoteUrl: string,
    scopeName: string,
    exposedModule: string
): Promise<any> => {
    return new Promise((resolve, reject) => {
        // 1. Check if the remote entry is already loaded in global scope
        if ((window as any)[scopeName]) {
            return resolve(initializeRemoteContainer(scopeName, exposedModule));
        }

        // 2. Inject script tag dynamically into active DOM
        const script = document.createElement("script");
        script.src = remoteUrl;
        script.type = "text/javascript";
        script.async = true;

        script.onload = () => {
            console.log(`[Federation] Script loaded successfully: ${remoteUrl}`);
            resolve(initializeRemoteContainer(scopeName, exposedModule));
        };

        script.onerror = (err) => {
            console.error(`[Federation] Failed to fetch remote script: ${remoteUrl}`);
            reject(new Error(`Failed to load remote entry: ${remoteUrl}`));
        };

        document.head.appendChild(script);
    });
};

const initializeRemoteContainer = async (
    scopeName: string,
    exposedModule: string
): Promise<any> => {
    // Acknowledge remote container interface in global window scope
    const container: RemoteContainer = (window as any)[scopeName];
    
    if (!container) {
        throw new Error(`Remote container scope "${scopeName}" not found on global window.`);
    }

    // Initialize sharing scopes for runtime dependency resolution
    await __webpack_init_sharing__("default");
    await container.init(__webpack_share_scopes__.default);

    // Fetch the exposed factory and resolve the module
    const factory = await container.get(exposedModule);
    const resolvedModule = factory();
    return resolvedModule;
};
