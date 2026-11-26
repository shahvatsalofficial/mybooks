// ResilientLoader.ts
// Robust dynamic script injector with exponential backoff retries and timeouts

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const loadDynamicRemoteResilient = async (
    remoteUrl: string,
    scopeName: string,
    exposedModule: string,
    maxRetries = 3,
    baseDelay = 1000
): Promise<any> => {
    let attempt = 0;

    const executeInjection = async (): Promise<any> => {
        attempt++;
        console.log(`[Loader] Attempting remote resolution. Src: ${remoteUrl} (Attempt ${attempt}/${maxRetries})`);

        try {
            return await new Promise((resolve, reject) => {
                // If already loaded in window context, resolve immediately
                if ((window as any)[scopeName]) {
                    return resolve(initializeRemoteContainer(scopeName, exposedModule));
                }

                const script = document.createElement("script");
                script.src = remoteUrl;
                script.type = "text/javascript";
                script.async = true;

                // Enforce a strict network execution timeout
                const networkTimeout = setTimeout(() => {
                    script.onerror!(new ErrorEvent("Network timeout exceeded"));
                }, 5000);

                script.onload = () => {
                    clearTimeout(networkTimeout);
                    console.log(`[Loader] Script resolved on attempt ${attempt}`);
                    resolve(initializeRemoteContainer(scopeName, exposedModule));
                };

                script.onerror = (err) => {
                    clearTimeout(networkTimeout);
                    script.remove(); // Clean up failed DOM node
                    reject(err);
                };

                document.head.appendChild(script);
            });
        } catch (error) {
            if (attempt < maxRetries) {
                const backoffDelay = baseDelay * Math.pow(2, attempt - 1);
                console.warn(`[Loader] Failed attempt ${attempt}. Retrying in ${backoffDelay}ms...`);
                await wait(backoffDelay);
                return executeInjection();
            } else {
                console.error(`[Loader] Max retries exhausted. Remote connection terminated.`);
                throw new Error(`Failed to load remote entry: ${remoteUrl} after ${maxRetries} attempts.`);
            }
        }
    };

    return executeInjection();
};
