function DashboardComponent() {
    // Hook 1: useState (memoizedState = 0)
    const [clickCount, setClickCount] = useState(0);

    // Hook 2: useRef (memoizedState = { current: null })
    const telemetryContainer = useRef(null);

    // Hook 3: useEffect (memoizedState = { create: ..., deps: ... })
    useEffect(() => {
        setupTelemetry(telemetryContainer.current);
    }, []);

    return <div ref={telemetryContainer}>Click count: {clickCount}</div>;
}
