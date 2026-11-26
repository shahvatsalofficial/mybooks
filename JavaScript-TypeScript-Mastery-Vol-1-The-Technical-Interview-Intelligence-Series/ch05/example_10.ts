import { useRef, useEffect, useCallback } from 'react';

export function useLiveCallback<T extends (...args: any[]) => any>(callback: T): T {
    const callbackRef = useRef(callback);

    // Update the ref's current property on every render to point to the newest callback function
    useEffect(() => {
        callbackRef.current = callback;
    });

    // Return a stable, cached wrapper function that delegates to the current callback ref
    return useCallback(((...args) => {
        return callbackRef.current(...args);
    }) as T, []); // Empty dependency array ensures the wrapper never changes
}
