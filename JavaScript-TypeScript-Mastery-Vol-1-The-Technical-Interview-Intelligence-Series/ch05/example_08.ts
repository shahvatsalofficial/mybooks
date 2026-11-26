useEffect(() => {
    const intervalId = setInterval(() => {
        // Safe: No local 'count' variable is referenced in the closure scope.
        // React provides the current value to the updater callback at runtime.
        setCount(prev => prev + 1);
    }, 1000);

    return () => clearInterval(intervalId);
}, []); // Safe to leave empty
