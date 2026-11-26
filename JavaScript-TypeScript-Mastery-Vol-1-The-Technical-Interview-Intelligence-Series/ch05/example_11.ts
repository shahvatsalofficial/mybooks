// Conceptual polyfill representation of the React RFC
export function useEvent<T extends (...args: any[]) => any>(handler: T): T {
    const handlerRef = useRef<T>(handler);

    // Layout effect runs synchronously before the browser paints,
    // guaranteeing that the handler ref is updated before any event can fire.
    useEffect(() => {
        handlerRef.current = handler;
    });

    return useCallback(((...args) => {
        const fn = handlerRef.current;
        return fn(...args);
    }) as T, []);
}
