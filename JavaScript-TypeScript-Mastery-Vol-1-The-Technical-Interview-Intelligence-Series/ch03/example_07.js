// Optimized Implementation: Decoupled State Mapping
function DynamicScopeTimer() {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const timerId = setInterval(() => {
            // Enforce update physics via functional payload, eliminating stale captures
            setCount(prevCount => prevCount + 1);
        }, 1000);

        return () => clearInterval(timerId);
    }, []); 
}
