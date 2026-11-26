// Vulnerable Implementation: Stale Closure Memory Trap
function StaleScopeTimer() {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const timerId = setInterval(() => {
            // Read path captures initial lexical closure (count = 0)
            console.log(`Executing count check: ${count}`);
            setCount(count + 1); 
        }, 1000);

        return () => clearInterval(timerId);
    }, []); // Dependency array is empty: closure is never updated!
}
